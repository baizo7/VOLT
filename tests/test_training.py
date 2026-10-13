import json
import os
import pytest
from training.lora_config import LoRATrainingConfig
from training.train_lora import validate_dataset_file, run_training_dry_run
from training.evaluate_finetuned import compare_model_evaluations, format_comparison_markdown_report


def test_lora_config_serialization():
    cfg = LoRATrainingConfig(
        base_model_name="Qwen/Qwen2.5-Coder-1.5B",
        lora_r=32,
        lora_alpha=64,
        learning_rate=3e-4,
    )
    d = cfg.to_dict()
    assert d["base_model_name"] == "Qwen/Qwen2.5-Coder-1.5B"
    assert d["lora_r"] == 32
    assert d["lora_alpha"] == 64
    assert d["learning_rate"] == 3e-4

    # Round trip
    reloaded = LoRATrainingConfig.from_dict(d)
    assert reloaded.base_model_name == cfg.base_model_name
    assert reloaded.lora_r == cfg.lora_r


def test_validate_dataset_file_and_dry_run(tmp_path):
    dataset_file = tmp_path / "train_sft.jsonl"
    output_dir = tmp_path / "checkpoints"

    # Write valid sample JSONL
    sample_lines = [
        {"messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "World"}]},
        {"messages": [{"role": "user", "content": "Code"}, {"role": "assistant", "content": "def f(): pass"}]},
    ]
    with open(dataset_file, "w", encoding="utf-8") as f:
        for item in sample_lines:
            f.write(json.dumps(item) + "\n")

    # Validate dataset
    stats = validate_dataset_file(str(dataset_file))
    assert stats["valid"] is True
    assert stats["records_count"] == 2
    assert stats["avg_turns"] == 2.0

    # Dry-run training
    cfg = LoRATrainingConfig(
        dataset_path=str(dataset_file),
        output_dir=str(output_dir)
    )
    summary = run_training_dry_run(cfg)
    assert summary["status"] == "completed_dry_run"
    assert os.path.exists(output_dir / "training_summary.json")


def test_validate_dataset_file_invalid(tmp_path):
    bad_file = tmp_path / "bad.jsonl"
    with open(bad_file, "w", encoding="utf-8") as f:
        f.write(json.dumps({"invalid": "no messages"}) + "\n")

    with pytest.raises(ValueError, match="missing 'messages' list"):
        validate_dataset_file(str(bad_file))


def test_compare_model_evaluations_and_report():
    base_results = {
        "models": {"base-model": {"pass_rate": 0.50, "avg_latency_ms": 400}},
        "runs": [
            {"task_name": "task-1", "passed": True},
            {"task_name": "task-2", "passed": False},
        ]
    }
    finetuned_results = {
        "models": {"finetuned-lora": {"pass_rate": 1.00, "avg_latency_ms": 350}},
        "runs": [
            {"task_name": "task-1", "passed": True},
            {"task_name": "task-2", "passed": True},
        ]
    }

    comparison = compare_model_evaluations(
        base_results=base_results,
        finetuned_results=finetuned_results,
        base_model_name="base-model",
        finetuned_model_name="finetuned-lora"
    )

    assert comparison["is_improved"] is True
    assert comparison["pass_rate_delta"] == 0.50
    assert comparison["wins"] == 1  # task-2 was fixed
    assert comparison["losses"] == 0
    assert comparison["ties"] == 1   # task-1 passed both

    report = format_comparison_markdown_report(comparison)
    assert "# Model Fine-Tuning Evaluation & Regression Report" in report
    assert "🏆 IMPROVED" in report
    assert "**+50.0%**" in report
    assert "WIN (Fixed failure)" in report
