"""
Standard benchmark coding evaluation tasks for model benchmarking.
"""
from dataclasses import dataclass
from typing import Callable, List, Optional


@dataclass
class BenchmarkTask:
    id: str
    task_type: str
    prompt: str
    function_name: str
    test_cases: List[dict]
    verification_code: str


BENCHMARK_TASKS: List[BenchmarkTask] = [
    BenchmarkTask(
        id="bench-algo-fib",
        task_type="algorithms",
        prompt=(
            "Write a Python function `fibonacci(n: int) -> int` that returns the n-th Fibonacci number "
            "where fibonacci(0) = 0 and fibonacci(1) = 1. The solution must be efficient (O(n) time, O(1) space). "
            "Return only the Python code inside markdown triple backticks."
        ),
        function_name="fibonacci",
        test_cases=[
            {"input": 0, "expected": 0},
            {"input": 1, "expected": 1},
            {"input": 10, "expected": 55},
            {"input": 30, "expected": 832040},
        ],
        verification_code="""
assert fibonacci(0) == 0
assert fibonacci(1) == 1
assert fibonacci(10) == 55
assert fibonacci(30) == 832040
"""
    ),
    BenchmarkTask(
        id="bench-ds-lru",
        task_type="data_structures",
        prompt=(
            "Write a Python class `LRUCache` with methods `get(key: int) -> int` and `put(key: int, value: int) -> None`. "
            "Initialize with `capacity: int`. Return -1 if key is not found. When capacity is exceeded, evict least recently used item. "
            "Return only the Python code inside markdown triple backticks."
        ),
        function_name="LRUCache",
        test_cases=[],
        verification_code="""
cache = LRUCache(2)
cache.put(1, 1)
cache.put(2, 2)
assert cache.get(1) == 1
cache.put(3, 3) # evicts 2
assert cache.get(2) == -1
cache.put(4, 4) # evicts 1
assert cache.get(1) == -1
assert cache.get(3) == 3
assert cache.get(4) == 4
"""
    ),
    BenchmarkTask(
        id="bench-algo-parens",
        task_type="algorithms",
        prompt=(
            "Write a Python function `is_valid_parentheses(s: str) -> bool` that checks if the input string containing "
            "characters '(', ')', '{', '}', '[' and ']' has valid matching brackets in correct order. "
            "Return only the Python code inside markdown triple backticks."
        ),
        function_name="is_valid_parentheses",
        test_cases=[
            {"input": "()[]{}", "expected": True},
            {"input": "(]", "expected": False},
            {"input": "([{}])", "expected": True},
            {"input": "((", "expected": False},
        ],
        verification_code="""
assert is_valid_parentheses("()[]{}") is True
assert is_valid_parentheses("(]") is False
assert is_valid_parentheses("([{}])") is True
assert is_valid_parentheses("(((") is False
assert is_valid_parentheses("") is True
"""
    ),
    BenchmarkTask(
        id="bench-str-phone",
        task_type="string_processing",
        prompt=(
            "Write a Python function `normalize_phone_number(s: str) -> Optional[str]` that strips all non-digit "
            "characters. If the digits count is 10, prepend '+1'. If 11 and starts with '1', prepend '+'. "
            "Otherwise return None. Return only the Python code inside markdown triple backticks."
        ),
        function_name="normalize_phone_number",
        test_cases=[],
        verification_code="""
assert normalize_phone_number("(555) 123-4567") == "+15551234567"
assert normalize_phone_number("1-555-123-4567") == "+15551234567"
assert normalize_phone_number("5551234567") == "+15551234567"
assert normalize_phone_number("123") is None
"""
    )
]
