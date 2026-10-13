"""
CI and Test/Lint Outcome Reporter for AI Model Observer.

Wraps any test, lint, or build command, captures output & metrics,
and automatically posts the outcome signal to the Observer.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple
import urllib.request
import urllib.error


def parse_test_output(output: str) -> Dict[str, int]:
    """Parse common test runner output for passed/failed counts."""
    metrics = {}
    
    # Pytest pattern: 40 passed, 2 failed, 1 error
    p_passed = re.search(r"(\d+)\s+passed", output, re.IGNORECASE)
    p_failed = re.search(r"(\d+)\s+failed", output, re.IGNORECASE)
    p_errors = re.search(r"(\d+)\s+error", output, re.IGNORECASE)
    p_skipped = re.search(r"(\d+)\s+skipped", output, re.IGNORECASE)

    if p_passed:
        metrics["passed"] = int(p_passed.group(1))
    if p_failed:
        metrics["failed"] = int(p_failed.group(1))
    if p_errors:
        metrics["errors"] = int(p_errors.group(1))
    if p_skipped:
        metrics["skipped"] = int(p_skipped.group(1))

    # Jest/npm pattern: Tests: 2 failed, 15 passed, 17 total
    jest_match = re.search(r"Tests:\s*(.*)", output)
    if jest_match and not metrics:
        j_text = jest_match.group(1)
        j_p = re.search(r"(\d+)\s+passed", j_text)
        j_f = re.search(r"(\d+)\s+failed", j_text)
        if j_p:
            metrics["passed"] = int(j_p.group(1))
        if j_f:
            metrics["failed"] = int(j_f.group(1))

    return metrics


def send_outcome(
    task_id: str,
    kind: str,
    status: str,
    details: dict,
    observer_url: str = "http://localhost:8787",
    token: Optional[str] = None
) -> bool:
    """Send outcome record to the Observer server."""
    payload = {
        "task_id": task_id,
        "kind": kind,
        "status": status,
        "details": details
    }
    url = observer_url.rstrip("/") + "/outcomes"
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    auth_token = token or os.environ.get("OBSERVER_AUTH_TOKEN")
    if auth_token:
        headers["X-Observer-Token"] = auth_token

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[Observer CI Reporter] Warning: could not send outcome ({e})", file=sys.stderr)
        return False


def run_and_report(
    command: List[str],
    task_id: str,
    kind: str = "test",
    observer_url: str = "http://localhost:8787",
    token: Optional[str] = None
) -> int:
    """Execute command, capture status, post outcome, and return exit code."""
    t0 = time.perf_counter()
    print(f"[Observer CI Reporter] Running command: {' '.join(command)}")

    # Run subprocess and stream output live while capturing it
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    captured_lines = []
    if proc.stdout:
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            captured_lines.append(line)

    exit_code = proc.wait()
    duration_ms = int((time.perf_counter() - t0) * 1000)
    full_output = "".join(captured_lines)

    status = "pass" if exit_code == 0 else "fail"
    parsed_metrics = parse_test_output(full_output)

    details = {
        "command": " ".join(command),
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "tail": "".join(captured_lines[-30:]) if len(captured_lines) > 30 else full_output,
        **parsed_metrics
    }

    send_outcome(
        task_id=task_id,
        kind=kind,
        status=status,
        details=details,
        observer_url=observer_url,
        token=token
    )

    return exit_code


def main():
    parser = argparse.ArgumentParser(
        description="Run test/lint/build command and report outcome to AI Model Observer",
        usage="python -m hooks.ci_reporter --task-id <id> [--kind <kind>] -- <command...>"
    )
    parser.add_argument("--task-id", required=True, help="Task ID to associate the outcome with")
    parser.add_argument("--kind", default="test", choices=["test", "build", "lint", "security"],
                        help="Outcome kind (default: test)")
    parser.add_argument("--url", default=os.environ.get("OBSERVER_URL", "http://localhost:8787"),
                        help="Observer base URL")
    parser.add_argument("--token", default=os.environ.get("OBSERVER_AUTH_TOKEN"),
                        help="Observer authentication token")
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="Command to execute (specify after --)")

    args = parser.parse_args()

    cmd = args.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]

    if not cmd:
        parser.print_help()
        return 1

    return run_and_report(
        command=cmd,
        task_id=args.task_id,
        kind=args.kind,
        observer_url=args.url,
        token=args.token
    )


if __name__ == "__main__":
    sys.exit(main())
