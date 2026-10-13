"""
LoRA and SFT Configuration for Open-Weight Coder Model Fine-Tuning.
"""
from dataclasses import asdict, dataclass, field
import json
from typing import Any, Dict, List, Optional


@dataclass
class LoRATrainingConfig:
    base_model_name: str = "deepseek-ai/deepseek-coder-1.3b-base"
    output_dir: str = "./checkpoints/observer-coder-lora"
    dataset_path: str = "./data/train_sft.jsonl"
    eval_dataset_path: Optional[str] = "./data/val_sft.jsonl"

    # LoRA / PEFT parameters
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    bias: str = "none"
    task_type: str = "CAUSAL_LM"
    target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"
    ])

    # Training Hyperparameters
    learning_rate: float = 2e-4
    per_device_train_batch_size: int = 4
    per_device_eval_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    num_train_epochs: int = 3
    warmup_ratio: float = 0.03
    lr_scheduler_type: str = "cosine"
    max_seq_length: int = 2048
    weight_decay: float = 0.01

    # Hardware & Performance
    fp16: bool = False
    bf16: bool = False
    logging_steps: int = 10
    save_strategy: str = "epoch"
    evaluation_strategy: str = "epoch"
    seed: int = 42

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoRATrainingConfig":
        valid_keys = {k for k in cls.__dataclass_fields__.keys()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


DEFAULT_LORA_CONFIG = LoRATrainingConfig()
