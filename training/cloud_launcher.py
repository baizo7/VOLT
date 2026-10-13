"""
Standalone Cloud GPU Training & Evaluation Launcher for Qwen2.5-Coder-1.5B.

Can be run on RunPod, Modal, Google Colab, Lambda Labs, or local GPU workstations.
Executes:
1. GPU hardware audit (device, VRAM, compute capability)
2. Qwen2.5-Coder-1.5B LoRA fine-tuning on curated SFT telemetry
3. Held-out benchmark evaluation on unseen coding tasks
4. Quality gating and promotion decision
"""
import argparse
import json
import logging
import os
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("observer.cloud_launcher")


def main():
    parser = argparse.ArgumentParser(description="Cloud GPU Trainer and Evaluator")
    parser.add_argument("--dataset", default="./data/curated_sft.jsonl", help="Path to SFT JSONL dataset")
    parser.add_argument("--output", default="./checkpoints/qwen2.5-coder-1.5b-adapter", help="Adapter save directory")
    parser.add_argument("--model", default="Qwen/Qwen2.5-Coder-1.5B", help="Base coder model")
    parser.add_argument("--rank", type=int, default=16, help="LoRA rank")
    parser.add_argument("--alpha", type=int, default=32, help="LoRA alpha")
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Per device batch size")
    parser.add_argument("--verify-mode", action="store_true", help="Run verification check without full GPU weights")
    args = parser.parse_args()

    logger.info("=== STEP 1: Inspecting Compute Hardware ===")
    import torch
    has_cuda = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if has_cuda else "CPU"
    vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2) if has_cuda else 0.0

    logger.info(f"Compute Device: {device_name}")
    logger.info(f"CUDA Available: {has_cuda}")
    logger.info(f"Available VRAM: {vram_gb} GB")

    from training.train_qwen_gpu import run_qwen_gpu_training
    from training.evaluate_heldout import evaluate_heldout_suite
    from training.promotion_policy import evaluate_adapter_promotion, promote_adapter

    logger.info("\n=== STEP 2: Running LoRA Training on Qwen2.5-Coder-1.5B ===")
    training_summary = run_qwen_gpu_training(
        dataset_path=args.dataset,
        output_dir=args.output,
        model_name=args.model,
        lora_r=args.rank,
        lora_alpha=args.alpha,
        num_train_epochs=args.epochs,
        batch_size=args.batch_size,
        verify_mode=args.verify_mode,
    )

    logger.info("\n=== STEP 3: Evaluating Held-Out Benchmark on Unseen Tasks ===")
    eval_report = evaluate_heldout_suite()

    logger.info("\n=== STEP 4: Evaluating Quality Gating & Promotion ===")
    gating = evaluate_adapter_promotion(eval_report)

    if gating["eligible"]:
        logger.info("Adapter passed all quality gates! Promoting to active serving pointer...")
        promotion_result = promote_adapter(
            candidate_adapter_dir=args.output,
            active_adapter_dir="./checkpoints/active_adapter",
            backup_adapter_dir="./checkpoints/last_known_good_adapter"
        )
    else:
        logger.warning(f"Adapter did NOT meet promotion criteria: {gating['violations']}")
        promotion_result = {"status": "rejected", "reasons": gating["violations"]}

    full_experiment_report = {
        "hardware": {
            "device": device_name,
            "cuda_available": has_cuda,
            "vram_gb": vram_gb,
        },
        "training": training_summary,
        "evaluation": eval_report,
        "gating": gating,
        "promotion": promotion_result,
    }

    report_path = "./checkpoints/experiment_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(full_experiment_report, f, indent=2)

    logger.info(f"\nExperiment complete! Report saved to {report_path}")
    print(json.dumps(full_experiment_report, indent=2))


if __name__ == "__main__":
    main()
