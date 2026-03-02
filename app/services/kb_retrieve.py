import os
from typing import Any
import boto3


def _get_region() -> str:
    return os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"


def retrieve_top_k(*, question: str, top_k: int) -> list[dict[str, Any]]:
    kb_id = os.getenv("AFMC_KB_ID")
    if not kb_id:
        raise RuntimeError("Missing env var AFMC_KB_ID (Bedrock Knowledge Base ID).")

    client = boto3.client("bedrock-agent-runtime", region_name=_get_region())

    # NOTE: use retrievalQuery={"text": ...} (keep it simple; avoids param validation pitfalls)
    resp = client.retrieve(
        knowledgeBaseId=kb_id,
        retrievalQuery={"text": question},
        retrievalConfiguration={
            "vectorSearchConfiguration": {"numberOfResults": int(top_k)}
        },
    )

    return resp.get("retrievalResults", [])
