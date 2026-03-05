# Eval Baseline Report
- Input: `eval/evalset_v1.jsonl`
- Output: `eval/outputs/outputs_evalset_v1_20260305_110607.jsonl`
- URL: `http://127.0.0.1:8000/answer`
- Total questions: **60** (answerable=40, unanswerable=20)

## Metrics
- HTTP 200 rate: **100.0%**
- JSON validity rate: **100.0%**
- Refusal correctness: **98.3%**
- Citation rate (non-refusals): **100.0%** (non-refusals=39)
- Avg latency: **1867.7 ms**
- P95 latency: **2649.1 ms**
- Total tokens in/out: **57539 / 4001**

## Failures (first 10)
- v1-007: expected_answerable=True status=200 refusal=True preview="Unified land operations is not explicitly defined in the provided excerpts.…"
