#!/usr/bin/env python3
import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    idx = int((0.95 * len(xs)) - 1)
    idx = max(0, min(idx, len(xs) - 1))
    return xs[idx]

def to_int(s: str | None, default: int = 0) -> int:
    try:
        return int(s) if s is not None and s != "" else default
    except Exception:
        return default

def post_json(url: str, payload: dict) -> tuple[int, dict | None, dict, float]:
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

    t0 = time.perf_counter()
    try:
        with urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            headers = dict(resp.headers)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            return resp.status, json.loads(body), headers, latency_ms
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        latency_ms = (time.perf_counter() - t0) * 1000.0
        try:
            obj = json.loads(body) if body else None
        except Exception:
            obj = None
        return e.code, obj, dict(e.headers) if e.headers else {}, latency_ms
    except URLError as e:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return 0, {"error": str(e)}, {}, latency_ms

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="eval/evalset_v1.jsonl")
    ap.add_argument("--url", default="http://127.0.0.1:8000/answer")
    ap.add_argument("--out", default="")
    ap.add_argument("--report", default="docs/report_baseline.md")
    ap.add_argument("--sleep-seconds", type=float, default=2.1)  # respects 30 RPM
    ap.add_argument("--max-questions", type=int, default=int(os.getenv("EVAL_MAX_QUESTIONS", "200")))
    ap.add_argument("--price-in-per-1k", type=float, default=float(os.getenv("EVAL_PRICE_IN_PER_1K", "0")))
    ap.add_argument("--price-out-per-1k", type=float, default=float(os.getenv("EVAL_PRICE_OUT_PER_1K", "0")))
    args = ap.parse_args()

    inp = Path(args.input)
    out_dir = Path("eval/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(args.out) if args.out else out_dir / f"outputs_{inp.stem}_{ts}.jsonl"
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    rows = [json.loads(line) for line in inp.read_text().splitlines() if line.strip()]
    rows = rows[: args.max_questions]

    latencies: list[float] = []
    n_http_ok = 0
    n_json_ok = 0
    n_refusal_correct = 0
    n_nonrefusal = 0
    n_cited_nonrefusal = 0
    n_unanswerable = 0
    n_answerable = 0
    sum_in_tok = 0
    sum_out_tok = 0

    failures: list[dict] = []

    with out_path.open("w", encoding="utf-8") as f:
        for i, r in enumerate(rows, start=1):
            qid = r["id"]
            question = r["question"]
            expected_answerable = bool(r["expected_answerable"])

            status, obj, headers, latency_ms = post_json(args.url, {"question": question, "top_k": 3})
            latencies.append(latency_ms)

            if status == 200:
                n_http_ok += 1

            # token headers (may be missing on pre-LLM refusals)
            in_tok = to_int(headers.get("x-afmc-input-tokens"))
            out_tok = to_int(headers.get("x-afmc-output-tokens"))
            sum_in_tok += in_tok
            sum_out_tok += out_tok

            ok_json = isinstance(obj, dict) and ("answer" in obj) and ("refusal" in obj) and ("citations" in obj)
            if ok_json:
                n_json_ok += 1

            refusal = bool(obj.get("refusal")) if isinstance(obj, dict) else False
            citations = obj.get("citations") if isinstance(obj, dict) else None
            cited = isinstance(citations, list) and len(citations) > 0

            if expected_answerable:
                n_answerable += 1
                correct = (refusal is False)
            else:
                n_unanswerable += 1
                correct = (refusal is True)

            if correct:
                n_refusal_correct += 1
            else:
                failures.append(
                    {
                        "id": qid,
                        "expected_answerable": expected_answerable,
                        "status": status,
                        "refusal": refusal,
                        "answer_preview": (obj.get("answer", "")[:160] + "…") if isinstance(obj, dict) else "",
                    }
                )

            if not refusal:
                n_nonrefusal += 1
                if cited:
                    n_cited_nonrefusal += 1

            rec = {
                "id": qid,
                "question": question,
                "expected_answerable": expected_answerable,
                "http_status": status,
                "latency_ms": round(latency_ms, 2),
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "response": obj,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

            if args.sleep_seconds > 0 and i != len(rows):
                time.sleep(args.sleep_seconds)

    total = len(rows)
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    p95_latency = p95(latencies)

    json_valid_rate = (n_json_ok / total) if total else 0.0
    http_ok_rate = (n_http_ok / total) if total else 0.0
    refusal_correct_rate = (n_refusal_correct / total) if total else 0.0
    citation_rate_nonrefusal = (n_cited_nonrefusal / n_nonrefusal) if n_nonrefusal else 0.0

    est_cost = 0.0
    if args.price_in_per_1k > 0 or args.price_out_per_1k > 0:
        est_cost = (sum_in_tok / 1000.0) * args.price_in_per_1k + (sum_out_tok / 1000.0) * args.price_out_per_1k

    lines = []
    lines.append(f"# Eval Baseline Report\n")
    lines.append(f"- Input: `{args.input}`\n")
    lines.append(f"- Output: `{out_path.as_posix()}`\n")
    lines.append(f"- URL: `{args.url}`\n")
    lines.append(f"- Total questions: **{total}** (answerable={n_answerable}, unanswerable={n_unanswerable})\n")
    lines.append("\n## Metrics\n")
    lines.append(f"- HTTP 200 rate: **{http_ok_rate:.1%}**\n")
    lines.append(f"- JSON validity rate: **{json_valid_rate:.1%}**\n")
    lines.append(f"- Refusal correctness: **{refusal_correct_rate:.1%}**\n")
    lines.append(f"- Citation rate (non-refusals): **{citation_rate_nonrefusal:.1%}** (non-refusals={n_nonrefusal})\n")
    lines.append(f"- Avg latency: **{avg_latency:.1f} ms**\n")
    lines.append(f"- P95 latency: **{p95_latency:.1f} ms**\n")
    lines.append(f"- Total tokens in/out: **{sum_in_tok} / {sum_out_tok}**\n")
    if est_cost > 0:
        lines.append(f"- Estimated cost: **${est_cost:.4f}** (using EVAL_PRICE_IN_PER_1K/EVAL_PRICE_OUT_PER_1K)\n")

    if failures:
        lines.append("\n## Failures (first 10)\n")
        for x in failures[:10]:
            lines.append(f"- {x['id']}: expected_answerable={x['expected_answerable']} status={x['status']} refusal={x['refusal']} preview=\"{x['answer_preview']}\"\n")
    else:
        lines.append("\n## Failures\n- None 🎉\n")

    report_path.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote: {out_path}")
    print(f"Wrote: {report_path}")

if __name__ == "__main__":
    main()
