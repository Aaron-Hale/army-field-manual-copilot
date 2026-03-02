import os
import boto3
from typing import Any

def _get_region() -> str:
    return os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"

def converse_json(*, system_text: str, user_text: str) -> tuple[str, dict[str, Any]]:
    model_id = os.getenv("AFMC_MODEL_ID", "amazon.nova-micro-v1:0")
    max_tokens = int(os.getenv("AFMC_MAX_OUTPUT_TOKENS", "400"))
    temperature = float(os.getenv("AFMC_TEMPERATURE", "0.2"))
    top_p = float(os.getenv("AFMC_TOP_P", "0.9"))

    session = boto3.Session(profile_name=os.getenv("AWS_PROFILE"), region_name=_get_region())
    client = session.client("bedrock-runtime")

    resp = client.converse(
        modelId=model_id,
        system=[{"text": system_text}],
        messages=[{"role": "user", "content": [{"text": user_text}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": temperature, "topP": top_p},
    )

    blocks = resp["output"]["message"]["content"]
    text = "".join(b.get("text", "") for b in blocks if isinstance(b, dict))
    return text, resp
