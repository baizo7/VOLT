"""
Report generator for benchmark evaluation results.
"""
from typing import Any, Dict


def format_benchmark_markdown_report(benchmark_results: Dict[str, Any]) -> str:
    """Format benchmark results into a clean markdown table."""
    models_data = benchmark_results.get("models", {})
    runs = benchmark_results.get("runs", [])

    lines = [
        "# Model Benchmark Evaluation Report",
        "",
        "## Summary Leaderboard",
        "",
        "| Model | Total Tasks | Passes | Fails | Pass Rate | Avg Latency (ms) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]

    sorted_models = sorted(
        models_data.items(),
        key=lambda item: item[1].get("pass_rate", 0),
        reverse=True
    )

    for model, stats in sorted_models:
        pass_pct = f"{stats.get('pass_rate', 0) * 100:.1f}%"
        lines.append(
            f"| `{model}` | {stats.get('total', 0)} | {stats.get('passes', 0)} | "
            f"{stats.get('fails', 0)} | **{pass_pct}** | {stats.get('avg_latency_ms', 0)} |"
        )

    lines.extend([
        "",
        "## Task Run Details",
        "",
        "| Task ID | Task Type | Model | Status | Latency (ms) | Error |",
        "| :--- | :--- | :--- | :---: | :---: | :--- |",
    ])

    for r in runs:
        status_badge = "✅ PASS" if r.get("passed") else "❌ FAIL"
        err_msg = r.get("error") or "-"
        if len(err_msg) > 60:
            err_msg = err_msg[:57] + "..."
        lines.append(
            f"| `{r.get('task_name')}` | {r.get('task_type')} | `{r.get('model')}` | "
            f"{status_badge} | {r.get('latency_ms')} | {err_msg} |"
        )

    return "\n".join(lines)
