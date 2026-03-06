# AWS resources (AFMC)

- S3 bucket: <YOUR_BUCKET_NAME>
- Prefix (raw manuals): afmc/raw/

## Bedrock Knowledge Base (AFMC)
- KB name: afmc-kb-v1
- KB id: <YOUR_KB_ID>
- Data source name: afmc-kb-v1-raw
- Data source id: <YOUR_DATA_SOURCE_ID>
- Raw manuals S3: s3://<YOUR_BUCKET_NAME>/afmc/raw/
- Vector store: Amazon S3 Vectors
- Vector bucket: <YOUR_VECTOR_BUCKET>
- Vector index: bedrock-knowledge-base-default-index
- Vector index ARN: arn:aws:s3vectors:<YOUR_REGION>:<YOUR_AWS_ACCOUNT_ID>:bucket/<YOUR_VECTOR_BUCKET>/index/bedrock-knowledge-base-default-index
- Embeddings: Titan Text Embeddings v2 (float, 512 dims)
