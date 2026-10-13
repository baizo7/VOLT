import os
import uuid
import json
import pytest
import asyncpg
from httpx import AsyncClient, ASGITransport
import main

# Test database URL from environment or default
DB_URL = os.environ.get("DATABASE_URL", "postgresql://observer:observer_secret_pw_123@127.0.0.1:5432/observer")


@pytest.fixture
async def db_pool():
    try:
        pool = await asyncpg.create_pool(DB_URL, min_size=1, max_size=3)
    except Exception as e:
        pytest.skip(f"PostgreSQL not reachable at {DB_URL}: {e}")
    # Initialize main.pool
    old_pool = main.pool
    main.pool = pool
    yield pool
    await pool.close()
    main.pool = old_pool


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_schema_and_health(db_pool, async_client):
    # Verify tables created by schema.sql
    async with db_pool.acquire() as conn:
        tables = await conn.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        )
        table_names = {r["table_name"] for r in tables}
        assert "tasks" in table_names
        assert "llm_calls" in table_names
        assert "outcomes" in table_names

    # Verify /health returns 200 ready
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "status": "ready"}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_log_call_and_scrubbing(db_pool):
    call_id = str(uuid.uuid4())
    task_id = f"task-int-{uuid.uuid4().hex[:8]}"

    raw_record = {
        "id": call_id,
        "project": "test-project",
        "task_id": task_id,
        "session_id": "sess-1",
        "task_type": "debugging",
        "model": "deepseek-chat",
        "upstream": "https://api.deepseek.com/v1",
        "style": "openai",
        "streamed": False,
        "request": {"messages": [{"role": "user", "content": "key is sk-1234567890abcdef123456"}]},
        "response_text": "Found secret AIzaSyD-1234567890abcdefghijklmnopqrstuv in code.",
        "tool_calls": [],
        "status_code": 200,
        "latency_ms": 320,
        "in": 15,
        "out": 10,
        "error": "Leaked error token: ghp_12345678901234567890123456789012"
    }

    await main.log_call(raw_record)

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM llm_calls WHERE id = $1", uuid.UUID(call_id))
        assert row is not None
        assert row["task_id"] == task_id
        assert row["model"] == "deepseek-chat"
        # Verify scrubbing in database
        req_json = json.loads(row["request"]) if isinstance(row["request"], str) else row["request"]
        assert "[REDACTED]" in req_json["messages"][0]["content"]
        assert "sk-" not in req_json["messages"][0]["content"]
        assert "[REDACTED]" in row["response_text"]
        assert "AIza" not in row["response_text"]
        assert "[REDACTED]" in row["error"]
        assert "ghp_" not in row["error"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_outcomes_and_multi_model_stats(db_pool, async_client):
    task_id = f"task-multi-{uuid.uuid4().hex[:8]}"

    # Step 1: Insert call with Model A (earlier)
    call_1 = {
        "id": str(uuid.uuid4()),
        "project": "proj-multi",
        "task_id": task_id,
        "session_id": "s1",
        "task_type": "coding",
        "model": "model-early-test",
        "upstream": "http://upstream",
        "style": "openai",
        "streamed": False,
        "request": {},
        "response_text": "Draft",
        "tool_calls": [],
        "status_code": 200,
        "latency_ms": 100,
        "in": 10,
        "out": 10,
        "error": None
    }
    await main.log_call(call_1)

    # Step 2: Insert call with Model B (later, final touch)
    call_2 = {
        "id": str(uuid.uuid4()),
        "project": "proj-multi",
        "task_id": task_id,
        "session_id": "s1",
        "task_type": "coding",
        "model": "model-final-test",
        "upstream": "http://upstream",
        "style": "openai",
        "streamed": False,
        "request": {},
        "response_text": "Final code",
        "tool_calls": [],
        "status_code": 200,
        "latency_ms": 150,
        "in": 20,
        "out": 20,
        "error": None
    }
    await main.log_call(call_2)

    # Step 3: Post an outcome for task_id
    outcome_resp = await async_client.post(
        "/outcomes",
        json={"task_id": task_id, "kind": "test", "status": "pass", "details": {"passed": 10}}
    )
    assert outcome_resp.status_code == 200
    assert outcome_resp.json() == {"ok": True}

    # Step 4: Verify /stats attribution
    stats_resp = await async_client.get("/stats")
    assert stats_resp.status_code == 200
    stats_list = stats_resp.json()

    stats_by_model = {item["model"]: item for item in stats_list}

    assert "model-final-test" in stats_by_model
    assert "model-early-test" in stats_by_model

    # model-final-test should receive the pass
    assert stats_by_model["model-final-test"]["passes"] >= 1

    # model-early-test should NOT be credited with the outcome (no double-counting)
    assert stats_by_model["model-early-test"]["passes"] == 0
