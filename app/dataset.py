"""
Dataset Curation and Export Engine for Supervised Fine-Tuning (SFT) and Direct Preference Optimization (DPO).

Extracts high-quality training pairs from verified LLM telemetry where tasks
passed builds, tests, or code reviews, ensuring sensitive credentials remain scrubbed.
"""
import hashlib
import json
import random
from typing import Any, Dict, List, Optional, Tuple
import asyncpg
from app.config import logger
from app.security import scrub_json, scrub_text


def extract_conversation_turns(request_body: Any, response_text: Optional[str], api_style: str = "openai") -> List[Dict[str, str]]:
    """
    Normalize raw request payloads and model completions into standard OpenAI-style messages list:
    [{"role": "user", "content": ...}, {"role": "assistant", "content": ...}]
    """
    messages: List[Dict[str, str]] = []
    if isinstance(request_body, str):
        try:
            request_body = json.loads(request_body)
        except Exception:
            return messages
    if not isinstance(request_body, dict):
        return messages

    if api_style == "anthropic":
        # Anthropic format: system prompt (optional) + messages list
        system_prompt = request_body.get("system")
        if system_prompt:
            messages.append({"role": "system", "content": str(system_prompt)})
        for m in request_body.get("messages", []):
            role = m.get("role", "user")
            content = m.get("content", "")
            if isinstance(content, list):
                has_image = any(isinstance(b, dict) and b.get("type") in ("image_url", "image") for b in content)
                if has_image:
                    messages.append({"role": role, "content": content})
                    continue
                # Anthropic content blocks
                text_parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
                content = "\n".join(text_parts)
            if content:
                messages.append({"role": role, "content": str(content)})
    else:
        # OpenAI format: messages list
        for m in request_body.get("messages", []):
            role = m.get("role", "user")
            content = m.get("content", "")
            if isinstance(content, list):
                has_image = any(isinstance(b, dict) and b.get("type") in ("image_url", "image") for b in content)
                if has_image:
                    messages.append({"role": role, "content": content})
                    continue
                text_parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
                content = "\n".join(text_parts)
            if content:
                messages.append({"role": role, "content": str(content)})

    # Append the assistant completion if available and not already present
    if response_text and (not messages or messages[-1]["role"] != "assistant"):
        messages.append({"role": "assistant", "content": response_text})

    return messages


def compute_content_hash(text: str) -> str:
    """Compute sha256 hash for deduplication."""
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


