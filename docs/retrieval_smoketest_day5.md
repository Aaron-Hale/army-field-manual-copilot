# Retrieval Smoke Test (Day 5) — AFMC

KB: afmc-kb-v1 (<YOUR_KB_ID>)
Data source: afmc-kb-v1-raw (X4KWWQFXN5)
TOP_K tested: 3
Embedding: Titan Text Embeddings v2 (float, 512)

Scoring: Relevance (0–2), Citation usability (0–2)

## Results (8 questions)
1) Operational environment definition — R: 2/2, C: 1.5/2
2) Elements of operational art — R: 2/2, C: 2/2
3) Operations process + why — R: 2/2, C: 2/2
4) Tempo definition + why — R: 2/2, C: 2/2
5) Unified land operations — R: 1/2, C: 2/2
6) Purpose of planning — R: 2/2, C: 2/2
7) MDMP steps — R: 2/2, C: 2/2
8) OPORD components — R: 2/2, C: 1/2

## Notes / follow-ups
- “Unified land operations” definition not consistently surfaced in top 3 → try query rewrite + TOP_K=5 and/or hybrid search.
- “OPORD components” returned template fragments but not the clean five-paragraph breakdown → try query rewrite (“five-paragraph format”) and/or TOP_K=5.
