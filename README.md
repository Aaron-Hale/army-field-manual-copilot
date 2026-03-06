# Doctrine (Spec v0)

## What it does
FastAPI RAG service over public Army Field Manuals using Bedrock KB (S3 Vectors) + Nova Micro. Returns strict JSON with citations; refuses when evidence is missing.

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

## Guardrails / caps
- TBD

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

