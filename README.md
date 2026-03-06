# Army Field Manual Copilot (AFMC)

## What it does
FastAPI RAG service over public Army Field Manuals using Bedrock Knowledge Bases (S3 Vectors) + Nova Micro, returning strict JSON with citations; implements cite-or-refuse behavior, token/latency telemetry, and CI eval gates to prevent regressions.

## Output schema
  {
    "answer": "…",
    "citations": [{"doc":"FM_5-0.pdf","location":"s3://…","snippet":"…"}],
    "refusal": false,
    "needs_clarification": []
  }

## Metrics
- Baseline: docs/report_baseline.md
- Updated: docs/report_v2.md
- CI: artifact docs/report_ci.md

## Guardrails / cost controls

The service is designed to be safe-by-default and keep spend predictable.

- **Top-K cap:** client `top_k` is validated and capped server-side (default 3; max 5).
- **Context cap:** retrieved text is truncated to `AFMC_MAX_CONTEXT_TOKENS` (default ~1800) before generation.
- **Output cap:** generation is capped via `AFMC_MAX_OUTPUT_TOKENS` (default ~400).
- **Cite-or-refuse:** if retrieval is empty or the best retrieval score is below `AFMC_MIN_RETRIEVAL_SCORE` (default ~0.45), the API refuses and returns clarifying questions (no hallucinated answers).
- **Rate limiting:** simple per-IP request throttle via `AFMC_RATE_LIMIT_RPM` (disabled in CI).
- **Eval safety:** eval runner has a max-questions limit to prevent accidental spend.
- **Telemetry headers:** response headers include `x-afmc-*` fields for tokens and latency to make cost/latency visible (input/output tokens, retrieval/LLM latency, max_score, top_k).

Environment variables (examples):
- `AFMC_TOP_K_MAX=5`
- `AFMC_MAX_CONTEXT_TOKENS=1800`
- `AFMC_MAX_OUTPUT_TOKENS=400`
- `AFMC_MIN_RETRIEVAL_SCORE=0.45`
- `AFMC_RATE_LIMIT_RPM=30`

## Repo structure
- app/ FastAPI service
- eval/ evaluation scripts + metrics
- scripts/ one-off utilities
- docs/ notes / diagrams

---

## Demo (30 seconds)

Terminal 1 (server + logs):

    cd ~/projects/army-field-manual-copilot
    export AFMC_KB_ID=<YOUR_KB_ID>
    export AWS_REGION=us-east-1
    export AFMC_MODEL_ID=amazon.nova-micro-v1:0
    ./scripts/run_local.sh

Terminal 2 (demo calls):

    cd ~/projects/army-field-manual-copilot
    ./scripts/demo.sh

## Architecture

See docs/architecture.md (includes a Mermaid diagram).

---

## Results

Baseline eval (60 Qs):
- JSON validity: 100%
- Citation rate (non-refusals): 100%
- Refusal correctness: 100%
- Avg latency: ~1.9s (p95 ~2.6s)
- Tokens in/out (60 Qs): ~59k / ~4.1k

CI gate (gold subset, 10 Qs on push to main):
- JSON validity: 100%
- Citation rate (non-refusals): 100%
- Refusal correctness: 100%
- Avg latency: ~1.3s (p95 ~1.6s)

See: docs/report_baseline.md, docs/report_v2.md, and CI artifact docs/report_ci.md.


## Security and cost guardrails

- GitHub Actions uses AWS OIDC (no long-lived AWS keys committed).
- Server-side caps: TOP_K max, context truncation (MAX_CONTEXT_TOKENS), output cap (MAX_OUTPUT_TOKENS).
- Cite-or-refuse policy: if retrieval is empty/low-confidence, the API refuses with clarifying questions instead of hallucinating.
- Eval runner has a max-question limit to prevent surprise spend.

