#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

pretty_json() {
  python -m json.tool
}

call_answer() {
  local question="$1"
  local top_k="${2:-3}"

  echo
  echo "============================================================"
  echo "Q: $question"
  echo "============================================================"

  curl -sS -D /tmp/afmc_headers.txt \
    -H "Content-Type: application/json" \
    -d "{\"question\":\"${question}\",\"top_k\":${top_k}}" \
    "${BASE_URL}/answer" \
    | pretty_json

  echo
  echo "--- Response headers (AFMC) ---"
  grep -i "^x-afmc-" /tmp/afmc_headers.txt || echo "(no x-afmc-* headers found)"
}

echo "Base URL: ${BASE_URL}"

echo
echo "1) Answerable (should cite)"
call_answer "What are the seven steps of MDMP?" 3

echo
echo "2) Unanswerable (should refuse)"
call_answer "What is the capital of France?" 3
