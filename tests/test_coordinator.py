"""
Unit tests for ObserverCoder-1.0 Multi-Model Coordinator Engine.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import main
from app.coordinator import analyze_intent, call_specialist, SPECIALIST_CATALOG


def test_analyze_intent_fast_coding():
    messages = [{"role": "user", "content": "Write a python function to add two numbers."}]
    decision = analyze_intent(messages)
    assert decision["track"] == "fast_coding"
    assert "fast_coder" in decision["specialists"]


def test_analyze_intent_deep_reasoning():
    messages = [{
        "role": "user",
        "content": "What is the best system design and architecture to handle high throughput distributed transactions without race conditions?"
    }]
    decision = analyze_intent(messages)
    assert decision["track"] == "two_pass_reasoning"
    assert "deep_reasoner" in decision["specialists"]
    assert "heavy_coder" in decision["specialists"]


def test_analyze_intent_math():
    messages = [{
        "role": "user",
        "content": "Solve this equation and calculate the eigenvalue matrix probability distribution."
    }]
    decision = analyze_intent(messages)
    assert decision["track"] == "two_pass_reasoning"
    assert "math_specialist" in decision["specialists"]


def test_analyze_intent_vision():
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Inspect this UI mockup and generate Tailwind HTML."},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBORw0KGgo..."}}
        ]
    }]
    decision = analyze_intent(messages)
    assert decision["track"] == "vision"
    assert "vision_specialist" in decision["specialists"]


@pytest.mark.asyncio
async def test_call_specialist_mocked():
    mock_client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "def test(): pass"}}],
        "usage": {"prompt_tokens": 15, "completion_tokens": 8}
    }
    mock_client.post.return_value = mock_resp

    text, in_tok, out_tok = await call_specialist(
        client=mock_client,
        specialist_key="fast_coder",
        messages=[{"role": "user", "content": "test"}]
    )
    assert text == "def test(): pass"
    assert in_tok == 15
    assert out_tok == 8


@pytest.mark.asyncio
async def test_observer_coder_endpoint_non_streaming(async_client, monkeypatch):
    mock_client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "print('hello from ObserverCoder-1.0')"}}],
        "usage": {"prompt_tokens": 20, "completion_tokens": 10}
    }
    mock_client.post.return_value = mock_resp
    monkeypatch.setattr(main, "client", mock_client)

    payload = {
        "model": "observer-coder-1.0",
        "messages": [{"role": "user", "content": "Write hello world in python"}],
        "stream": False
    }

    resp = await async_client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["model"] == "observer-coder-1.0"
    assert len(data["choices"]) == 1
    assert "hello from ObserverCoder-1.0" in data["choices"][0]["message"]["content"]
    assert "observer_coordination" in data
    assert data["observer_coordination"]["track"] == "fast_coding"
    assert "fast_coder" in data["observer_coordination"]["specialists_used"]
    assert resp.headers.get("x-observer-model") == "observer-coder-1.0"


@pytest.mark.asyncio
async def test_observer_coder_two_pass_reasoning(async_client, monkeypatch):
    mock_client = AsyncMock()
    # First response: Reasoner plan; Second response: Coder synthesis
    plan_resp = MagicMock()
    plan_resp.status_code = 200
    plan_resp.json.return_value = {
        "choices": [{"message": {"content": "1. Use connection pool. 2. Use semaphore."}}],
        "usage": {"prompt_tokens": 25, "completion_tokens": 15}
    }

    code_resp = MagicMock()
    code_resp.status_code = 200
    code_resp.json.return_value = {
        "choices": [{"message": {"content": "class ConnectionPool: pass"}}],
        "usage": {"prompt_tokens": 40, "completion_tokens": 30}
    }

    mock_client.post.side_effect = [plan_resp, code_resp]
    monkeypatch.setattr(main, "client", mock_client)

    payload = {
        "model": "observer-coder-1.0",
        "messages": [{
            "role": "user",
            "content": "Design and architect a resilient connection pool algorithm to avoid race condition and deadlock."
        }],
        "stream": False
    }

    resp = await async_client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["model"] == "observer-coder-1.0"
    assert "ConnectionPool" in data["choices"][0]["message"]["content"]
    assert data["observer_coordination"]["track"] == "two_pass_reasoning"
    assert data["observer_coordination"]["has_reasoning_pass"] is True
    assert "deep_reasoner" in data["observer_coordination"]["specialists_used"]


@pytest.mark.asyncio
async def test_observer_coder_endpoint_streaming(async_client, monkeypatch):
    mock_client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "def add(a, b): return a + b"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 8}
    }
    mock_client.post.return_value = mock_resp
    monkeypatch.setattr(main, "client", mock_client)

    payload = {
        "model": "observer-coder-1.0",
        "messages": [{"role": "user", "content": "Write add function"}],
        "stream": True
    }

    resp = await async_client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")

    lines = resp.text.strip().split("\n\n")
    assert any("[DONE]" in line for line in lines)
    # Check that tokens were yielded
    parsed_deltas = []
    for line in lines:
        if line.startswith("data: ") and "[DONE]" not in line:
            chunk = json.loads(line[6:])
            delta = chunk["choices"][0]["delta"]
            if "content" in delta:
                parsed_deltas.append(delta["content"])

    full_reconstructed = "".join(parsed_deltas)
    assert "def add(a, b)" in full_reconstructed


@pytest.mark.asyncio
async def test_v1_models_endpoint_lists_observer_coder(async_client):
    resp = await async_client.get("/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    model_ids = [m["id"] for m in data["data"]]
    assert "observer-coder-1.0" in model_ids
