"""
Unit tests for ObserverCoder-1.0 Multi-Model Coordinator Engine.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import main
from app.coordinator import analyze_intent, call_specialist, SPECIALIST_CATALOG, SpecialistExecutionError


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

    resp = await async_client.post(
        "/v1/chat/completions",
        json=payload,
        headers={"Authorization": "Bearer sk-or-v1-test-developer-key"}
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["model"] == "observer-coder-1.0"
    assert len(data["choices"]) == 1
    assert "hello from ObserverCoder-1.0" in data["choices"][0]["message"]["content"]
    assert "observer_coordination" in data
    assert data["observer_coordination"]["track"] == "fast_coding"
    assert "fast_coder" in data["observer_coordination"]["specialists_used"]
    assert resp.headers.get("x-observer-model") == "observer-coder-1.0"
    assert resp.headers.get("x-volt-byok") == "active"
    assert resp.headers.get("x-volt-data-collection") == "active"


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

    resp = await async_client.post(
        "/v1/chat/completions",
        json=payload,
        headers={"Authorization": "Bearer sk-or-v1-test-developer-key"}
    )
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

    resp = await async_client.post(
        "/v1/chat/completions",
        json=payload,
        headers={"Authorization": "Bearer sk-or-v1-test-developer-key"}
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")
    assert resp.headers.get("x-volt-byok") == "active"
    assert resp.headers.get("x-volt-data-collection") == "active"

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


@pytest.mark.asyncio
async def test_call_specialist_primary_fails_fallback_succeeds():
    mock_client = AsyncMock()

    fail_resp = MagicMock()
    fail_resp.status_code = 500
    fail_resp.text = "Internal Server Error"

    success_resp = MagicMock()
    success_resp.status_code = 200
    success_resp.json.return_value = {
        "choices": [{"message": {"content": "def fallback_solution(): return True"}}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 6}
    }

    mock_client.post.side_effect = [fail_resp, success_resp]

    text, in_tok, out_tok = await call_specialist(
        client=mock_client,
        specialist_key="fast_coder",
        messages=[{"role": "user", "content": "test"}]
    )
    assert text == "def fallback_solution(): return True"
    assert in_tok == 12
    assert out_tok == 6
    assert mock_client.post.call_count == 2


@pytest.mark.asyncio
async def test_call_specialist_all_fail_raises_exception():
    mock_client = AsyncMock()

    fail_resp = MagicMock()
    fail_resp.status_code = 401
    fail_resp.text = '{"error": "Unauthorized"}'

    mock_client.post.return_value = fail_resp

    with pytest.raises(SpecialistExecutionError) as exc_info:
        await call_specialist(
            client=mock_client,
            specialist_key="fast_coder",
            messages=[{"role": "user", "content": "test"}]
        )
    assert "All specialist candidates failed for fast_coder" in str(exc_info.value)
    assert exc_info.value.specialist_key == "fast_coder"


@pytest.mark.asyncio
async def test_call_specialist_forwards_client_auth():
    mock_client = AsyncMock()

    # First call (local) fails with connection error, second call (cloud fallback) succeeds
    success_resp = MagicMock()
    success_resp.status_code = 200
    success_resp.json.return_value = {
        "choices": [{"message": {"content": "client auth response"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5}
    }
    mock_client.post.side_effect = [httpx.ConnectError("Connection refused"), success_resp]

    routes_map = {
        "local/": {"base_url": "http://127.0.0.1:8080/v1", "api_key_env": None},
        "*": {"base_url": "https://openrouter.ai/api/v1", "api_key_env": "MISSING_ENV_KEY"}
    }

    text, in_tok, out_tok = await call_specialist(
        client=mock_client,
        specialist_key="fast_coder",
        messages=[{"role": "user", "content": "test"}],
        routes_map=routes_map,
        client_auth_header="Bearer sk-or-custom-client-key"
    )
    assert text == "client auth response"
    assert mock_client.post.call_count == 2
    # Verify the fallback call to OpenRouter received the client BYOK header
    second_call_headers = mock_client.post.call_args_list[1].kwargs.get("headers", {})
    assert second_call_headers.get("Authorization") == "Bearer sk-or-custom-client-key"


@pytest.mark.asyncio
async def test_observer_coder_endpoint_failure_returns_502(async_client, monkeypatch):
    mock_client = AsyncMock()
    fail_resp = MagicMock()
    fail_resp.status_code = 502
    fail_resp.text = "Bad Gateway"
    mock_client.post.return_value = fail_resp
    monkeypatch.setattr(main, "client", mock_client)

    payload = {
        "model": "observer-coder-1.0",
        "messages": [{"role": "user", "content": "Write quicksort in python"}],
        "stream": False
    }

    resp = await async_client.post(
        "/v1/chat/completions",
        json=payload,
        headers={"Authorization": "Bearer sk-or-v1-test-developer-key"}
    )
    assert resp.status_code == 502
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == 502
    assert "ObserverCoder specialist execution failed" in data["error"]["message"]
    # Ensure placeholder comment is NEVER returned on failure
    assert "choices" not in data


@pytest.mark.asyncio
async def test_call_specialist_malformed_json_triggers_fallback():
    mock_client = AsyncMock()

    # First call returns 200 with invalid JSON
    bad_json_resp = MagicMock()
    bad_json_resp.status_code = 200
    bad_json_resp.json.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)

    # Second call returns 200 with valid completion
    valid_resp = MagicMock()
    valid_resp.status_code = 200
    valid_resp.json.return_value = {
        "choices": [{"message": {"content": "recovered from bad json"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5}
    }

    mock_client.post.side_effect = [bad_json_resp, valid_resp]

    text, in_tok, out_tok = await call_specialist(
        client=mock_client,
        specialist_key="fast_coder",
        messages=[{"role": "user", "content": "test"}]
    )
    assert text == "recovered from bad json"
    assert mock_client.post.call_count == 2


@pytest.mark.asyncio
async def test_volt_ai_endpoint_non_streaming(async_client, monkeypatch):
    mock_client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "print('hello from VOLT-AI')"}}],
        "usage": {"prompt_tokens": 18, "completion_tokens": 9}
    }
    mock_client.post.return_value = mock_resp
    monkeypatch.setattr(main, "client", mock_client)

    payload = {
        "model": "VOLT-AI",
        "messages": [{"role": "user", "content": "Write quicksort in python"}],
        "stream": False
    }

    resp = await async_client.post(
        "/v1/chat/completions",
        json=payload,
        headers={"Authorization": "Bearer sk-or-v1-test-developer-key"}
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["model"] == "VOLT-AI"
    assert "hello from VOLT-AI" in data["choices"][0]["message"]["content"]
    assert "volt_coordination" in data
    assert data["volt_coordination"]["track"] == "fast_coding"
    assert resp.headers.get("x-volt-model") == "VOLT-AI"
    assert resp.headers.get("x-observer-model") == "VOLT-AI"
    assert resp.headers.get("x-volt-byok") == "active"
    assert resp.headers.get("x-volt-data-collection") == "active"


@pytest.mark.asyncio
async def test_volt_ai_models_listing(async_client):
    resp = await async_client.get("/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    model_ids = [m["id"] for m in data["data"]]
    assert "VOLT-AI" in model_ids
    assert "volt-ai-1.0" in model_ids
    assert "observer-coder-1.0" in model_ids


@pytest.mark.asyncio
async def test_volt_ai_requires_byok_api_key(async_client):
    """Ensure requests to VOLT-AI without a user API key return 401 Unauthorized with BYOK requirement."""
    payload = {
        "model": "VOLT-AI",
        "messages": [{"role": "user", "content": "Write quicksort"}],
        "stream": False
    }
    # No Authorization header
    resp = await async_client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 401
    data = resp.json()
    assert "error" in data
    assert "Bring-Your-Own-Key" in data["error"]["message"]
    assert resp.headers.get("x-volt-byok") == "required"


@pytest.mark.asyncio
async def test_volt_ai_byok_dummy_keys_rejected(async_client):
    """Ensure dummy placeholder keys ('volt-cloud', 'none', short keys) are rejected."""
    payload = {
        "model": "VOLT-AI",
        "messages": [{"role": "user", "content": "Write quicksort"}],
        "stream": False
    }
    for dummy in ["volt-cloud", "none", "null", "abc"]:
        resp = await async_client.post(
            "/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {dummy}"}
        )
        assert resp.status_code == 401
        assert resp.headers.get("x-volt-byok") == "required"

