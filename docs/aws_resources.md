# AWS resources (AFMC)

- S3 bucket: army-field-manual-copilot-852136298942-2602281207
- Prefix (raw manuals): afmc/raw/

## Bedrock Knowledge Base (AFMC)
- KB name: afmc-kb-v1
- KB id: 48Q5IV9XZ1
- Data source name: afmc-kb-v1-raw
- Data source id: X4KWWQFXN5
- Raw manuals S3: s3://army-field-manual-copilot-852136298942-2602281207/afmc/raw/
- Vector store: Amazon S3 Vectors
- Vector bucket: bedrock-knowledge-base-s5scig
- Vector index: bedrock-knowledge-base-default-index
- Vector index ARN: arn:aws:s3vectors:us-east-1:852136298942:bucket/bedrock-knowledge-base-s5scig/index/bedrock-knowledge-base-default-index
- Embeddings: Titan Text Embeddings v2 (float, 512 dims)
