import json
import pytest
import httpx
import main


@pytest.mark.asyncio
async def test_proxy_forwarding_and_credential_passthrough(async_client, monkeypatch):
    # Upstream mock to capture request sent by proxy
    captured_request = {}

    def mock_handler(request: httpx.Request):
        captured_request["url"] = str(request.url)
        captured_request["headers"] = dict(request.headers)
        captured_request["body"] = request.read().decode("utf-8")
        resp_data = {
            "choices": [{"message": {"role": "assistant", "content": "Hello from mock upstream"}}]
        }
        return httpx.Response(200, json=resp_data)

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    monkeypatch.setattr(main, "client", mock_client)

    # Call /v1/chat/completions with custom client authorization header and claude model (no api_key_env)
    payload = {"model": "claude-3-opus", "messages": [{"role": "user", "content": "hi"}]}
    headers = {
        "Authorization": "Bearer client-secret-token",
        "X-Task-Id": "task-test-1",
        "X-Project": "my-project"
    }

    resp = await async_client.post("/v1/chat/completions", json=payload, headers=headers)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["choices"][0]["message"]["content"] == "Hello from mock upstream"

    # Upstream should receive the forwarded body and client auth header
    assert json.loads(captured_request["body"]) == payload
    assert captured_request["headers"]["authorization"] == "Bearer client-secret-token"


@pytest.mark.asyncio
async def test_proxy_credential_replacement(async_client, monkeypatch):
    captured_request = {}

    def mock_handler(request: httpx.Request):
        captured_request["headers"] = dict(request.headers)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    monkeypatch.setattr(main, "client", mock_client)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-proxy-managed-key")

    payload = {"model": "deepseek-chat", "messages": []}
    headers = {"Authorization": "Bearer user-original-key"}

    resp = await async_client.post("/v1/chat/completions", json=payload, headers=headers)
    assert resp.status_code == 200

    # Proxy-held key replaces user's authorization header
    assert captured_request["headers"]["authorization"] == "Bearer deepseek-proxy-managed-key"


@pytest.mark.asyncio
async def test_proxy_upstream_httperror_returns_502(async_client, monkeypatch):
    def mock_handler(request: httpx.Request):
        raise httpx.ConnectError("Failed to connect to upstream", request=request)

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    monkeypatch.setattr(main, "client", mock_client)

    logged_records = []

    async def mock_log_call(rec):
        logged_records.append(rec)

    monkeypatch.setattr(main, "log_call", mock_log_call)

    payload = {"model": "gpt-4", "messages": []}
    resp = await async_client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 502
    assert "upstream error" in resp.json().get("error", "")

    # Error was logged
    assert len(logged_records) == 1
    assert logged_records[0]["status_code"] == 502
    assert "Failed to connect" in logged_records[0]["error"]


@pytest.mark.asyncio
async def test_proxy_db_failure_does_not_break_response(async_client, monkeypatch):
    def mock_handler(request: httpx.Request):
        return httpx.Response(200, json={"choices": [{"message": {"content": "success despite db down"}}]})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    monkeypatch.setattr(main, "client", mock_client)

    # Force log_call to fail / raise an exception
    async def broken_log_call(rec):
        raise RuntimeError("Database completely crashed!")

    monkeypatch.setattr(main, "log_call", broken_log_call)

    payload = {"model": "gpt-4", "messages": []}
    resp = await async_client.post("/v1/chat/completions", json=payload)
    # The client response must still succeed
    assert resp.status_code == 200
    assert resp.json()["choices"][0]["message"]["content"] == "success despite db down"


@pytest.mark.asyncio
async def test_proxy_strips_observer_auth_tokens_before_upstream(async_client, monkeypatch):
    captured_request = {}

    def mock_handler(request: httpx.Request):
        captured_request["headers"] = dict(request.headers)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    monkeypatch.setattr(main, "client", mock_client)

    payload = {"model": "claude-3-opus", "messages": [{"role": "user", "content": "hi"}]}
    headers = {
        "Authorization": "Bearer client-provider-token",
        "X-Observer-Token": "observer-secret-admin-key",
        "X-Inject-Knowledge": "true",
        "X-Task-Id": "task-security-check",
    }

    resp = await async_client.post("/v1/chat/completions", json=payload, headers=headers)
    assert resp.status_code == 200

    # Ensure observer internal tokens are NEVER leaked upstream
    upstream_headers = captured_request["headers"]
    assert "x-observer-token" not in upstream_headers
    assert "x-inject-knowledge" not in upstream_headers
    assert upstream_headers.get("authorization") == "Bearer client-provider-token"


@pytest.mark.asyncio
async def test_proxy_payload_too_large_413(async_client, monkeypatch):
    monkeypatch.setattr(main, "MAX_REQUEST_BYTES", 100)

    big_payload = {"model": "gpt-4", "messages": [{"role": "user", "content": "a" * 200}]}
    resp = await async_client.post("/v1/chat/completions", json=big_payload)
    assert resp.status_code == 413
    assert "Payload Too Large" in resp.json()["error"]


@pytest.mark.asyncio
async def test_get_v1_models(async_client):
    resp = await async_client.get("/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "list"
    assert len(data["data"]) >= 1
    model_ids = [m["id"] for m in data["data"]]
    assert "claude" in model_ids or "deepseek" in model_ids

    # Also test project-scoped models route
    resp_proj = await async_client.get("/p/proj-alpha/v1/models")
    assert resp_proj.status_code == 200
    assert resp_proj.json()["object"] == "list"


@pytest.mark.asyncio
async def test_proxy_local_adapter_failover_to_upstream(async_client, monkeypatch):
    captured_urls = []

    def mock_handler(request: httpx.Request):
        url = str(request.url)
        captured_urls.append(url)
        if "127.0.0.1:8080" in url:
            # Simulate local inference server is offline / connection refused
            raise httpx.ConnectError("Connection refused by local server", request=request)
        # Upstream fallback succeeds
        return httpx.Response(200, json={"choices": [{"message": {"content": "upstream failover success"}}]})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    monkeypatch.setattr(main, "client", mock_client)

    payload = {
        "model": "local/qwen2.5-coder-1.5b-adapter",
        "messages": [{"role": "user", "content": "Write quicksort"}]
    }

    resp = await async_client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 200
    assert resp.json()["choices"][0]["message"]["content"] == "upstream failover success"
    # Verify first call tried local, then failed over to upstream
    assert len(captured_urls) == 2
    assert "127.0.0.1:8080" in captured_urls[0]
    assert "openrouter.ai" in captured_urls[1]
