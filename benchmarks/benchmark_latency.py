#!/usr/bin/env python3
"""Measure client-observed latency and API usage for VOLT chat completions.

Example (PowerShell):
  $env:VOLT_API_KEY = "..."
  python benchmarks/benchmark_latency.py --base-url https://volt-ai-lmgz.onrender.com --samples 20

Results contain timings and aggregate usage metadata, not prompts or responses.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((p / 100) * (len(ordered) - 1))))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("VOLT_BASE_URL", "https://volt-ai-lmgz.onrender.com"))
    parser.add_argument("--api-key-env", default="VOLT_API_KEY", help="Environment variable containing the API key")
    parser.add_argument("--model", default="VOLT-AI")
    parser.add_argument("--prompt", default="Explain binary search in Java with a small example.")
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--output", default="benchmarks/results/latest.jsonl")
    args = parser.parse_args()

    if args.samples < 1 or args.warmups < 0:
        parser.error("--samples must be >= 1 and --warmups must be >= 0")
    api_key = os.getenv(args.api_key_env)
    if not api_key:
        parser.error(f"Missing API key environment variable: {args.api_key_env}")

    endpoint = args.base_url.rstrip("/") + "/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body: dict[str, Any] = {
        "model": args.model,
        "messages": [{"role": "user", "content": args.prompt}],
        "stream": False,
    }

    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    with httpx.Client(timeout=args.timeout) as client:
        for index in range(args.warmups + args.samples):
            started = time.perf_counter()
            try:
                response = client.post(endpoint, headers=headers, json=body)
                elapsed_ms = (time.perf_counter() - started) * 1000
                response.raise_for_status()
                data = response.json()
                usage = data.get("usage") or {}
                coordination = data.get("volt_coordination") or data.get("observer_coordination") or {}
                row = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "sample": index - args.warmups if index >= args.warmups else None,
                    "status_code": response.status_code,
                    "client_latency_ms": round(elapsed_ms, 2),
                    "server_latency_ms": coordination.get("latency_ms"),
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens"),
                    "total_tokens": usage.get("total_tokens"),
                    "track": coordination.get("track"),
                    "specialists_used": coordination.get("specialists_used"),
                }
                if index >= args.warmups:
                    rows.append(row)
                print(f"[{'warmup' if index < args.warmups else index - args.warmups + 1}] {elapsed_ms:.0f} ms")
            except (httpx.HTTPError, ValueError) as exc:
                elapsed_ms = (time.perf_counter() - started) * 1000
                message = f"{type(exc).__name__}: {exc}"
                errors.append(message)
                if index >= args.warmups:
                    rows.append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "sample": index - args.warmups,
                        "client_latency_ms": round(elapsed_ms, 2),
                        "error": type(exc).__name__,
                    })
                print(f"[error] {message}", file=sys.stderr)

    successful = [r for r in rows if "error" not in r]
    latencies = [float(r["client_latency_ms"]) for r in successful]
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "model": args.model,
        "requested_samples": args.samples,
        "successful_samples": len(successful),
        "failed_samples": len(rows) - len(successful),
        "mean_client_latency_ms": round(statistics.mean(latencies), 2) if latencies else None,
        "p50_client_latency_ms": percentile(latencies, 50),
        "p95_client_latency_ms": percentile(latencies, 95),
        "mean_server_latency_ms": round(statistics.mean([float(r["server_latency_ms"]) for r in successful if r.get("server_latency_ms") is not None]), 2) if any(r.get("server_latency_ms") is not None for r in successful) else None,
        "input_tokens": sum(int(r.get("prompt_tokens") or 0) for r in successful),
        "output_tokens": sum(int(r.get("completion_tokens") or 0) for r in successful),
        "errors": errors,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({"summary": summary}, ensure_ascii=False) + "\n")
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2))
    print(f"Saved results to {output}")
    return 0 if successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
