## Core Components 
| Component                | Azure Service               | Purpose                                     |
| ------------------------ | --------------------------- | ------------------------------------------- |
| App container            | Azure Container Apps        | Serve UI and chat backend                   |
| Serverless logic         | Azure Functions             | Document ingestion, orchestration workflows |
| Vector storage + search  | Azure AI Search (or Cosmos) | Semantic retrieval                          |
| LLM inference            | Azure OpenAI or external    | Generate answers based on retrieved chunks  |
| Auth & identity          | Azure AD + Managed Identity | SSO and secure resource access              |
| Secrets management       | Azure Key Vault             | For external LLM configs or endpoints       |
| Deployment orchestration | Azure Developer CLI (azd)   | `azd up` single‑click provisioning          |
| Monitoring & logging     | Application Insights        | Telemetry, tracing, and alerts              |


## Popular Azure RAG Patterns
- Pattern 1: Fully Managed Serverless
                
        API Management → Azure Functions → Azure OpenAI + Cognitive Search
- Pattern 2: Microservices with AKS
                
                Application Gateway → AKS → Multiple RAG services → Azure OpenAI + PostgreSQL
- Pattern 3: Web App with Background Processing
                
                App Service → Service Bus → Functions → Cognitive Search + OpenAI

## References:
1. [Building a serverless RAG application with LlamaIndex and Azure OpenAI](https://www.llamaindex.ai/blog/building-a-serverless-rag-application-with-llamaindex-and-azure-openai?utm_source=chatgpt.com)
2. 

