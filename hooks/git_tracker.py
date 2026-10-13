"""
Git outcome tracking hook for AI Model Observer.

Extracts commit metadata, files changed, and active task ID,
and sends a 'git' outcome record to the Observer capture proxy.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional
import urllib.request
import urllib.error


def run_git(args: List[str]) -> str:
    """Run a git command and return stripped stdout, or empty string on error."""
    try:
        res = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace"
        )
        return res.stdout.strip()
    except Exception:
        return ""


def detect_task_id(repo_root: Optional[str] = None) -> Optional[str]:
    """
    Attempt to discover active task ID from:
    1. OBSERVER_TASK_ID environment variable
    2. .observer_task file in repo root
    3. Commit message regex: [task_123] or task-123
    4. Current branch name: task/123 or feat/task_123
    """
    # 1. Environment variable
    env_task = os.environ.get("OBSERVER_TASK_ID")
    if env_task:
        return env_task.strip()

    # 2. .observer_task file
    if repo_root:
        marker_file = os.path.join(repo_root, ".observer_task")
        if os.path.isfile(marker_file):
            try:
                with open(marker_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        return content
            except Exception:
                pass

    # 3. Commit message
    msg = run_git(["log", "-1", "--format=%B"])
    match = re.search(r"\[(task[_-][A-Za-z0-9_\-]+)\]", msg, re.IGNORECASE)
    if match:
        return match.group(1)
    match_standalone = re.search(r"\b(task[_-][A-Za-z0-9_\-]+)\b", msg, re.IGNORECASE)
    if match_standalone:
        return match_standalone.group(1)

    # 4. Branch name
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    branch_match = re.search(r"task[/_-]([A-Za-z0-9_\-]+)", branch, re.IGNORECASE)
    if branch_match:
        return f"task_{branch_match.group(1)}"

    return None


def get_git_metadata() -> Dict[str, str | List[str]]:
    """Collect git commit metadata for the current HEAD."""
    commit_hash = run_git(["rev-parse", "HEAD"])
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    author = run_git(["log", "-1", "--format=%an <%ae>"])
    msg = run_git(["log", "-1", "--format=%B"])
    shortstat = run_git(["show", "--shortstat", "--format=", "HEAD"]).strip()
    
    # List files changed in the latest commit
    raw_files = run_git(["diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"])
    files_changed = [f.strip() for f in raw_files.splitlines() if f.strip()]

    return {
        "commit": commit_hash,
        "branch": branch,
        "author": author,
        "message": msg,
        "shortstat": shortstat,
        "files_changed": files_changed
    }


def report_git_outcome(
    task_id: str,
    status: str = "accepted",
    observer_url: str = "http://localhost:8787",
    token: Optional[str] = None,
    extra_details: Optional[dict] = None
) -> bool:
    """Post git outcome record to the observer proxy."""
    meta = get_git_metadata()
    if extra_details:
        meta.update(extra_details)

    payload = {
        "task_id": task_id,
        "kind": "git",
        "status": status,
        "details": meta
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
        # Never break developer commit flow
        print(f"[Observer Git Hook] Warning: could not report outcome ({e})", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Report git commit outcome to AI Model Observer")
    parser.add_argument("--task-id", help="Target task ID. If omitted, auto-discovered.")
    parser.add_argument("--status", default="accepted", choices=["accepted", "edited", "rejected"],
                        help="Outcome status (default: accepted)")
    parser.add_argument("--url", default=os.environ.get("OBSERVER_URL", "http://localhost:8787"),
                        help="Observer base URL (default: http://localhost:8787)")
    parser.add_argument("--token", default=os.environ.get("OBSERVER_AUTH_TOKEN"),
                        help="Observer authentication token")
    args = parser.parse_args()

    task_id = args.task_id or detect_task_id()
    if not task_id:
        print("[Observer Git Hook] No active task ID found; skipping outcome reporting.")
        return 0

    success = report_git_outcome(
        task_id=task_id,
        status=args.status,
        observer_url=args.url,
        token=args.token
    )
    if success:
        print(f"[Observer Git Hook] Recorded git outcome for {task_id} ({args.status}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
