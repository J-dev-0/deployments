import json
import boto3
import os
import requests
from typing import Dict, List, Any
import logging
from opensearchpy import OpenSearch, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager')
cloudwatch = boto3.client('cloudwatch')

# Environment variables
OPENSEARCH_ENDPOINT = os.environ['OPENSEARCH_ENDPOINT']
LLM_API_KEY_SECRET = os.environ['LLM_API_KEY_SECRET']
EXTERNAL_LLM_ENDPOINT = os.environ['EXTERNAL_LLM_ENDPOINT']

# Initialize OpenSearch client
host = OPENSEARCH_ENDPOINT.replace('https://', '')
region = os.environ['AWS_REGION']
service = 'aoss'
credentials = boto3.Session().get_credentials()
awsauth = AWSRequestsAuth(credentials, region, service)

opensearch_client = OpenSearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

def get_secret(secret_name: str) -> Dict[str, Any]:
    """Retrieve secret from AWS Secrets Manager"""
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        logger.error(f"Error retrieving secret: {str(e)}")
        raise

def generate_embedding(text: str) -> List[float]:
    """Generate embedding using external LLM API"""
    try:
        secret = get_secret(LLM_API_KEY_SECRET)
        api_key = secret['api_key']
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Example for OpenAI API - adjust based on your LLM provider
        payload = {
            'input': text,
            'model': 'text-embedding-ada-002'
        }
        
        response = requests.post(
            f"{EXTERNAL_LLM_ENDPOINT}/embeddings",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()['data'][0]['embedding']
        else:
            logger.error(f"Embedding API error: {response.status_code} - {response.text}")
            raise Exception(f"Embedding generation failed: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise

def search_similar_documents(query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    """Search for similar documents in OpenSearch"""
    try:
        search_body = {
            "size": top_k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": top_k
                    }
                }
            },
            "_source": ["content", "metadata", "title"]
        }
        
        response = opensearch_client.search(
            index=os.environ['VECTOR_INDEX_NAME'],
            body=search_body
        )
        
        return [hit['_source'] for hit in response['hits']['hits']]
        
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise

def generate_rag_response(query: str, context_documents: List[Dict[str, Any]]) -> str:
    """Generate response using external LLM with retrieved context"""
    try:
        secret = get_secret(LLM_API_KEY_SECRET)
        api_key = secret['api_key']
        
        # Prepare context from retrieved documents
        context = "\n\n".join([
            f"Document: {doc.get('title', 'Unknown')}\n{doc.get('content', '')}"
            for doc in context_documents
        ])
        
        # Create prompt with context
        prompt = f"""Based on the following context, answer the user's question. If the answer cannot be found in the context, say so clearly.

Context:
{context}

Question: {query}

Answer:"""
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Example for OpenAI API - adjust based on your LLM provider
        payload = {
            'model': 'gpt-4',
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a helpful assistant that answers questions based on provided context.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': 500,
            'temperature': 0.7
        }
        
        response = requests.post(
            f"{EXTERNAL_LLM_ENDPOINT}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            logger.error(f"LLM API error: {response.status_code} - {response.text}")
            raise Exception(f"LLM response generation failed: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error generating LLM response: {str(e)}")
        raise

def publish_metrics(metric_name: str, value: float, unit: str = 'Count'):
    """Publish custom metrics to CloudWatch"""
    try:
        cloudwatch.put_metric_data(
            Namespace='RAG/Application',
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit,
                    'Dimensions': [
                        {
                            'Name': 'Environment',
                            'Value': os.environ.get('ENVIRONMENT', 'dev')
                        }
                    ]
                }
            ]
        )
    except Exception as e:
        logger.error(f"Error publishing metrics: {str(e)}")

def lambda_handler(event, context):
    """Main Lambda handler for RAG queries"""
    start_time = context.get_remaining_time_in_millis()
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        query = body.get('query', '').strip()
        if not query:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Query is required'})
            }
        
        logger.info(f"Processing query: {query}")
        
        # Generate embedding for the query
        query_embedding = generate_embedding(query)
        
        # Search for similar documents
        similar_docs = search_similar_documents(query_embedding)
        
        if not similar_docs:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'answer': 'I could not find relevant information to answer your question.',
                    'sources': []
                })
            }
        
        # Generate RAG response
        answer = generate_rag_response(query, similar_docs)
        
        # Prepare response
        response_data = {
            'answer': answer,
            'sources': [
                {
                    'title': doc.get('title', 'Unknown'),
                    'content_preview': doc.get('content', '')[:200] + '...' if len(doc.get('content', '')) > 200 else doc.get('content', ''),
                    'metadata': doc.get('metadata', {})
                }
                for doc in similar_docs
            ],
            'query': query
        }
        
        # Publish metrics
        processing_time = (start_time - context.get_remaining_time_in_millis()) / 1000
        publish_metrics('QueryProcessingTime', processing_time, 'Seconds')
        publish_metrics('DocumentsRetrieved', len(similar_docs), 'Count')
        publish_metrics('QueriesProcessed', 1, 'Count')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        
        # Publish error metrics
        publish_metrics('QueryErrors', 1, 'Count')
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e) if os.environ.get('ENVIRONMENT') == 'dev' else 'An error occurred processing your request'
            })
        }