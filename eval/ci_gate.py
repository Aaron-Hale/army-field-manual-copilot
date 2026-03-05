#!/usr/bin/env python3
import sys
from pathlib import Path

def extract_percent(lines: list[str], prefix: str) -> float:
    line = next((l for l in lines if l.strip().startswith(prefix)), None)
    if not line:
        raise ValueError(f"Could not find line starting with: {prefix}")
    # Example: "- Citation rate (non-refusals): **100.0%** (non-refusals=8)"
    parts = line.split("**")
    if len(parts) < 2:
        raise ValueError(f"Could not parse percent from line: {line}")
    val = parts[1].replace("%", "").strip()
    return float(val)

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python eval/ci_gate.py <report_md_path>")
        sys.exit(2)

    report_path = Path(sys.argv[1])
    txt = report_path.read_text(encoding="utf-8")
    lines = txt.splitlines()

    http_200 = extract_percent(lines, "- HTTP 200 rate:")
    json_valid = extract_percent(lines, "- JSON validity rate:")
    refusal_correct = extract_percent(lines, "- Refusal correctness:")
    citation_rate = extract_percent(lines, "- Citation rate (non-refusals):")

    # Gates
    if http_200 < 95.0:
        sys.exit(f"HTTP 200 rate too low: {http_200}%")
    if json_valid < 100.0:
        sys.exit(f"JSON validity must be 100%: {json_valid}%")
    if citation_rate < 95.0:
        sys.exit(f"Citation rate too low: {citation_rate}%")
    if refusal_correct < 90.0:
        sys.exit(f"Refusal correctness too low: {refusal_correct}%")

    print("CI gates passed:", {
        "http_200": http_200,
        "json_valid": json_valid,
        "citation_rate": citation_rate,
        "refusal_correct": refusal_correct,
    })

if __name__ == "__main__":
    main()
