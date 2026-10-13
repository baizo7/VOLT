"""
Automated benchmark runner and test harness for evaluating model performance.
"""
import asyncio
import json
import re
import time
from typing import Any, Dict, List, Optional
import httpx
from benchmarks.tasks import BENCHMARK_TASKS, BenchmarkTask


def extract_code_block(text: str) -> str:
    """Extract code from markdown blocks or return text if not wrapped."""
    match = re.search(r"```(?:python)?\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def verify_code_solution(code: str, verification_code: str) -> Dict[str, Any]:
    """Execute code along with verification code in a local namespace."""
    combined = f"from typing import *\n{code}\n{verification_code}"
    local_scope: Dict[str, Any] = {}
    try:
        exec(combined, local_scope)
        return {"passed": True, "error": None}
    except Exception as e:
        return {"passed": False, "error": f"{type(e).__name__}: {e}"}


async def run_task_on_model(
    client: httpx.AsyncClient,
    observer_base_url: str,
    task: BenchmarkTask,
    model: str,
    project: str = "benchmark-suite",
    auth_token: Optional[str] = None
) -> Dict[str, Any]:
    """Send task to observer proxy, verify code, and report outcome."""
    task_id = f"{task.id}-{model.replace('/', '-')}"
    headers = {
        "X-Task-Id": task_id,
        "X-Task-Type": task.task_type,
        "X-Project": project,
    }
    if auth_token:
        headers["X-Observer-Token"] = auth_token

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": task.prompt}
        ],
        "temperature": 0.0
    }

    t0 = time.perf_counter()
    resp = await client.post(f"{observer_base_url}/v1/chat/completions", json=payload, headers=headers)
    latency_ms = int((time.perf_counter() - t0) * 1000)

    if resp.status_code != 200:
        outcome_status = "fail"
        return {
            "task_id": task_id,
            "task_name": task.id,
            "model": model,
            "status": outcome_status,
            "latency_ms": latency_ms,
            "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
            "passed": False,
        }

    resp_json = resp.json()
    content = resp_json.get("choices", [{}])[0].get("message", {}).get("content", "")
    code = extract_code_block(content)

    test_result = verify_code_solution(code, task.verification_code)
    outcome_status = "pass" if test_result["passed"] else "fail"

    # Report verified outcome back to Observer
    outcome_payload = {
        "task_id": task_id,
        "kind": "eval_test",
        "status": outcome_status,
        "details": {
            "task_type": task.task_type,
            "model": model,
            "latency_ms": latency_ms,
            "error": test_result.get("error")
        }
    }
    await client.post(f"{observer_base_url}/outcomes", json=outcome_payload, headers=headers)

    return {
        "task_id": task_id,
        "task_name": task.id,
        "task_type": task.task_type,
        "model": model,
        "status": outcome_status,
        "passed": test_result["passed"],
        "latency_ms": latency_ms,
        "error": test_result.get("error"),
    }


async def run_benchmark_suite(
    observer_base_url: str = "http://127.0.0.1:8000",
    models: Optional[List[str]] = None,
    tasks: Optional[List[BenchmarkTask]] = None,
    auth_token: Optional[str] = None
) -> Dict[str, Any]:
    """Execute full evaluation benchmark across all models and tasks."""
    target_models = models or ["deepseek", "claude"]
    target_tasks = tasks or BENCHMARK_TASKS

    results = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for model in target_models:
            for task in target_tasks:
                res = await run_task_on_model(
                    client=client,
                    observer_base_url=observer_base_url,
                    task=task,
                    model=model,
                    auth_token=auth_token
                )
                results.append(res)

    # Aggregate results per model
    model_summaries: Dict[str, Any] = {}
    for r in results:
        m = r["model"]
        if m not in model_summaries:
            model_summaries[m] = {"total": 0, "passes": 0, "fails": 0, "total_latency": 0}
        model_summaries[m]["total"] += 1
        if r["passed"]:
            model_summaries[m]["passes"] += 1
        else:
            model_summaries[m]["fails"] += 1
        model_summaries[m]["total_latency"] += r["latency_ms"]

    for m, s in model_summaries.items():
        s["pass_rate"] = round(s["passes"] / s["total"], 4) if s["total"] > 0 else 0.0
        s["avg_latency_ms"] = int(s["total_latency"] / s["total"]) if s["total"] > 0 else 0

    return {
        "models": model_summaries,
        "runs": results,
    }
