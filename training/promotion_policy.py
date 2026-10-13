"""
Quality Gating and Adapter Promotion / Rollback Policy.

Ensures that new fine-tuned LoRA adapters are promoted to active serving ONLY
when they meet strict quality thresholds on held-out benchmarks, with guaranteed
zero-regression gating and automated rollback to the last-known-good adapter.
"""
from dataclasses import dataclass
import json
import logging
import os
import shutil
import time
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("observer.promotion_policy")


@dataclass
class QualityThresholds:
    min_pass_rate: float = 0.80           # Must achieve at least 80% on held-out tasks
    max_regressions_allowed: int = 0      # Zero regressions on tasks base model solved
    min_improvement_delta: float = 0.05   # Must show at least +5% improvement
    max_latency_ratio: float = 1.30       # Latency cannot exceed 130% of base model


DEFAULT_THRESHOLDS = QualityThresholds()


def evaluate_adapter_promotion(
    evaluation_report: Dict[str, Any],
    thresholds: QualityThresholds = DEFAULT_THRESHOLDS
) -> Dict[str, Any]:
    """
    Evaluate whether a newly fine-tuned adapter qualifies for serving promotion.
    """
    pass_rate = evaluation_report.get("adapter_pass_rate", 0.0)
    delta = evaluation_report.get("pass_rate_delta", 0.0)
    regressions = evaluation_report.get("regressions_count", 0)
    base_lat = evaluation_report.get("base_avg_latency_ms", 100)
    adapter_lat = evaluation_report.get("adapter_avg_latency_ms", 100)

    latency_ratio = round(adapter_lat / base_lat, 2) if base_lat > 0 else 1.0

    violations: List[str] = []

    if pass_rate < thresholds.min_pass_rate:
        violations.append(
            f"Pass rate ({pass_rate * 100:.1f}%) below minimum required threshold ({thresholds.min_pass_rate * 100:.1f}%)"
        )

    if regressions > thresholds.max_regressions_allowed:
        violations.append(
            f"Detected {regressions} regressions on tasks that previously passed in the base model (maximum allowed: {thresholds.max_regressions_allowed})"
        )

    if delta < thresholds.min_improvement_delta:
        violations.append(
            f"Pass rate improvement ({delta * 100:+.1f}%) below required threshold ({thresholds.min_improvement_delta * 100:+.1f}%)"
        )

    if latency_ratio > thresholds.max_latency_ratio:
        violations.append(
            f"Latency ratio ({latency_ratio}x) exceeds allowed tolerance ({thresholds.max_latency_ratio}x)"
        )

    eligible = len(violations) == 0
    decision = "PROMOTE" if eligible else "REJECT_AND_ROLLBACK"

    logger.info(f"Promotion gate evaluation: {decision} (Violations: {len(violations)})")

    return {
        "eligible": eligible,
        "decision": decision,
        "adapter_pass_rate": pass_rate,
        "pass_rate_delta": delta,
        "regressions_count": regressions,
        "latency_ratio": latency_ratio,
        "violations": violations,
        "evaluation_timestamp": time.time(),
    }


def promote_adapter(
    candidate_adapter_dir: str,
    active_adapter_dir: str = "./checkpoints/active_adapter",
    backup_adapter_dir: str = "./checkpoints/last_known_good_adapter"
) -> Dict[str, Any]:
    """
    Atomically promote candidate adapter:
    1. Backs up current active adapter to last_known_good_adapter
    2. Deploys candidate adapter to active_adapter
    """
    os.makedirs(os.path.dirname(os.path.abspath(active_adapter_dir)), exist_ok=True)

    # 1. Backup existing active adapter if present
    if os.path.exists(active_adapter_dir) and os.listdir(active_adapter_dir):
        if os.path.exists(backup_adapter_dir):
            shutil.rmtree(backup_adapter_dir)
        shutil.copytree(active_adapter_dir, backup_adapter_dir)
        logger.info(f"Backed up previous active adapter to {backup_adapter_dir}")

    # 2. Deploy candidate to active adapter
    if os.path.exists(active_adapter_dir):
        shutil.rmtree(active_adapter_dir)
    shutil.copytree(candidate_adapter_dir, active_adapter_dir)

    status_meta = {
        "status": "promoted",
        "source_checkpoint": candidate_adapter_dir,
        "active_adapter_dir": active_adapter_dir,
        "backup_adapter_dir": backup_adapter_dir,
        "promoted_at": time.time(),
    }

    with open(os.path.join(active_adapter_dir, "promotion_status.json"), "w", encoding="utf-8") as f:
        json.dump(status_meta, f, indent=2)

    logger.info(f"Successfully promoted adapter from {candidate_adapter_dir} to {active_adapter_dir}")
    return status_meta


def rollback_adapter(
    active_adapter_dir: str = "./checkpoints/active_adapter",
    backup_adapter_dir: str = "./checkpoints/last_known_good_adapter"
) -> Dict[str, Any]:
    """Roll back active adapter to last known good adapter."""
    if not os.path.exists(backup_adapter_dir) or not os.listdir(backup_adapter_dir):
        logger.warning(f"No backup adapter found at {backup_adapter_dir} for rollback.")
        return {"status": "rollback_failed", "error": "No backup adapter exists"}

    if os.path.exists(active_adapter_dir):
        shutil.rmtree(active_adapter_dir)
    shutil.copytree(backup_adapter_dir, active_adapter_dir)

    meta = {
        "status": "rolled_back",
        "active_adapter_dir": active_adapter_dir,
        "restored_from": backup_adapter_dir,
        "rolled_back_at": time.time(),
    }
    with open(os.path.join(active_adapter_dir, "promotion_status.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info(f"Successfully rolled back active adapter to {backup_adapter_dir}")
    return meta
