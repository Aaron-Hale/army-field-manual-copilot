#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${AFMC_KB_ID:?Missing AFMC_KB_ID (export it before running)}"

export AWS_REGION="${AWS_REGION:-us-east-1}"
export AFMC_TOP_K_MAX="${AFMC_TOP_K_MAX:-5}"
export AFMC_MAX_OUTPUT_TOKENS="${AFMC_MAX_OUTPUT_TOKENS:-400}"
export AFMC_MAX_CONTEXT_TOKENS="${AFMC_MAX_CONTEXT_TOKENS:-1800}"
export AFMC_MIN_RETRIEVAL_SCORE="${AFMC_MIN_RETRIEVAL_SCORE:-0.45}"
export AFMC_RATE_LIMIT_RPM="${AFMC_RATE_LIMIT_RPM:-30}"

exec ./.venv/bin/python -m uvicorn app.main:app --reload
