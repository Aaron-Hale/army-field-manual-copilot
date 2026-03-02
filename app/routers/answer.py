import json
import logging
import os
import time
from fastapi import APIRouter, HTTPException

from app.schemas.answer import AnswerRequest, AnswerResponse, Citation
from app.services.kb_retrieve import retrieve_top_k
from app.services.llm_converse import converse_json

router = APIRouter()
logger = logging.getLogger("afmc")

def _as_citation(r: dict) -> Citation:
    loc = r.get("location", {}) or {}
    loc_type = loc.get("type", "") or ""
    uri = (
        (loc.get("s3Location") or {}).get("uri")
        or (loc.get("webLocation") or {}).get("url")
        or (loc.get("kendraDocumentLocation") or {}).get("uri")
        or ""
    )

    md = r.get("metadata", {}) or {}
    doc = (
        md.get("document_title")
        or md.get("source")
        or md.get("x-amz-bedrock-kb-source-uri")
        or (uri.split("/")[-1] if uri else loc_type or "unknown")
    )

    text = (r.get("content", {}) or {}).get("text", "") or ""
    snippet = text.strip().replace("\n", " ")
    if len(snippet) > 280:
        snippet = snippet[:280] + "…"

    return Citation(doc=str(doc), location=str(uri or loc_type), snippet=snippet)

@router.post("/answer", response_model=AnswerResponse)
def answer(req: AnswerRequest) -> AnswerResponse:
    top_k = min(int(req.top_k), 5)

    t0 = time.perf_counter()
    try:
        retrieval_results = retrieve_top_k(question=req.question, top_k=top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieve failed: {e}")
    t_retrieve = time.perf_counter()

    citations_all = [_as_citation(r) for r in retrieval_results]
    context_text = "\n\n".join(
        f"[{i}] doc={c.doc}\nlocation={c.location}\nsnippet={c.snippet}"
        for i, c in enumerate(citations_all, start=1)
    )

    system = (
        "You are AFMC, a retrieval-grounded assistant. "
        "Use ONLY the provided excerpts. "
        "If insufficient, set refusal=true. "
        "Return JSON ONLY (no markdown, no extra text)."
    )

    user = (
        "Return JSON with keys: answer, citation_ids, refusal, needs_clarification.\n"
        "citation_ids must be numbers referencing excerpt ids like [1], [2].\n\n"
        f"QUESTION:\n{req.question}\n\n"
        f"EXCERPTS (top_k={top_k}):\n{context_text}\n"
    )

    try:
        llm_text, llm_raw = converse_json(system_text=system, user_text=user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM failed: {e}")
    t_llm = time.perf_counter()

    try:
        obj = json.loads(llm_text)
    except Exception:
        start = llm_text.find("{")
        end = llm_text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise HTTPException(status_code=500, detail="Model did not return valid JSON.")
        obj = json.loads(llm_text[start : end + 1])

    answer_txt = str(obj.get("answer", "")).strip()
    refusal = bool(obj.get("refusal", False))
    needs = obj.get("needs_clarification") or []
    if not isinstance(needs, list):
        needs = [str(needs)]

    ids = obj.get("citation_ids") or []
    if not isinstance(ids, list):
        ids = []

    picked: list[Citation] = []
    for x in ids:
        try:
            i = int(x)
        except Exception:
            continue
        if 1 <= i <= len(citations_all):
            picked.append(citations_all[i - 1])

    usage = (llm_raw.get("usage") or {}) if isinstance(llm_raw, dict) else {}
    logger.info(
        json.dumps(
            {
                "event": "answer",
                "top_k": top_k,
                "model_id": os.getenv("AFMC_MODEL_ID"),
                "latency_ms_retrieve": int((t_retrieve - t0) * 1000),
                "latency_ms_llm": int((t_llm - t_retrieve) * 1000),
                "input_tokens": usage.get("inputTokens"),
                "output_tokens": usage.get("outputTokens"),
            }
        )
    )

    return AnswerResponse(
        answer=answer_txt,
        citations=picked,
        refusal=refusal,
        needs_clarification=[str(s) for s in needs],
    )
