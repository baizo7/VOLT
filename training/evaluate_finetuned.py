"""
Evaluation Harness comparing Base Model vs Fine-Tuned LoRA Adapter.
Runs standardized benchmark suite to verify fine-tuning improvements and guard against regressions.
"""
from typing import Any, Dict, List, Optional
from benchmarks.tasks import BENCHMARK_TASKS, BenchmarkTask
from benchmarks.eval_reporter import format_benchmark_markdown_report


def compare_model_evaluations(
    base_results: Dict[str, Any],
    finetuned_results: Dict[str, Any],
    base_model_name: str = "base-model",
    finetuned_model_name: str = "finetuned-lora"
) -> Dict[str, Any]:
    """
    Compare performance between base model and fine-tuned model.
    Computes pass-rate delta, latency improvements, and task-level win/loss records.
    """
    base_stats = base_results.get("models", {}).get(base_model_name, {})
    ft_stats = finetuned_results.get("models", {}).get(finetuned_model_name, {})

    base_pass_rate = base_stats.get("pass_rate", 0.0)
    ft_pass_rate = ft_stats.get("pass_rate", 0.0)

    pass_rate_delta = round(ft_pass_rate - base_pass_rate, 4)
    base_lat = base_stats.get("avg_latency_ms", 0)
    ft_lat = ft_stats.get("avg_latency_ms", 0)
    latency_delta = ft_lat - base_lat

    base_runs = {r["task_name"]: r for r in base_results.get("runs", [])}
    ft_runs = {r["task_name"]: r for r in finetuned_results.get("runs", [])}

    all_tasks = set(base_runs.keys()) | set(ft_runs.keys())
    wins = 0
    losses = 0
    ties = 0

    task_comparisons = []
    for tid in sorted(all_tasks):
        b_passed = base_runs.get(tid, {}).get("passed", False)
        f_passed = ft_runs.get(tid, {}).get("passed", False)

        if f_passed and not b_passed:
            wins += 1
            verdict = "WIN (Fixed failure)"
        elif not f_passed and b_passed:
            losses += 1
            verdict = "LOSS (Regression)"
        else:
            ties += 1
            verdict = "TIE"

        task_comparisons.append({
            "task_id": tid,
            "base_passed": b_passed,
            "finetuned_passed": f_passed,
            "verdict": verdict,
        })

    is_improved = pass_rate_delta > 0 or (pass_rate_delta == 0 and wins >= losses)

    return {
        "base_model": base_model_name,
        "finetuned_model": finetuned_model_name,
        "base_pass_rate": base_pass_rate,
        "finetuned_pass_rate": ft_pass_rate,
        "pass_rate_delta": pass_rate_delta,
        "latency_delta_ms": latency_delta,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "is_improved": is_improved,
        "task_comparisons": task_comparisons,
    }


def format_comparison_markdown_report(comparison: Dict[str, Any]) -> str:
    """Format model comparison into a structured markdown report."""
    base_pct = f"{comparison['base_pass_rate'] * 100:.1f}%"
    ft_pct = f"{comparison['finetuned_pass_rate'] * 100:.1f}%"
    delta_str = f"{comparison['pass_rate_delta'] * 100:+.1f}%"
    verdict_badge = "🏆 IMPROVED" if comparison["is_improved"] else "⚠️ REGRESSION"

    lines = [
        "# Model Fine-Tuning Evaluation & Regression Report",
        "",
        f"**Status**: {verdict_badge}",
        "",
        "## Summary Metrics",
        "",
        "| Metric | Base Model | Fine-Tuned Model | Delta |",
        "| :--- | :---: | :---: | :---: |",
        f"| **Model Name** | `{comparison['base_model']}` | `{comparison['finetuned_model']}` | - |",
        f"| **Benchmark Pass Rate** | {base_pct} | **{ft_pct}** | **{delta_str}** |",
        f"| **Head-to-Head Record** | Wins: {comparison['wins']} | Losses: {comparison['losses']} | Ties: {comparison['ties']} |",
        "",
        "## Task Breakdown",
        "",
        "| Task ID | Base Model | Fine-Tuned Model | Verdict |",
        "| :--- | :---: | :---: | :--- |",
    ]

    for t in comparison.get("task_comparisons", []):
        b_badge = "✅ PASS" if t["base_passed"] else "❌ FAIL"
        f_badge = "✅ PASS" if t["finetuned_passed"] else "❌ FAIL"
        lines.append(f"| `{t['task_id']}` | {b_badge} | {f_badge} | {t['verdict']} |")

    return "\n".join(lines)
