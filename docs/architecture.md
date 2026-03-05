# Architecture

This project is a retrieval-grounded Q&A service over Army doctrine manuals using:
- Amazon Bedrock Knowledge Bases (S3 Vectors)
- Bedrock model inference (Nova Micro/Lite)
- Local FastAPI API (`POST /answer`) returning strict JSON + citations
- Evaluation harness + CI regression gate (GitHub Actions)

## High-level flow

~~~mermaid
flowchart LR
  U[User / Client] -->|POST /answer| API[FastAPI Service]

  API -->|Retrieve top_k| KB[Bedrock Knowledge Base]
  KB -->|Vector search| VEC[S3 Vectors]
  KB -->|Source chunks| S3[(S3: manuals / raw PDFs)]

  API -->|Grounded prompt + excerpts| LLM[Bedrock InvokeModel (Nova Micro/Lite)]
  LLM -->|JSON: answer + citation_ids| API
  API -->|JSON: answer + citations + refusal| U

  subgraph Guardrails
    G1[TOP_K cap]
    G2[MAX_CONTEXT_TOKENS]
    G3[MAX_OUTPUT_TOKENS]
    G4[Cite-or-refuse]
    G5[Rate limit]
  end

  API --- Guardrails

  subgraph CI
    GH[GitHub Actions] -->|OIDC assume role| IAM[IAM Role (OIDC)]
    GH -->|Run gold eval| API
    GH -->|Upload artifact| ART[docs/report_ci.md]
  end
~~~

## Notes
- Cite-or-refuse: if evidence is missing/weak, the API refuses with clarifying questions.
- Cost guardrails: top_k cap, context truncation, output token cap, eval limits.
- CI: unit tests on PRs; AWS-backed gold eval gate on pushes to main.
