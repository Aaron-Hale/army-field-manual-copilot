import os

def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default

def _get_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")

# Caps
TOP_K_MAX = _get_int("AFMC_TOP_K_MAX", 5)
MAX_CONTEXT_TOKENS = _get_int("AFMC_MAX_CONTEXT_TOKENS", 1800)

# “No evidence” gating
MIN_RETRIEVAL_SCORE = _get_float("AFMC_MIN_RETRIEVAL_SCORE", 0.45)
REQUIRE_CITATIONS = _get_bool("AFMC_REQUIRE_CITATIONS", True)

# Simple per-process rate limit (per IP). Set to 0 to disable.
RATE_LIMIT_RPM = _get_int("AFMC_RATE_LIMIT_RPM", 30)