async def fetch_verified_calls(
    pool: asyncpg.Pool,
    project: Optional[str] = None,
    task_type: Optional[str] = None,
    verified_statuses: Optional[List[str]] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Query LLM calls that are tied to verified passing/accepted outcomes."""
    statuses = verified_statuses or ["pass", "accepted"]

    query = """
        SELECT c.id, c.task_id, c.project, c.task_type, c.model, c.api_style,
               c.request, c.response_text, c.latency_ms, c.input_tokens, c.output_tokens,
               o.status AS outcome_status, o.kind AS outcome_kind, c.ts
        FROM llm_calls c
        JOIN outcomes o ON o.task_id = c.task_id
        WHERE o.status = ANY($1::text[])
          AND c.response_text IS NOT NULL
          AND c.response_text != ''
          AND (c.status_code IS NULL OR c.status_code = 200)
    """
    params: List[Any] = [statuses]
    idx = 2

    if project:
        query += f" AND (c.project = ${idx} OR c.project IS NULL)"
        params.append(project)
        idx += 1

    if task_type:
        query += f" AND c.task_type = ${idx}"
        params.append(task_type)
        idx += 1

    query += " ORDER BY c.ts DESC"
    if limit:
        query += f" LIMIT ${idx}"
        params.append(limit)

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
        return [dict(r) for r in rows]


def format_sft_record(call: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Format a single call into standard SFT JSONL format with scrubbing."""
    req_raw = call.get("request")
    if isinstance(req_raw, str):
        try:
            req_raw = json.loads(req_raw)
        except Exception:
            pass
    request_data = scrub_json(req_raw)
    response_text = scrub_text(call.get("response_text"))

    if not request_data or not response_text:
        return None

    messages = extract_conversation_turns(request_data, response_text, api_style=call.get("api_style", "openai"))
    # Minimum requirement: at least 1 user turn and 1 assistant turn
    has_user = any(m["role"] == "user" for m in messages)
    has_assistant = any(m["role"] == "assistant" for m in messages)

    if not (has_user and has_assistant):
        return None

    return {
        "messages": messages,
        "metadata": {
            "call_id": str(call.get("id")),
            "task_id": call.get("task_id"),
            "task_type": call.get("task_type"),
            "model": call.get("model"),
            "project": call.get("project"),
            "outcome_status": call.get("outcome_status"),
        }
    }


async def export_sft_dataset(
    pool: asyncpg.Pool,
    project: Optional[str] = None,
    task_type: Optional[str] = None,
    verified_statuses: Optional[List[str]] = None,
    limit: Optional[int] = None,
    deduplicate: bool = True
) -> List[Dict[str, Any]]:
    """
    Export supervised fine-tuning (SFT) dataset containing multi-turn conversations
    from verified successful task runs.
    """
    raw_calls = await fetch_verified_calls(
        pool=pool,
        project=project,
        task_type=task_type,
        verified_statuses=verified_statuses,
        limit=limit
    )

    dataset: List[Dict[str, Any]] = []
    seen_hashes = set()

    for call in raw_calls:
        formatted = format_sft_record(call)
        if not formatted:
            continue

        if deduplicate:
            # Hash prompt and completion to prevent redundant examples
            content_sig = "".join(m["content"] for m in formatted["messages"])
            h = compute_content_hash(content_sig)
            if h in seen_hashes:
                continue
            seen_hashes.add(h)

        dataset.append(formatted)

    return dataset


async def export_dpo_dataset(
    pool: asyncpg.Pool,
    project: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Export Direct Preference Optimization (DPO) pairs for preference tuning.
    Matches winning responses (pass/accepted) with losing responses (fail/rejected)
    for the same task or identical user prompt.
    """
    # 1. Fetch passing calls
    passes = await fetch_verified_calls(
        pool=pool,
        project=project,
        task_type=task_type,
        verified_statuses=["pass", "accepted"],
        limit=limit
    )

    # 2. Fetch failing calls
    fails = await fetch_verified_calls(
        pool=pool,
        project=project,
        task_type=task_type,
        verified_statuses=["fail", "rejected"],
        limit=limit
    )

    # Group passing calls by task_id and by prompt text
    pass_by_task: Dict[str, Dict[str, Any]] = {}
    pass_by_prompt: Dict[str, Dict[str, Any]] = {}

    for p in passes:
        tid = p.get("task_id")
        if tid:
            pass_by_task[tid] = p
        req = p.get("request") or {}
        msgs = extract_conversation_turns(req, None, p.get("api_style", "openai"))
        user_prompt = "\n".join(m["content"] for m in msgs if m["role"] == "user")
        if user_prompt:
            pass_by_prompt[compute_content_hash(user_prompt)] = p

    dpo_pairs: List[Dict[str, Any]] = []
    used_chosen = set()

    for f in fails:
        tid = f.get("task_id")
        matched_pass = None

        # Match by task_id first
        if tid and tid in pass_by_task:
            matched_pass = pass_by_task[tid]
        else:
            # Match by prompt content hash
            req = f.get("request") or {}
            msgs = extract_conversation_turns(req, None, f.get("api_style", "openai"))
            user_prompt = "\n".join(m["content"] for m in msgs if m["role"] == "user")
            if user_prompt:
                h = compute_content_hash(user_prompt)
                matched_pass = pass_by_prompt.get(h)

        if not matched_pass:
            continue

        chosen_text = scrub_text(matched_pass.get("response_text"))
        rejected_text = scrub_text(f.get("response_text"))

        if not chosen_text or not rejected_text or chosen_text == rejected_text:
            continue

        # Extract prompt
        p_raw = matched_pass.get("request")
        if isinstance(p_raw, str):
            try:
                p_raw = json.loads(p_raw)
            except Exception:
                pass
        p_msgs = extract_conversation_turns(
            scrub_json(p_raw), None, matched_pass.get("api_style", "openai")
        )
        prompt_parts = [m["content"] for m in p_msgs if m["role"] in ("system", "user")]
        full_prompt = "\n\n".join(prompt_parts)

        pair_key = (compute_content_hash(full_prompt), compute_content_hash(chosen_text))
        if pair_key in used_chosen:
            continue
        used_chosen.add(pair_key)

        dpo_pairs.append({
            "prompt": full_prompt,
            "chosen": chosen_text,
            "rejected": rejected_text,
            "metadata": {
                "task_id": tid or matched_pass.get("task_id"),
                "task_type": matched_pass.get("task_type") or f.get("task_type"),
                "chosen_model": matched_pass.get("model"),
                "rejected_model": f.get("model"),
                "project": matched_pass.get("project") or f.get("project"),
            }
        })

    return dpo_pairs


async def export_multimodal_dataset(
    pool: asyncpg.Pool,
    project: Optional[str] = None,
    verified_statuses: Optional[List[str]] = None,
    image_dir: Optional[str] = "./data/multimodal_images",
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Export multimodal dataset (UI screenshot + prompt -> generated code) for Vision-Language Models (Qwen2-VL).
    Saves embedded base64 image strings into image files in `image_dir` and generates JSONL records.
    """
    import base64
    from pathlib import Path

    statuses = verified_statuses or ["pass", "accepted"]
    query = """
        SELECT c.id, c.task_id, c.project, c.task_type, c.model, c.api_style,
               c.request, c.response_text, c.latency_ms, c.input_tokens, c.output_tokens,
               o.status AS outcome_status, o.kind AS outcome_kind, c.ts
        FROM llm_calls c
        JOIN outcomes o ON o.task_id = c.task_id
        WHERE o.status = ANY($1::text[])
          AND c.response_text IS NOT NULL
          AND c.response_text != ''
          AND (c.task_type = 'vision' OR c.request::text LIKE '%image_url%')
    """
    params: List[Any] = [statuses]
    idx = 2
    if project:
        query += f" AND (c.project = ${idx} OR c.project IS NULL)"
        params.append(project)
        idx += 1

    query += " ORDER BY c.ts DESC"
    if limit:
        query += f" LIMIT ${idx}"
        params.append(limit)

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
        raw_calls = [dict(r) for r in rows]

    records = []
    if image_dir:
        Path(image_dir).mkdir(parents=True, exist_ok=True)

    for call in raw_calls:
        formatted = format_sft_record(call)
        if not formatted:
            continue

        msgs = formatted["messages"]
        for m in msgs:
            content = m.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "image_url":
                        url_val = part.get("image_url", {}).get("url", "")
                        if "base64," in url_val and image_dir:
                            try:
                                header, b64_str = url_val.split("base64,", 1)
                                ext = "png"
                                if "image/jpeg" in header or "image/jpg" in header:
                                    ext = "jpg"
                                img_filename = f"img_{call['id']}.{ext}"
                                img_path = Path(image_dir) / img_filename
                                with open(img_path, "wb") as img_f:
                                    img_f.write(base64.b64decode(b64_str))
                                part["image_url"]["url"] = str(img_path.as_posix())
                            except Exception:
                                pass
        records.append(formatted)

    return records


def split_dataset(records: List[Dict[str, Any]], val_ratio: float = 0.1, seed: int = 42) -> Dict[str, List[Dict[str, Any]]]:
    """Deterministically split dataset into train and validation sets."""
    if not records:
        return {"train": [], "validation": []}

    shuffled = list(records)
    random.Random(seed).shuffle(shuffled)

    val_size = max(1, int(len(shuffled) * val_ratio)) if val_ratio > 0 and len(shuffled) > 1 else 0
    val_set = shuffled[:val_size]
    train_set = shuffled[val_size:]

    return {
        "train": train_set,
        "validation": val_set
    }


def compute_dataset_summary(records: List[Dict[str, Any]], dataset_type: str = "sft") -> Dict[str, Any]:
    """Compute token, task type, and quality statistics for dataset reporting."""
    total = len(records)
    task_types: Dict[str, int] = {}
    models_represented: Dict[str, int] = {}
    total_chars = 0

    for r in records:
        meta = r.get("metadata", {})
        tt = meta.get("task_type") or "unspecified"
        task_types[tt] = task_types.get(tt, 0) + 1

        if dataset_type == "sft":
            m_name = meta.get("model") or "unknown"
            models_represented[m_name] = models_represented.get(m_name, 0) + 1
            for m in r.get("messages", []):
                total_chars += len(m.get("content", ""))
        else:  # dpo
            m_chosen = meta.get("chosen_model") or "unknown"
            models_represented[m_chosen] = models_represented.get(m_chosen, 0) + 1
            total_chars += len(r.get("prompt", "")) + len(r.get("chosen", "")) + len(r.get("rejected", ""))

    avg_chars = int(total_chars / total) if total > 0 else 0
    estimated_tokens = int(total_chars / 4)  # ~4 chars per token rule of thumb

    return {
        "dataset_type": dataset_type,
        "total_records": total,
        "estimated_total_tokens": estimated_tokens,
        "avg_chars_per_sample": avg_chars,
        "task_types": task_types,
        "models_represented": models_represented,
    }
