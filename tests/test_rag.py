import json
import pytest
from unittest.mock import AsyncMock, MagicMock
import httpx
from app.rag import (
    format_solution_context,
    extract_prompt_text,
    augment_openai_request,
    augment_anthropic_request,
)
import main


def test_format_solution_context():
    solutions = [
        {
            "task_id": "task_1",
            "task_type": "frontend",
            "problem_summary": "Render user profile card",
            "solution_code": "export function Card() { return <div/> }",
            "similarity": 0.94
        }
    ]
    formatted = format_solution_context(solutions)
    assert "[AI MODEL OBSERVER: RELEVANT VERIFIED PAST SOLUTIONS]" in formatted
    assert "Task: task_1" in formatted
    assert "Render user profile card" in formatted
    assert "94%" in formatted
    assert "export function Card()" in formatted


def test_extract_prompt_text():
    # OpenAI format with string content
    req_openai = {
        "messages": [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Fix the bug in auth"}
        ]
    }
    assert extract_prompt_text(req_openai, "openai") == "Fix the bug in auth"

    # Multimodal / block content format
    req_multimodal = {
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": "Describe the"}, {"type": "text", "text": "issue"}]}
        ]
    }
    assert extract_prompt_text(req_multimodal, "openai") == "Describe the issue"


def test_augment_openai_request_with_existing_system():
    body = {
        "messages": [
            {"role": "system", "content": "Initial prompt"},
            {"role": "user", "content": "Solve task"}
        ]
    }
    solutions = [{"task_id": "t1", "problem_summary": "p", "solution_code": "c"}]
    augmented = augment_openai_request(body, solutions)
    assert len(augmented["messages"]) == 2
    assert "Initial prompt" in augmented["messages"][0]["content"]
    assert "[AI MODEL OBSERVER" in augmented["messages"][0]["content"]


def test_augment_openai_request_without_system():
    body = {
        "messages": [
            {"role": "user", "content": "Solve task"}
        ]
    }
    solutions = [{"task_id": "t1", "problem_summary": "p", "solution_code": "c"}]
    augmented = augment_openai_request(body, solutions)
    assert len(augmented["messages"]) == 2
    assert augmented["messages"][0]["role"] == "system"
    assert "[AI MODEL OBSERVER" in augmented["messages"][0]["content"]


def test_augment_anthropic_request():
    body = {
        "system": "Base instructions",
        "messages": [{"role": "user", "content": "Hi"}]
    }
    solutions = [{"task_id": "t1", "problem_summary": "p", "solution_code": "c"}]
    augmented = augment_anthropic_request(body, solutions)
    assert "Base instructions" in augmented["system"]
    assert "[AI MODEL OBSERVER" in augmented["system"]


@pytest.mark.asyncio
async def test_proxy_injects_rag_when_header_present(async_client, monkeypatch):
    captured_request = {}

    def mock_handler(request: httpx.Request):
        captured_request["body"] = request.read().decode("utf-8")
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    monkeypatch.setattr(main, "client", mock_client)

    # Mock database pool and solution search
    mock_pool = MagicMock()
    monkeypatch.setattr(main, "pool", mock_pool)

    mock_solution = {
        "id": 99,
        "task_id": "past_task_123",
        "task_type": "backend",
        "problem_summary": "Handle database pool crash",
        "solution_code": "try: pass except: pass",
        "similarity": 0.98
    }

    async def mock_search(pool, query_vec, limit, task_type, **kwargs):
        return [mock_solution]

    monkeypatch.setattr("main.search_solutions_by_embedding", mock_search)

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "Handle database pool crash"}]
    }
    headers = {
        "X-Inject-Knowledge": "true",
        "X-Task-Id": "current_task_456"
    }

    resp = await async_client.post("/v1/chat/completions", json=payload, headers=headers)
    assert resp.status_code == 200

    # Upstream body should contain injected past solution context
    sent_body = json.loads(captured_request["body"])
    assert len(sent_body["messages"]) == 2
    assert sent_body["messages"][0]["role"] == "system"
    assert "Handle database pool crash" in sent_body["messages"][0]["content"]
    assert "past_task_123" in sent_body["messages"][0]["content"]


@pytest.mark.asyncio
async def test_auto_index_task_solution_on_passing_outcome(async_client, monkeypatch):
    mock_pool = MagicMock()
    mock_conn = MagicMock()

    # Task is not yet in solutions
    mock_conn.fetchval = AsyncMock(return_value=None)
    # Return previous call
    mock_conn.fetchrow = AsyncMock(return_value={
        "id": 1,
        "task_type": "coding",
        "project": "demo",
        "request": {"messages": [{"role": "user", "content": "Implement Fibonacci"}]},
        "response_text": "def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)"
    })
    mock_conn.execute = AsyncMock(return_value=None)

    mock_acquire = MagicMock()
    mock_acquire.__aenter__.return_value = mock_conn
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire

    monkeypatch.setattr(main, "pool", mock_pool)

    indexed_solutions = []

    async def mock_index(pool, task_id, problem_summary, solution_code, outcome_status, task_type, project, embedding):
        indexed_solutions.append({
            "task_id": task_id,
            "problem": problem_summary,
            "solution": solution_code,
            "status": outcome_status
        })
        return 1

    monkeypatch.setattr("main.index_solution", mock_index)

    # Post passing outcome to /outcomes
    resp = await async_client.post("/outcomes", json={
        "task_id": "task_fib_01",
        "kind": "test",
        "status": "pass",
        "details": {"passed": 5}
    })
    assert resp.status_code == 200
    assert len(indexed_solutions) == 1
    assert indexed_solutions[0]["task_id"] == "task_fib_01"
    assert "Fibonacci" in indexed_solutions[0]["problem"]
    assert "def fib" in indexed_solutions[0]["solution"]
