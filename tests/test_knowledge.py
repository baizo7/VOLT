import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.knowledge import (
    vector_to_string,
    validate_embedding_vector,
    index_solution,
    search_solutions_by_embedding,
    search_solutions_by_text,
)
import main


def test_vector_to_string():
    vec = [0.1, 0.25, -0.5]
    res = vector_to_string(vec)
    assert res == "[0.1,0.25,-0.5]"


def test_validate_embedding_vector_dimensions_and_values():
    # Valid vector
    valid_vec = [0.0] * 1536
    validate_embedding_vector(valid_vec)  # should not raise

    # Dimension mismatch
    with pytest.raises(ValueError, match="does not match expected dimension"):
        validate_embedding_vector([0.1, 0.2], expected_dim=1536)

    # Non-list input
    with pytest.raises(ValueError, match="must be a list of floats"):
        validate_embedding_vector("not-a-list")

    # Non-finite / NaN values
    with pytest.raises(ValueError, match="non-finite"):
        validate_embedding_vector([float("nan")] * 1536)

    with pytest.raises(ValueError, match="non-finite"):
        validate_embedding_vector([float("inf")] * 1536)


@pytest.mark.asyncio
async def test_api_add_solution_endpoint(async_client, monkeypatch):
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_conn.fetchval = AsyncMock(return_value=None)
    mock_conn.fetchrow = AsyncMock(return_value={"id": 42})
    mock_acquire = MagicMock()
    mock_acquire.__aenter__.return_value = mock_conn
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire

    monkeypatch.setattr(main, "pool", mock_pool)

    payload = {
        "task_id": "task_know_01",
        "problem_summary": "Fix broken SSE parsing for OpenAI streaming",
        "solution_code": "def parse_sse(): pass",
        "outcome_status": "pass",
        "task_type": "debugging"
    }

    resp = await async_client.post("/knowledge/solutions", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["solution_id"] == 42


@pytest.mark.asyncio
async def test_api_search_knowledge_by_text(async_client, monkeypatch):
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_conn.fetch = AsyncMock(return_value=[
        {
            "id": 1,
            "task_id": "task_know_01",
            "task_type": "debugging",
            "project": "proj-x",
            "problem_summary": "Fix broken SSE",
            "solution_code": "def fix(): pass",
            "outcome_status": "pass",
            "similarity": 1.0
        }
    ])
    mock_acquire = MagicMock()
    mock_acquire.__aenter__.return_value = mock_conn
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire

    monkeypatch.setattr(main, "pool", mock_pool)

    payload = {
        "query_text": "broken SSE",
        "limit": 3
    }

    resp = await async_client.post("/knowledge/search", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["task_id"] == "task_know_01"


@pytest.mark.asyncio
async def test_api_search_knowledge_validation(async_client, monkeypatch):
    mock_pool = MagicMock()
    monkeypatch.setattr(main, "pool", mock_pool)

    # Empty payload with neither text nor embedding -> 400
    resp = await async_client.post("/knowledge/search", json={})
    assert resp.status_code == 400
    assert "Must provide" in resp.json()["error"]


@pytest.mark.asyncio
async def test_api_add_solution_invalid_vector_returns_400(async_client, monkeypatch):
    mock_pool = MagicMock()
    monkeypatch.setattr(main, "pool", mock_pool)

    # Invalid dimension (e.g. 5 floats instead of 1536)
    payload = {
        "task_id": "task_bad_vec",
        "problem_summary": "Test bad dim",
        "solution_code": "pass",
        "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
    }
    resp = await async_client.post("/knowledge/solutions", json=payload)
    assert resp.status_code == 400
    assert "Embedding dimension" in resp.json()["error"]


@pytest.mark.asyncio
async def test_api_search_knowledge_with_project_filter(async_client, monkeypatch):
    mock_pool = MagicMock()
    captured_kwargs = {}

    async def mock_search_by_text(pool, query_text, limit=10, project=None, **kwargs):
        captured_kwargs["project"] = project
        return [{"id": 10, "task_id": "t1", "project": project, "problem_summary": "p", "solution_code": "c"}]

    monkeypatch.setattr(main, "pool", mock_pool)
    monkeypatch.setattr("main.search_solutions_by_text", mock_search_by_text)

    payload = {
        "query_text": "connection pool issue",
        "project": "secret-project-omega",
        "limit": 5
    }
    resp = await async_client.post("/knowledge/search", json=payload)
    assert resp.status_code == 200
    assert captured_kwargs["project"] == "secret-project-omega"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pgvector_live_integration():
    """Verify live PostgreSQL pgvector insertion and cosine similarity search."""
    import asyncpg

    db_url = os.environ.get("DATABASE_URL", "postgresql://observer:observer_secret_pw_123@127.0.0.1:5432/observer")
    pool = await asyncpg.create_pool(db_url, min_size=1, max_size=2)
    try:
        # Create a test task first
        test_task_id = "test_vec_task_001"
        async with pool.acquire() as c:
            await c.execute("INSERT INTO tasks (task_id, project) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                            test_task_id, "pgvector_test")

        # 1536-dimensional mock embedding vector
        vec_a = [0.0] * 1536
        vec_a[0] = 1.0  # unit vector along dimension 0

        sol_id = await index_solution(
            pool=pool,
            task_id=test_task_id,
            problem_summary="Implement resilient streaming proxy",
            solution_code="async def stream(): yield chunk",
            outcome_status="pass",
            task_type="proxy",
            embedding=vec_a
        )
        assert sol_id is not None

        # Search with the exact same vector
        results = await search_solutions_by_embedding(
            pool=pool,
            query_vector=vec_a,
            limit=5
        )
        assert len(results) >= 1
        top_match = results[0]
        assert top_match["id"] == sol_id
        # Cosine similarity with identical vector should be ~1.0
        assert top_match["similarity"] > 0.99

        # Clean up test row
        async with pool.acquire() as c:
            await c.execute("DELETE FROM solutions WHERE id = $1", sol_id)
            await c.execute("DELETE FROM tasks WHERE task_id = $1", test_task_id)
    finally:
        await pool.close()
