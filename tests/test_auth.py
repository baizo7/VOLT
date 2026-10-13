import pytest
import main


@pytest.mark.asyncio
async def test_auth_disabled_by_default(async_client, monkeypatch):
    monkeypatch.delenv("OBSERVER_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("OBSERVER_TOKEN", raising=False)

    # Health is open
    resp = await async_client.get("/health")
    assert resp.status_code in (200, 503)

    # Protected routes do not reject with 401 due to auth
    resp = await async_client.post("/outcomes", json={"task_id": "t1", "kind": "test", "status": "pass"})
    # Not 401 (might be 200 or 503 if DB is uninitialized, but definitely not 401)
    assert resp.status_code != 401


@pytest.mark.asyncio
async def test_auth_protected_routes_reject_missing_token(async_client, monkeypatch):
    monkeypatch.setenv("OBSERVER_AUTH_TOKEN", "secret-token-123")

    # 401 on /v1/chat/completions
    resp = await async_client.post("/v1/chat/completions", json={"model": "gpt-4", "messages": []})
    assert resp.status_code == 401
    assert resp.json() == {"error": "unauthorized"}

    # 401 on /v1/messages
    resp = await async_client.post("/v1/messages", json={"model": "claude-3", "messages": []})
    assert resp.status_code == 401

    # 401 on /outcomes
    resp = await async_client.post("/outcomes", json={"task_id": "t1", "kind": "test", "status": "pass"})
    assert resp.status_code == 401

    # 401 on /stats
    resp = await async_client.get("/stats")
    assert resp.status_code == 401

    # /health is always unauthenticated
    resp = await async_client.get("/health")
    assert resp.status_code != 401


@pytest.mark.asyncio
async def test_auth_accepted_with_bearer_token(async_client, monkeypatch):
    monkeypatch.setenv("OBSERVER_AUTH_TOKEN", "secret-token-123")

    headers = {"Authorization": "Bearer secret-token-123"}
    resp = await async_client.post(
        "/outcomes",
        json={"task_id": "t1", "kind": "test", "status": "pass"},
        headers=headers
    )
    # Token accepted; not 401
    assert resp.status_code != 401


@pytest.mark.asyncio
async def test_auth_accepted_with_observer_header(async_client, monkeypatch):
    monkeypatch.setenv("OBSERVER_AUTH_TOKEN", "secret-token-123")

    headers = {"X-Observer-Token": "secret-token-123"}
    resp = await async_client.post(
        "/outcomes",
        json={"task_id": "t1", "kind": "test", "status": "pass"},
        headers=headers
    )
    assert resp.status_code != 401


@pytest.mark.asyncio
async def test_auth_rejected_with_invalid_token(async_client, monkeypatch):
    monkeypatch.setenv("OBSERVER_AUTH_TOKEN", "secret-token-123")

    headers = {"Authorization": "Bearer wrong-token"}
    resp = await async_client.post(
        "/outcomes",
        json={"task_id": "t1", "kind": "test", "status": "pass"},
        headers=headers
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_auth_strictly_enforced_when_token_unset_and_require_auth_true(async_client, monkeypatch):
    monkeypatch.delenv("OBSERVER_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("OBSERVER_TOKEN", raising=False)
    monkeypatch.setenv("REQUIRE_AUTH", "true")

    resp = await async_client.post(
        "/outcomes",
        json={"task_id": "t1", "kind": "test", "status": "pass"}
    )
    assert resp.status_code == 401
    assert resp.json() == {"error": "unauthorized"}


@pytest.mark.asyncio
async def test_auth_accepted_with_x_api_key_and_query_param(async_client, monkeypatch):
    monkeypatch.setenv("OBSERVER_AUTH_TOKEN", "secret-token-123")

    # X-API-Key
    headers = {"X-API-Key": "secret-token-123"}
    resp = await async_client.post(
        "/outcomes",
        json={"task_id": "t1", "kind": "test", "status": "pass"},
        headers=headers
    )
    assert resp.status_code != 401

    # Query param token
    resp2 = await async_client.get("/stats?token=secret-token-123")
    assert resp2.status_code != 401
