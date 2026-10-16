import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
import main


@pytest.mark.asyncio
async def test_dashboard_and_root_view(async_client):
    resp = await async_client.get("/dashboard")
    assert resp.status_code == 200
    assert "VOLT-AI" in resp.text
    assert "Model Performance Leaderboard" in resp.text

    root_resp = await async_client.get("/")
    assert root_resp.status_code == 200
    assert "VOLT-AI" in root_resp.text


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
    monkeypatch.setenv("OBSERVER_ADMIN_KEY", "admin-prune-secret")

    # Unauthorized -> 401
    resp_unauth = await async_client.post("/admin/prune?days=30")
    assert resp_unauth.status_code == 401

    # Authorized -> 200
    resp = await async_client.post("/admin/prune?days=30", headers={"X-Admin-Token": "admin-prune-secret"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["outcomes_pruned"] == "DELETE 5"


@pytest.mark.asyncio
async def test_dashboard_phase6_html_elements(async_client):
    resp = await async_client.get("/dashboard")
    assert resp.status_code == 200
    assert "live-badge" in resp.text
    assert "loop-alert-banner" in resp.text
    assert "banner-quota-bar" in resp.text
    assert "Specialist Model Retraining Center" in resp.text


@pytest.mark.asyncio
async def test_quotas_endpoint_rbac_and_loop_detection(async_client, monkeypatch):
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    # Mock token row
    mock_conn.fetchrow = AsyncMock(return_value={"tokens_today": 25000, "calls_today": 12})
    # Mock loop detection rows (e.g. high repetition task)
    mock_conn.fetch = AsyncMock(return_value=[
        {
            "task_id": "stuck_task_42",
            "call_count": 9,
            "session_id": "alice",
            "model": "qwen2.5-coder",
            "has_fail": True,
        }
    ])
    mock_acquire = MagicMock()
    mock_acquire.__aenter__.return_value = mock_conn
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire

    monkeypatch.setattr(main, "pool", mock_pool)
    monkeypatch.setenv("OBSERVER_ADMIN_KEY", "super-secret-admin")

    # Developer alice querying her own quotas
    resp_alice = await async_client.get("/stats/quotas?session_id=alice", headers={"X-Session-Id": "alice"})
    assert resp_alice.status_code == 200
    d_alice = resp_alice.json()
    assert d_alice["ok"] is True
    assert d_alice["tokens_today"] == 25000
    assert d_alice["loop_detected"] is True
    assert len(d_alice["active_alerts"]) == 1
    assert d_alice["active_alerts"][0]["task_id"] == "stuck_task_42"

    # Anti-spoofing: developer alice trying to query bob's quota -> 403 Forbidden
    resp_spoof = await async_client.get("/stats/quotas?session_id=bob", headers={"X-Session-Id": "alice"})
    assert resp_spoof.status_code == 403

    # Admin querying global / user quota
    resp_admin = await async_client.get("/stats/quotas?session_id=bob", headers={"X-Admin-Token": "super-secret-admin"})
    assert resp_admin.status_code == 200


@pytest.mark.asyncio
async def test_admin_retrain_pipeline(async_client, monkeypatch):
    monkeypatch.setenv("OBSERVER_ADMIN_KEY", "admin-key-123")

    # 1. Unauthorized attempt
    resp_unauth = await async_client.post("/admin/retrain/trigger", json={"model": "Qwen/Qwen2.5-Coder-1.5B"})
    assert resp_unauth.status_code == 401

    # 2. Authorized trigger
    resp_trigger = await async_client.post(
        "/admin/retrain/trigger",
        headers={"X-Admin-Token": "admin-key-123"},
        json={
            "model": "Qwen/Qwen2.5-Coder-1.5B",
            "specialist": "Fast Coder (Qwen2.5-Coder-1.5B)",
            "dataset_type": "sft",
            "rank": 16,
            "alpha": 32,
            "epochs": 1
        }
    )
    assert resp_trigger.status_code == 200
    data = resp_trigger.json()
    assert data["ok"] is True
    job_id = data["job_id"]
    assert job_id.startswith("job-")

    # 3. Check status
    resp_status = await async_client.get(
        f"/admin/retrain/status/{job_id}",
        headers={"X-Admin-Token": "admin-key-123"}
    )
    assert resp_status.status_code == 200
    job_data = resp_status.json()
    assert job_data["job_id"] == job_id
    assert job_data["model"] == "Qwen/Qwen2.5-Coder-1.5B"

    # 4. List jobs
    resp_jobs = await async_client.get(
        "/admin/retrain/jobs",
        headers={"X-Admin-Token": "admin-key-123"}
    )
    assert resp_jobs.status_code == 200
    jobs_list = resp_jobs.json()["jobs"]
    assert any(j["job_id"] == job_id for j in jobs_list)


@pytest.mark.asyncio
async def test_live_stream_manager():
    mgr = main.LiveStreamManager()
    ws_mock = AsyncMock()

    await mgr.connect(ws_mock, role="developer", session_id="dev1")
    assert ws_mock in mgr.active_connections

    # Broadcast matching session
    await mgr.broadcast("call", {"id": "c1", "session_id": "dev1", "model": "flash"})
    ws_mock.send_text.assert_called()

    # Broadcast different session - developer dev1 should NOT receive it (isolation)
    ws_mock.send_text.reset_mock()
    await mgr.broadcast("call", {"id": "c2", "session_id": "other_dev", "model": "flash"})
    ws_mock.send_text.assert_not_called()

    await mgr.disconnect(ws_mock)
    assert ws_mock not in mgr.active_connections

