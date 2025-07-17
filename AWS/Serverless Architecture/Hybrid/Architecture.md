## Architecture Overview with Hybrid LLM Support

    User → CloudFront → API Gateway → Lambda Functions → LLM Router
                                        ↓                    ↓
                                OpenSearch/RDS         On-Prem LLM (VPN/Direct Connect)
                                        ↓                    ↓
                                S3 Document Storage    External LLM (Internet)