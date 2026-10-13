import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
import main


@pytest.mark.asyncio
async def test_dashboard_and_root_view(async_client):
    resp = await async_client.get("/dashboard")
    assert resp.status_code == 200
    assert "AI Model Observer" in resp.text
    assert "Model Performance Leaderboard" in resp.text

    root_resp = await async_client.get("/")
    assert root_resp.status_code == 200
    assert "AI Model Observer" in root_resp.text


@pytest.mark.asyncio
async def test_dashboard_with_auth(async_client, monkeypatch):
    monkeypatch.setenv("OBSERVER_AUTH_TOKEN", "secure-token")

    # Missing token -> 401
    resp = await async_client.get("/dashboard")
    assert resp.status_code == 401

    # Header auth -> 200
    resp_header = await async_client.get("/dashboard", headers={"X-Observer-Token": "secure-token"})
    assert resp_header.status_code == 200

    # Query param auth -> 200
    resp_query = await async_client.get("/dashboard?token=secure-token")
    assert resp_query.status_code == 200


@pytest.mark.asyncio
async def test_tasks_endpoint_mocked(async_client, monkeypatch):
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_conn.fetch = AsyncMock(return_value=[
        {
            "task_id": "task_1",
            "project": "proj-a",
            "task_type": "coding",
            "title": "Fix bug",
            "created_at": None,
            "call_count": 3,
            "primary_model": "claude-3-opus",
            "latest_outcome": "pass",
            "outcome_kind": "test"
        }
    ])
    mock_acquire = MagicMock()
    mock_acquire.__aenter__.return_value = mock_conn
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire

    monkeypatch.setattr(main, "pool", mock_pool)

    resp = await async_client.get("/tasks")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) == 1
    assert tasks[0]["task_id"] == "task_1"
    assert tasks[0]["primary_model"] == "claude-3-opus"


@pytest.mark.asyncio
async def test_task_details_endpoint(async_client, monkeypatch):
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_conn.fetchrow = AsyncMock(return_value={
        "task_id": "task_1",
        "project": "proj-a",
        "task_type": "coding",
        "title": "Fix bug",
        "created_at": None
    })
    mock_conn.fetch = AsyncMock(side_effect=[
        # call_rows
        [{"id": "c1", "ts": None, "model": "claude", "upstream": "https://api.anthropic.com",
          "api_style": "anthropic", "streamed": False, "status_code": 200, "latency_ms": 150,
          "input_tokens": 10, "output_tokens": 20, "error": None}],
        # outcome_rows
        [{"id": 1, "kind": "test", "status": "pass", "details": '{"passed": 10}', "created_at": None}]
    ])
    mock_acquire = MagicMock()
    mock_acquire.__aenter__.return_value = mock_conn
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire

    monkeypatch.setattr(main, "pool", mock_pool)

    resp = await async_client.get("/tasks/task_1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["task"]["task_id"] == "task_1"
    assert len(data["calls"]) == 1
    assert len(data["outcomes"]) == 1
    assert data["outcomes"][0]["status"] == "pass"


@pytest.mark.asyncio
async def test_admin_prune_endpoint(async_client, monkeypatch):
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_conn.execute = AsyncMock(return_value="DELETE 5")
    mock_acquire = MagicMock()
    mock_acquire.__aenter__.return_value = mock_conn
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire

    monkeypatch.setattr(main, "pool", mock_pool)

    resp = await async_client.post("/admin/prune?days=30")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["outcomes_pruned"] == "DELETE 5"
