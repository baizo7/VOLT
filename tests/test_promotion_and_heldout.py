import json
import os
import pytest
from benchmarks.heldout_benchmark import HELDOUT_BENCHMARK_TASKS
from training.evaluate_heldout import evaluate_heldout_suite
from training.promotion_policy import (
    QualityThresholds,
    evaluate_adapter_promotion,
    promote_adapter,
    rollback_adapter,
)


def test_heldout_benchmark_structure():
    assert len(HELDOUT_BENCHMARK_TASKS) == 10
    task_ids = set()
    for t in HELDOUT_BENCHMARK_TASKS:
        assert t.id.startswith("heldout-")
        assert t.id not in task_ids
        task_ids.add(t.id)
        assert len(t.prompt) > 30
        assert len(t.verification_code) > 20


def test_evaluate_heldout_suite_execution():
    rep = evaluate_heldout_suite()
    assert rep["total_tasks"] == 10
    assert rep["base_pass_rate"] >= 0.0
    assert rep["adapter_pass_rate"] > rep["base_pass_rate"]
    assert rep["pass_rate_delta"] > 0
    assert len(rep["base_runs"]) == 10
    assert len(rep["adapter_runs"]) == 10
    assert rep["regressions_count"] == 0
    assert rep["fixed_tasks_count"] >= 1


def test_promotion_policy_gating_success():
    report = {
        "adapter_pass_rate": 0.90,
        "pass_rate_delta": 0.20,
        "regressions_count": 0,
        "base_avg_latency_ms": 100,
        "adapter_avg_latency_ms": 110,
    }
    decision = evaluate_adapter_promotion(report)
    assert decision["eligible"] is True
    assert decision["decision"] == "PROMOTE"
    assert len(decision["violations"]) == 0


def test_promotion_policy_gating_rejection_on_regression():
    # High pass rate, but has 1 regression on previously passing task
    report = {
        "adapter_pass_rate": 0.90,
        "pass_rate_delta": 0.20,
        "regressions_count": 1,
        "base_avg_latency_ms": 100,
        "adapter_avg_latency_ms": 110,
    }
    decision = evaluate_adapter_promotion(report)
    assert decision["eligible"] is False
    assert decision["decision"] == "REJECT_AND_ROLLBACK"
    assert any("regressions" in v for v in decision["violations"])


def test_promotion_and_rollback_operations(tmp_path):
    candidate = tmp_path / "candidate_adapter"
    active = tmp_path / "active_adapter"
    backup = tmp_path / "last_known_good"

    os.makedirs(candidate)
    with open(candidate / "adapter_config.json", "w") as f:
        f.write('{"model": "candidate"}')

    # 1. Promote candidate to active
    promote_adapter(str(candidate), str(active), str(backup))
    assert os.path.exists(active / "adapter_config.json")
    assert not os.path.exists(backup)  # No prior active adapter to back up

    # 2. Promote candidate v2 (should back up candidate v1)
    candidate_v2 = tmp_path / "candidate_v2"
    os.makedirs(candidate_v2)
    with open(candidate_v2 / "adapter_config.json", "w") as f:
        f.write('{"model": "v2"}')

    promote_adapter(str(candidate_v2), str(active), str(backup))
    with open(active / "adapter_config.json") as f:
        assert json.load(f)["model"] == "v2"
    with open(backup / "adapter_config.json") as f:
        assert json.load(f)["model"] == "candidate"

    # 3. Rollback active to backup
    res = rollback_adapter(str(active), str(backup))
    assert res["status"] == "rolled_back"
    with open(active / "adapter_config.json") as f:
        assert json.load(f)["model"] == "candidate"
