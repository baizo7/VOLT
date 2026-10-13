import pytest


@pytest.mark.asyncio
async def test_proxy_rejects_non_object_json_bodies(async_client):
    # Array body
    resp = await async_client.post("/v1/chat/completions", content="[1, 2, 3]", headers={"Content-Type": "application/json"})
    assert resp.status_code == 400
    assert "JSON object" in resp.json().get("error", "")

    # String scalar body
    resp = await async_client.post("/v1/chat/completions", content='"just a string"', headers={"Content-Type": "application/json"})
    assert resp.status_code == 400
    assert "JSON object" in resp.json().get("error", "")

    # Number scalar body
    resp = await async_client.post("/v1/messages", content="42", headers={"Content-Type": "application/json"})
    assert resp.status_code == 400
    assert "JSON object" in resp.json().get("error", "")

    # Invalid JSON
    resp = await async_client.post("/v1/chat/completions", content="{malformed json", headers={"Content-Type": "application/json"})
    assert resp.status_code == 400
    assert resp.json() == {"error": "invalid JSON"}


@pytest.mark.asyncio
async def test_outcomes_pydantic_validation(async_client):
    # Missing task_id -> 422
    resp = await async_client.post("/outcomes", json={"kind": "test", "status": "pass"})
    assert resp.status_code == 422

    # Missing kind -> 422
    resp = await async_client.post("/outcomes", json={"task_id": "task-1", "status": "pass"})
    assert resp.status_code == 422

    # Missing status -> 422
    resp = await async_client.post("/outcomes", json={"task_id": "task-1", "kind": "test"})
    assert resp.status_code == 422
