import pytest
import httpx
from benchmarks.tasks import BENCHMARK_TASKS
from benchmarks.runner import extract_code_block, verify_code_solution, run_task_on_model
from benchmarks.eval_reporter import format_benchmark_markdown_report


def test_extract_code_block():
    wrapped = "Here is the code:\n```python\ndef add(a, b):\n    return a + b\n```\nEnjoy!"
    assert extract_code_block(wrapped) == "def add(a, b):\n    return a + b"

    plain = "def sub(a, b):\n    return a - b"
    assert extract_code_block(plain) == plain


def test_verify_code_solution():
    code_pass = "def fibonacci(n):\n    if n <= 1: return n\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a"
    verif = "assert fibonacci(0) == 0\nassert fibonacci(1) == 1\nassert fibonacci(10) == 55"
    res = verify_code_solution(code_pass, verif)
    assert res["passed"] is True
    assert res["error"] is None

    # Failing code
    code_fail = "def fibonacci(n): return 0"
    res_fail = verify_code_solution(code_fail, verif)
    assert res_fail["passed"] is False
    assert "AssertionError" in res_fail["error"]

    # Syntax error code
    code_syntax_err = "def bad(: pass"
    res_err = verify_code_solution(code_syntax_err, verif)
    assert res_err["passed"] is False
    assert "SyntaxError" in res_err["error"]


def test_benchmark_tasks_structure():
    assert len(BENCHMARK_TASKS) >= 4
    for task in BENCHMARK_TASKS:
        assert task.id.startswith("bench-")
        assert len(task.prompt) > 20
        assert len(task.verification_code) > 10


@pytest.mark.asyncio
async def test_run_task_on_model_mocked():
    outcomes_reported = []

    def mock_handler(request: httpx.Request):
        url = str(request.url)
        if "/v1/chat/completions" in url:
            resp_body = {
                "choices": [{
                    "message": {
                        "content": "```python\ndef is_valid_parentheses(s):\n    stack = []\n    m = {')': '(', '}': '{', ']': '['}\n    for c in s:\n        if c in m.values():\n            stack.append(c)\n        elif c in m:\n            if not stack or stack.pop() != m[c]: return False\n    return len(stack) == 0\n```"
                    }
                }]
            }
            return httpx.Response(200, json=resp_body)
        elif "/outcomes" in url:
            import json
            outcomes_reported.append(json.loads(request.read()))
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    task = next(t for t in BENCHMARK_TASKS if t.id == "bench-algo-parens")

    result = await run_task_on_model(
        client=client,
        observer_base_url="http://test-observer",
        task=task,
        model="deepseek",
        auth_token="token-123"
    )

    assert result["passed"] is True
    assert result["status"] == "pass"
    assert len(outcomes_reported) == 1
    assert outcomes_reported[0]["status"] == "pass"
    assert outcomes_reported[0]["task_id"] == "bench-algo-parens-deepseek"


def test_format_benchmark_markdown_report():
    sample_data = {
        "models": {
            "deepseek": {"total": 4, "passes": 4, "fails": 0, "pass_rate": 1.0, "avg_latency_ms": 320},
            "claude": {"total": 4, "passes": 3, "fails": 1, "pass_rate": 0.75, "avg_latency_ms": 650},
        },
        "runs": [
            {"task_name": "bench-algo-fib", "task_type": "algorithms", "model": "deepseek", "passed": True, "latency_ms": 300, "error": None},
            {"task_name": "bench-algo-fib", "task_type": "algorithms", "model": "claude", "passed": False, "latency_ms": 600, "error": "AssertionError"},
        ]
    }
    report = format_benchmark_markdown_report(sample_data)
    assert "# Model Benchmark Evaluation Report" in report
    assert "`deepseek`" in report
    assert "**100.0%**" in report
    assert "**75.0%**" in report
    assert "✅ PASS" in report
    assert "❌ FAIL" in report
