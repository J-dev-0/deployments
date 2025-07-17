## Architecture Overview 

    User → CloudFront → API Gateway → Lambda Functions → External LLM 

                                            ↓ 

                                   OpenSearch/RDS Vector DB 

                                            ↓ 

                                    S3 Document Storage 

