## Core Components 

### Authentication & Authorization 
- AWS IAM Identity Center (SSO) - Central identity management 
- Amazon Cognito User Pools - Application user management 
- API Gateway Authorizers - JWT token validation 
- AWS Lambda Authorizer - Custom auth logic if needed 

### Serverless Compute 
- AWS Lambda - RAG processing, embeddings, search 
- Lambda Layers - Shared libraries (transformers, vector libs) 
- Lambda@Edge - Edge computing for low latency 

### API & Frontend 
- Amazon API Gateway - RESTful APIs with throttling 
- Amazon CloudFront - CDN for static assets 
- AWS Amplify - Frontend hosting (React/Vue.js) 

### Storage & Vector Database 
- Amazon S3 - Document storage with versioning 
- Amazon OpenSearch Serverless - Vector search 
- Amazon RDS Proxy - Connection pooling for RDS 

### External LLM Integration 
- VPC Endpoints - Secure external API calls 
- AWS Secrets Manager - API keys for external LLMs 
- Amazon EventBridge - Event-driven LLM calls 

## Popular Patterns
- Pattern 1: Fully Managed
        
        API Gateway → Lambda → Bedrock + OpenSearch Service
- Pattern 2: Scalable Microservices

        ALB → ECS/Fargate → Multiple RAG services → Bedrock + RDS/pgvector
- Pattern 3: Real-time Processing


        Kinesis → Lambda → OpenSearch → API Gateway

The choice depends on your scale, latency requirements, and team expertise. For most applications, the serverless approach with Lambda, Bedrock, and OpenSearch Service provides a good balance of simplicity and scalability.