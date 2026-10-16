import pytest
from unittest.mock import AsyncMock, MagicMock
from app.dataset import (
    extract_conversation_turns,
    format_sft_record,
    split_dataset,
    compute_dataset_summary,
    export_sft_dataset,
    export_dpo_dataset,
)
import main


def test_extract_conversation_turns_openai():
    req = {
        "messages": [
            {"role": "system", "content": "You are a python assistant."},
            {"role": "user", "content": "Write quicksort."}
        ]
    }
    resp_text = "def quicksort(arr): return arr"
    turns = extract_conversation_turns(req, resp_text, api_style="openai")
    assert len(turns) == 3
    assert turns[0]["role"] == "system"
    assert turns[1]["role"] == "user"
    assert turns[2]["role"] == "assistant"
    assert turns[2]["content"] == resp_text


def test_extract_conversation_turns_anthropic():
    req = {
        "system": "You are a helpful coding model.",
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": "Fix this bug"}]}
        ]
    }
    resp_text = "Here is the fix: pass"
    turns = extract_conversation_turns(req, resp_text, api_style="anthropic")
    assert len(turns) == 3
    assert turns[0]["role"] == "system"
    assert turns[1]["role"] == "user"
    assert turns[1]["content"] == "Fix this bug"
    assert turns[2]["role"] == "assistant"


def test_format_sft_record_scrubs_secrets():
    raw_call = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "task_id": "task_sft_01",
        "task_type": "backend",
        "model": "deepseek-coder",
        "project": "proj-x",
        "api_style": "openai",
        "request": {
            "messages": [{"role": "user", "content": "My API key is sk-1234567890abcdef123456"}]
        },
        "response_text": "Saved key sk-1234567890abcdef123456 securely",
        "outcome_status": "pass"
    }
    rec = format_sft_record(raw_call)
    assert rec is not None
    user_msg = rec["messages"][0]["content"]
    asst_msg = rec["messages"][1]["content"]
    assert "sk-" not in user_msg
    assert "[REDACTED]" in user_msg
    assert "sk-" not in asst_msg
    assert "[REDACTED]" in asst_msg
    assert rec["metadata"]["task_id"] == "task_sft_01"


def test_split_dataset():
    records = [{"id": i} for i in range(20)]
    splits = split_dataset(records, val_ratio=0.2, seed=42)
    assert len(splits["train"]) == 16
    assert len(splits["validation"]) == 4

    # Empty records
    empty_splits = split_dataset([])
    assert empty_splits["train"] == []
    assert empty_splits["validation"] == []


def test_compute_dataset_summary():
    records = [
        {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"}
            ],
            "metadata": {"task_type": "chat", "model": "gpt-4"}
        },
        {
            "messages": [
                {"role": "user", "content": "Compute sum"},
                {"role": "assistant", "content": "def sum(a, b): return a + b"}
            ],
            "metadata": {"task_type": "coding", "model": "deepseek"}
        }
    ]
    summary = compute_dataset_summary(records, dataset_type="sft")
    assert summary["total_records"] == 2
    assert summary["task_types"]["chat"] == 1
    assert summary["task_types"]["coding"] == 1
    assert summary["models_represented"]["gpt-4"] == 1
    assert summary["models_represented"]["deepseek"] == 1
    assert summary["estimated_total_tokens"] > 0


@pytest.mark.asyncio
async def test_export_sft_and_dpo_datasets_mocked():
    mock_pool = MagicMock()
    mock_conn = MagicMock()

    sample_calls = [
        {
            "id": "c1",
            "task_id": "task_1",
            "project": "proj-a",
            "task_type": "backend",
            "model": "deepseek",
            "api_style": "openai",
            "request": {"messages": [{"role": "user", "content": "Solve problem A"}]},
            "response_text": "def solve(): return 42",
            "latency_ms": 300,
            "input_tokens": 10,
            "output_tokens": 20,
            "outcome_status": "pass",
            "outcome_kind": "test",
            "ts": "2026-10-11T00:00:00Z"
        },
        {
            "id": "c2",
            "task_id": "task_1",
            "project": "proj-a",
            "task_type": "backend",
            "model": "claude",
            "api_style": "openai",
            "request": {"messages": [{"role": "user", "content": "Solve problem A"}]},
            "response_text": "broken buggy answer",
            "latency_ms": 500,
            "input_tokens": 10,
            "output_tokens": 15,
            "outcome_status": "fail",
            "outcome_kind": "test",
            "ts": "2026-10-11T00:01:00Z"
        }
    ]

    async def mock_fetch(query, *args):
        # If querying for passes vs fails
        statuses = args[0]
        if "pass" in statuses:
            return [sample_calls[0]]
        return [sample_calls[1]]

    mock_conn.fetch = AsyncMock(side_effect=mock_fetch)
    mock_acquire = MagicMock()
    mock_acquire.__aenter__.return_value = mock_conn
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire

    # SFT export
    sft_data = await export_sft_dataset(mock_pool, project="proj-a")
    assert len(sft_data) == 1
    assert sft_data[0]["metadata"]["outcome_status"] == "pass"

    # DPO export (matches pass and fail)
    dpo_data = await export_dpo_dataset(mock_pool, project="proj-a")
    assert len(dpo_data) == 1
    assert dpo_data[0]["chosen"] == "def solve(): return 42"
    assert dpo_data[0]["rejected"] == "broken buggy answer"


@pytest.mark.asyncio
async def test_api_export_dataset_endpoint(async_client, monkeypatch):
    mock_pool = MagicMock()
    monkeypatch.setattr(main, "pool", mock_pool)
    monkeypatch.setenv("OBSERVER_ADMIN_KEY", "test-admin-dataset-key")

    mock_sft = [
        {
            "messages": [
                {"role": "user", "content": "Do task"},
                {"role": "assistant", "content": "Task done"}
            ],
            "metadata": {"task_id": "t1", "task_type": "algo", "model": "m1"}
        }
    ]

    async def mock_export_sft(pool, **kwargs):
        return mock_sft

    monkeypatch.setattr("main.export_sft_dataset", mock_export_sft)

    payload = {
        "dataset_type": "sft",
        "val_split": 0.0,
        "limit": 10
    }
    # Unauthenticated rejected
    resp_unauth = await async_client.post("/admin/export-dataset", json=payload)
    assert resp_unauth.status_code == 401

    # Authenticated accepted
    resp = await async_client.post(
        "/admin/export-dataset",
        json=payload,
        headers={"X-Admin-Token": "test-admin-dataset-key"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["dataset_type"] == "sft"
    assert len(data["train"]) == 1
    assert data["summary"]["total_records"] == 1


@pytest.mark.asyncio
async def test_api_dataset_stats_endpoint(async_client, monkeypatch):
    mock_pool = MagicMock()
    monkeypatch.setattr(main, "pool", mock_pool)
    monkeypatch.setenv("OBSERVER_ADMIN_KEY", "test-admin-dataset-key")

    async def mock_export_sft(pool, **kwargs):
        return [{"messages": [], "metadata": {}}]

    async def mock_export_dpo(pool, **kwargs):
        return []

    monkeypatch.setattr("main.export_sft_dataset", mock_export_sft)
    monkeypatch.setattr("main.export_dpo_dataset", mock_export_dpo)

    # Unauthenticated rejected
    resp_unauth = await async_client.get("/admin/dataset/stats")
    assert resp_unauth.status_code == 401

    # Authenticated accepted
    resp = await async_client.get(
        "/admin/dataset/stats",
        headers={"X-Admin-Token": "test-admin-dataset-key"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "sft" in data
    assert "dpo" in data
