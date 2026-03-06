# Setup: Amazon Bedrock Knowledge Base

This project expects an existing Amazon Bedrock Knowledge Base over a public corpus of Army Field Manuals.

## Prerequisites
- AWS account with Bedrock enabled
- Access to Amazon Nova Micro
- An S3 bucket containing the public source PDFs
- Permission to create and query a Bedrock Knowledge Base

## Create the knowledge base
1. Upload the source PDFs to S3.
2. In Amazon Bedrock, create a **Knowledge Base**.
3. Choose the S3 data source that points at the manuals bucket/prefix.
4. Use the default Bedrock-managed vector store / S3 Vectors setup for this demo.
5. Run ingestion/sync so the documents are indexed.
6. Copy the Knowledge Base ID.

## Environment variables
Export these before running locally:

```bash
export AFMC_KB_ID="YOUR_REAL_KB_ID"
export AWS_REGION="us-east-1"
export AFMC_MODEL_ID="amazon.nova-micro-v1:0"
export AFMC_TOP_K_MAX="5"
export AFMC_MAX_CONTEXT_TOKENS="1800"
export AFMC_MAX_OUTPUT_TOKENS="400"
export AFMC_MIN_RETRIEVAL_SCORE="0.45"
export AFMC_RATE_LIMIT_RPM="30"
```

## Local run

```bash
./scripts/run_local.sh
```

## Notes
- This repo demonstrates a **RAG application layer** on top of Bedrock Knowledge Bases.
- It does **not** implement a custom embedding pipeline, custom chunker, or custom reranker.
