import json
import logging
import os
import time
from collections import defaultdict, deque
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response

from app.config import (
    TOP_K_MAX,
    MAX_CONTEXT_TOKENS,
    MIN_RETRIEVAL_SCORE,
    REQUIRE_CITATIONS,
    RATE_LIMIT_RPM,
)
from app.schemas.answer import AnswerRequest, AnswerResponse, Citation
from app.services.kb_retrieve import retrieve_top_k
from app.services.llm_converse import converse_json

router = APIRouter()
logger = logging.getLogger("afmc")

# ---------------- Rate limiting (simple, in-process) ----------------
_REQ_LOG: dict[str, deque[float]] = defaultdict(deque)

def _enforce_rate_limit(client_key: str) -> None:
    """Allow RATE_LIMIT_RPM requests per 60s per client_key. 0 disables."""
    if RATE_LIMIT_RPM <= 0:
        return
    now = time.time()
    q = _REQ_LOG[client_key]
    while q and (now - q[0]) > 60.0:
        q.popleft()
    if len(q) >= RATE_LIMIT_RPM:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again shortly.")
    q.append(now)

# ---------------- Helpers ----------------
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

def _approx_tokens(text: str) -> int:
    # Rough estimate: ~4 chars/token
    if not text:
        return 0
    return max(1, len(text) // 4)

def _truncate_to_token_budget(text: str, token_budget: int) -> str:
    if token_budget <= 0 or not text:
        return ""
    max_chars = token_budget * 4
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    last_nl = cut.rfind("\n")
    last_sp = cut.rfind(" ")
    pivot = max(last_nl, last_sp)
    if pivot > int(max_chars * 0.7):
        cut = cut[:pivot]
    return cut.rstrip() + "…"

def _refusal(needs: list[str]) -> AnswerResponse:
    return AnswerResponse(
        answer="I don’t have enough evidence in the provided manuals to answer that reliably.",
        citations=[],
        refusal=True,
        needs_clarification=needs,
    )

@router.post("/answer", response_model=AnswerResponse)
def answer(req: AnswerRequest, request: Request, response: Response) -> AnswerResponse:
    # Rate limit (per client IP)
    client_ip = (request.client.host if request.client else None) or "unknown"
    _enforce_rate_limit(client_ip)

    # Hard cap TOP_K
    top_k = min(int(req.top_k), TOP_K_MAX)

    t0 = time.perf_counter()
    try:
        retrieval_results = retrieve_top_k(question=req.question, top_k=top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieve failed: {e}")
    t_retrieve = time.perf_counter()

    # Keep only results with real text
    evidence: list[dict[str, Any]] = []
    for r in retrieval_results or []:
        text = ((r.get("content") or {}).get("text") or "").strip()
        if not text:
            continue
        score = r.get("score")
        score_f = float(score) if isinstance(score, (int, float)) else None
        evidence.append({"raw": r, "text": text, "score": score_f, "citation": _as_citation(r)})

    # Refusal BEFORE LLM (saves cost + blocks hallucination)
    if not evidence:
        response.headers["x-afmc-input-tokens"] = "0"
        response.headers["x-afmc-output-tokens"] = "0"
        response.headers["x-afmc-top-k"] = str(top_k)
        response.headers["x-afmc-latency-ms-retrieve"] = str(int((t_retrieve - t0) * 1000))
        response.headers["x-afmc-latency-ms-llm"] = "0"
        return _refusal(
            [
                "Which field manual should I use (e.g., FM 3-0 vs FM 5-0)?",
                "What specific term/section should I look up?",
                "Can you rephrase using doctrinal terms (e.g., MDMP, OPORD, COA)?",
            ]
        )

    # Low-score refusal (only if scores exist—score can be missing)
    scores = [e["score"] for e in evidence if e["score"] is not None]
    max_score = max(scores) if scores else None
    if max_score is not None and max_score < MIN_RETRIEVAL_SCORE:
        response.headers["x-afmc-input-tokens"] = "0"
        response.headers["x-afmc-output-tokens"] = "0"
        response.headers["x-afmc-top-k"] = str(top_k)
        response.headers["x-afmc-max-score"] = str(max_score)
        response.headers["x-afmc-latency-ms-retrieve"] = str(int((t_retrieve - t0) * 1000))
        response.headers["x-afmc-latency-ms-llm"] = "0"
        return _refusal(
            [
                "Add 1–2 keywords that would appear verbatim in the manual text.",
                "Is this about planning (FM 5-0) or operations (FM 3-0)?",
                "Do you want a definition, steps/process, or an example?",
            ]
        )

    # Build capped context from chunk text (not just 280-char snippets)
    remaining = MAX_CONTEXT_TOKENS
    context_blocks: list[str] = []
    citations_all: list[Citation] = [e["citation"] for e in evidence]

    for i, e in enumerate(evidence, start=1):
        c: Citation = e["citation"]
        score_str = f"{e['score']:.3f}" if isinstance(e["score"], float) else "n/a"
        header = f"[{i}] score={score_str}\ndoc={c.doc}\nlocation={c.location}\n"
        header_tok = _approx_tokens(header)
        if header_tok >= remaining:
            break
        remaining -= header_tok

        chunk = _truncate_to_token_budget(e["text"], remaining)
        chunk_tok = _approx_tokens(chunk)
        remaining = max(0, remaining - chunk_tok)

        context_blocks.append(header + chunk)
        if remaining <= 0:
            break

    context_text = "\n\n".join(context_blocks)

    system = (
        "You are AFMC, a retrieval-grounded assistant. "
        "Use ONLY the provided excerpts. "
        "If insufficient, set refusal=true and ask clarifying questions. "
        "Return JSON ONLY (no markdown, no extra text)."
    )

    user = (
        "Return JSON with keys: answer, citation_ids, refusal, needs_clarification.\n"
        "citation_ids must be numbers referencing excerpt ids like [1], [2].\n\n"
        f"QUESTION:\n{req.question}\n\n"
        f"EXCERPTS (top_k={top_k}, context_cap_tokens≈{MAX_CONTEXT_TOKENS}):\n{context_text}\n"
    )

    try:
        llm_text, llm_raw = converse_json(system_text=system, user_text=user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM failed: {e}")
    t_llm = time.perf_counter()

    # Parse JSON robustly
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
            idx = int(x)
        except Exception:
            continue
        if 1 <= idx <= len(citations_all):
            picked.append(citations_all[idx - 1])

    # Hallucination control: if not refusing, require citations (default)
    if not refusal and REQUIRE_CITATIONS and len(picked) == 0:
        response.headers["x-afmc-input-tokens"] = "0"
        response.headers["x-afmc-output-tokens"] = "0"
        response.headers["x-afmc-top-k"] = str(top_k)
        response.headers["x-afmc-max-score"] = str(max_score) if max_score is not None else ""
        response.headers["x-afmc-latency-ms-retrieve"] = str(int((t_retrieve - t0) * 1000))
        response.headers["x-afmc-latency-ms-llm"] = str(int((t_llm - t_retrieve) * 1000))
        return _refusal(
            [
                "I couldn’t map the answer to a specific excerpt. Can you narrow the question?",
                "Try asking for a definition, steps, or a named doctrine term (e.g., MDMP, OPORD).",
            ]
        )

    usage = (llm_raw.get("usage") or {}) if isinstance(llm_raw, dict) else {}
    in_tok = usage.get("inputTokens")
    out_tok = usage.get("outputTokens")

    # Response headers for eval runner (keeps JSON body strict)
    response.headers["x-afmc-top-k"] = str(top_k)
    if max_score is not None:
        response.headers["x-afmc-max-score"] = str(max_score)
    if in_tok is not None:
        response.headers["x-afmc-input-tokens"] = str(in_tok)
    if out_tok is not None:
        response.headers["x-afmc-output-tokens"] = str(out_tok)
    response.headers["x-afmc-latency-ms-retrieve"] = str(int((t_retrieve - t0) * 1000))
    response.headers["x-afmc-latency-ms-llm"] = str(int((t_llm - t_retrieve) * 1000))

    logger.info(
        json.dumps(
            {
                "event": "answer",
                "client_ip": client_ip,
                "top_k": top_k,
                "model_id": os.getenv("AFMC_MODEL_ID"),
                "retrieval_results": len(retrieval_results or []),
                "evidence_chunks": len(evidence),
                "max_score": max_score,
                "context_cap_tokens_est": MAX_CONTEXT_TOKENS,
                "latency_ms_retrieve": int((t_retrieve - t0) * 1000),
                "latency_ms_llm": int((t_llm - t_retrieve) * 1000),
                "input_tokens": in_tok,
                "output_tokens": out_tok,
            }
        )
    )

    return AnswerResponse(
        answer=answer_txt,
        citations=picked,
        refusal=refusal,
        needs_clarification=[str(s) for s in needs],
    )
