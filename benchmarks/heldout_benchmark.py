"""
Held-Out Evaluation Benchmark Suite.

Contains 10 unseen, rigorous coding tasks strictly isolated from training
and validation datasets. Used to verify that fine-tuning gains represent
genuine coding capability rather than memorization or training data leakage.
"""
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class HeldOutTask:
    id: str
    task_type: str
    prompt: str
    function_name: str
    verification_code: str


HELDOUT_BENCHMARK_TASKS: List[HeldOutTask] = [
    HeldOutTask(
        id="heldout-async-limiter",
        task_type="concurrency",
        prompt=(
            "Write a Python class `AsyncTokenBucket` implementing the token bucket rate limiting algorithm. "
            "Initialize with `capacity: int` and `fill_rate: float` (tokens per second). "
            "Implement async method `async def acquire(tokens: int = 1) -> bool` that consumes tokens if available "
            "without blocking, returning True if tokens were consumed or False otherwise. "
            "Return only the Python code inside markdown triple backticks."
        ),
        function_name="AsyncTokenBucket",
        verification_code="""
import asyncio, time
bucket = AsyncTokenBucket(capacity=5, fill_rate=10.0)
assert asyncio.run(bucket.acquire(3)) is True
assert asyncio.run(bucket.acquire(2)) is True
assert asyncio.run(bucket.acquire(1)) is False
time.sleep(0.2) # adds ~2 tokens
assert asyncio.run(bucket.acquire(1)) is True
"""
    ),
    HeldOutTask(
        id="heldout-trie-prefix",
        task_type="data_structures",
        prompt=(
            "Write a Python class `Trie` with methods `insert(word: str) -> None`, "
            "`search(word: str) -> bool`, and `starts_with(prefix: str) -> bool`. "
            "Return only the Python code inside markdown triple backticks."
        ),
        function_name="Trie",
        verification_code="""
t = Trie()
t.insert("apple")
assert t.search("apple") is True
assert t.search("app") is False
assert t.starts_with("app") is True
t.insert("app")
assert t.search("app") is True
assert t.starts_with("ban") is False
"""
    ),
    HeldOutTask(
        id="heldout-sql-guard",
        task_type="security",
        prompt=(
            "Write a Python function `is_safe_sql_identifier(identifier: str) -> bool` that verifies if a given string "
            "is a safe SQL identifier (table or column name): must begin with a letter or underscore, contain only letters, "
            "digits, and underscores, cannot be empty, cannot exceed 63 characters, and cannot match common SQL keywords "
            "such as 'SELECT', 'DROP', 'INSERT', 'DELETE', 'UPDATE', 'TABLE', 'FROM', 'WHERE' (case-insensitive). "
            "Return only the Python code inside markdown triple backticks."
        ),
        function_name="is_safe_sql_identifier",
        verification_code="""
assert is_safe_sql_identifier("user_accounts") is True
assert is_safe_sql_identifier("_private_id") is True
assert is_safe_sql_identifier("123users") is False
assert is_safe_sql_identifier("user-name") is False
assert is_safe_sql_identifier("SELECT") is False
assert is_safe_sql_identifier("drop") is False
assert is_safe_sql_identifier("") is False
assert is_safe_sql_identifier("a" * 64) is False
assert is_safe_sql_identifier("a" * 63) is True
"""
    ),
    HeldOutTask(
        id="heldout-dag-topological-sort",
        task_type="algorithms",
        prompt=(
            "Write a Python function `topological_sort(num_nodes: int, edges: list[tuple[int, int]]) -> list[int]` "
            "that takes the total number of nodes (labeled 0 to num_nodes - 1) and directed edges (u, v) where u -> v. "
            "Return a valid topological ordering of nodes. If the graph contains a cycle, return an empty list `[]`. "
            "Return only the Python code inside markdown triple backticks."
        ),
        function_name="topological_sort",
        verification_code="""
# DAG: 0 -> 1, 0 -> 2, 1 -> 3, 2 -> 3
order = topological_sort(4, [(0, 1), (0, 2), (1, 3), (2, 3)])
assert len(order) == 4
assert order.index(0) < order.index(1)
assert order.index(0) < order.index(2)
assert order.index(1) < order.index(3)
assert order.index(2) < order.index(3)

# Cycle: 0 -> 1, 1 -> 2, 2 -> 0
assert topological_sort(3, [(0, 1), (1, 2), (2, 0)]) == []
"""
    ),
    HeldOutTask(
        id="heldout-sliding-window-max",
        task_type="algorithms",
        prompt=(
            "Write an efficient Python function `max_sliding_window(nums: list[int], k: int) -> list[int]` "
            "that returns the maximum element in each sliding window of size k moving from left to right. "
            "The solution must be O(N) time complexity using a monotonic deque. "
            "Return only the Python code inside markdown triple backticks."
        ),
        function_name="max_sliding_window",
        verification_code="""
assert max_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
assert max_sliding_window([1], 1) == [1]
assert max_sliding_window([1, -1], 1) == [1, -1]
assert max_sliding_window([9, 11], 2) == [11]
assert max_sliding_window([], 0) == []
"""
    ),
    HeldOutTask(
        id="heldout-json-patch-apply",
        task_type="data_processing",
        prompt=(
            "Write a Python function `apply_json_patches(doc: dict, patches: list[dict]) -> dict` "
            "implementing basic RFC 6902 JSON patch operations: 'add', 'remove', and 'replace'. "
            "Each patch has keys 'op' and 'path' (e.g. '/a/b') and optional 'value'. "
            "Return the modified document. Return only the Python code inside markdown triple backticks."
        ),
        function_name="apply_json_patches",
        verification_code="""
doc = {"a": {"b": 10}, "c": [1, 2, 3]}
patches = [
    {"op": "replace", "path": "/a/b", "value": 20},
    {"op": "add", "path": "/a/d", "value": 30},
    {"op": "remove", "path": "/c"}
]
res = apply_json_patches(doc, patches)
assert res["a"]["b"] == 20
assert res["a"]["d"] == 30
assert "c" not in res
"""
    ),
    HeldOutTask(
        id="heldout-semaphore-pool",
        task_type="concurrency",
        prompt=(
            "Write an async Python class `BoundedResourcePool` with async context manager method "
            "`async def acquire(timeout_sec: float = 1.0)` that limits concurrent active resources to `max_size: int`. "
            "If a resource cannot be acquired within timeout, raise `TimeoutError`. "
            "Return only the Python code inside markdown triple backticks."
        ),
        function_name="BoundedResourcePool",
        verification_code="""
import asyncio
pool = BoundedResourcePool(max_size=2)
async def worker():
    async with pool.acquire(timeout_sec=0.5):
        await asyncio.sleep(0.05)
async def run_all():
    await asyncio.gather(worker(), worker(), worker())
asyncio.run(run_all())
"""
    ),
    HeldOutTask(
        id="heldout-csv-streaming-parser",
        task_type="data_processing",
        prompt=(
            "Write a Python generator function `parse_csv_lines(lines: list[str], delimiter: str = ',') -> list[list[str]]` "
            "that parses CSV lines handling double quotes and escaped quotes (e.g. `\"John \"\"Jack\"\" Doe\"`). "
            "Return only the Python code inside markdown triple backticks."
        ),
        function_name="parse_csv_lines",
        verification_code="""
data = ['name,age,city', '"Smith, John",30,"New York"', 'Jane,25,"San ""Sunny"" Francisco"']
res = list(parse_csv_lines(data))
assert res[0] == ["name", "age", "city"]
assert res[1] == ["Smith, John", "30", "New York"]
assert res[2] == ["Jane", "25", 'San "Sunny" Francisco']
"""
    ),
    HeldOutTask(
        id="heldout-binary-search-rotated",
        task_type="algorithms",
        prompt=(
            "Write a Python function `search_rotated_array(nums: list[int], target: int) -> int` "
            "that finds the index of `target` in a sorted array that was rotated at an unknown pivot. "
            "Must achieve O(log n) time complexity. Return -1 if target is not in nums. "
            "Return only the Python code inside markdown triple backticks."
        ),
        function_name="search_rotated_array",
        verification_code="""
assert search_rotated_array([4, 5, 6, 7, 0, 1, 2], 0) == 4
assert search_rotated_array([4, 5, 6, 7, 0, 1, 2], 3) == -1
assert search_rotated_array([1], 0) == -1
assert search_rotated_array([1], 1) == 0
assert search_rotated_array([5, 1, 3], 5) == 0
"""
    ),
    HeldOutTask(
        id="heldout-circuit-breaker",
        task_type="networking",
        prompt=(
            "Write a Python class `CircuitBreaker` with states 'CLOSED', 'OPEN', and 'HALF_OPEN'. "
            "Initialize with `failure_threshold: int = 3` and `recovery_time_sec: float = 1.0`. "
            "Implement method `record_failure()` and method `record_success()`, and `can_execute() -> bool`. "
            "When in CLOSED state, if failures reach failure_threshold, transition to OPEN. "
            "While in OPEN state, `can_execute()` returns False until recovery_time_sec passes, "
            "at which point state transitions to HALF_OPEN. In HALF_OPEN, a success returns to CLOSED, "
            "while a failure returns to OPEN. Return only the Python code inside markdown triple backticks."
        ),
        function_name="CircuitBreaker",
        verification_code="""
import time
cb = CircuitBreaker(failure_threshold=2, recovery_time_sec=0.1)
assert cb.can_execute() is True
cb.record_failure()
assert cb.can_execute() is True
cb.record_failure()
assert cb.can_execute() is False # Tripped to OPEN
time.sleep(0.15)
assert cb.can_execute() is True # Transitions to HALF_OPEN
cb.record_success()
assert cb.can_execute() is True # Restores to CLOSED
"""
    )
]
