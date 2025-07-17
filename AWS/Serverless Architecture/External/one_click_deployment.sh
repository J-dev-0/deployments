#!/bin/bash

# RAG Application One-Click Deployment Script
# This script deploys a complete serverless RAG application on AWS

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="rag-application"
REGION="us-east-1"
ENVIRONMENT="dev"
EXTERNAL_LLM_ENDPOINT="https://api.openai.com/v1"
SSO_DOMAIN="your-company.com"
ALLOWED_ORIGINS="https://localhost:3000,https://your-domain.com"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if SAM CLI is installed
    if ! command -v sam &> /dev/null; then
        print_error "SAM CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials are not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    print_success "All prerequisites are met!"
}

# Function to prompt for configuration
prompt_configuration() {
    print_status "Configuring deployment parameters..."
    
    read -p "Enter stack name (default: $STACK_NAME): " input_stack_name
    STACK_NAME=${input_stack_name:-$STACK_NAME}
    
    read -p "Enter AWS region (default: $REGION): " input_region
    REGION=${input_region:-$REGION}
    
    read -p "Enter environment (dev/staging/prod, default: $ENVIRONMENT): " input_environment
    ENVIRONMENT=${input_environment:-$ENVIRONMENT}
    
    read -p "Enter external LLM API endpoint (default: $EXTERNAL_LLM_ENDPOINT): " input_llm_endpoint
    EXTERNAL_LLM_ENDPOINT=${input_llm_endpoint:-$EXTERNAL_LLM_ENDPOINT}
    
    read -p "Enter SSO domain (default: $SSO_DOMAIN): " input_sso_domain
    SSO_DOMAIN=${input_sso_domain:-$SSO_DOMAIN}
    
    read -p "Enter allowed CORS origins (default: $ALLOWED_ORIGINS): " input_origins
    ALLOWED_ORIGINS=${input_origins:-$ALLOWED_ORIGINS}
    
    print_success "Configuration complete!"
}

# Function to create project structure
create_project_structure() {
    print_status "Creating project structure..."
    
    # Create directory structure
    mkdir -p src/document_processor
    mkdir -p src/query_processor
    mkdir -p src/embedding_generator
    mkdir -p src/document_upload
    mkdir -p frontend/src
    mkdir -p infrastructure
    
    # Create requirements.txt for Lambda functions
    cat > requirements.txt << 'EOF'
boto3==1.26.137
opensearch-py==2.2.0
requests==2.31.0
aws-requests-auth==0.4.3
python-multipart==0.0.6
PyPDF2==3.0.1
python-docx==0.8.11
beautifulsoup4==4.12.2
numpy==1.24.3
scikit-learn==1.2.2
EOF
    
    # Copy requirements to each Lambda function directory
    cp requirements.txt src/document_processor/
    cp requirements.txt src/query_processor/
    cp requirements.txt src/embedding_generator/
    cp requirements.txt src/document_upload/
    
    print_success "Project structure created!"
}

# Function to create Lambda function code
create_lambda_functions() {
    print_status "Creating Lambda function code..."
    
    # Document processor function
    cat > src/document_processor/app.py << 'EOF'
import json
import boto3
import os
from typing import Dict, Any
import logging
from urllib.parse import unquote_plus

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    """Process uploaded documents and trigger embedding generation"""
    try:
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = unquote_plus(record['s3']['object']['key'])
            
            logger.info(f"Processing document: {key}")
            
            # Get document content
            response = s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()
            
            # Extract text based on file type
            if key.endswith('.txt'):
                text = content.decode('utf-8')
            elif key.endswith('.pdf'):
                # Add PDF processing logic here
                text = "PDF content extraction not implemented"
            else:
                text = content.decode('utf-8', errors='ignore')
            
            # Trigger embedding generation
            embedding_function = os.environ.get('EMBEDDING_FUNCTION_NAME')
            if embedding_function:
                lambda_client.invoke(
                    FunctionName=embedding_function,
                    InvocationType='Event',
                    Payload=json.dumps({
                        'document_key': key,
                        'content': text,
                        'bucket': bucket
                    })
                )
            
            logger.info(f"Document processed: {key}")
            
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise
    
    return {'statusCode': 200}
EOF
    
    # Document upload function
    cat > src/document_upload/app.py << 'EOF'
import json
import boto3
import base64
import os
from typing import Dict, Any
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """Handle document uploads via API Gateway"""
    try:
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        filename = body.get('filename')
        file_content = body.get('content')
        
        if not filename or not file_content:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'filename and content are required'})
            }
        
        # Decode base64 content