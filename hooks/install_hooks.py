"""
Installer script for AI Model Observer git hooks.
"""
import os
import sys

POST_COMMIT_SCRIPT = """#!/bin/sh
# AI Model Observer post-commit hook
if [ -f ".venv/Scripts/python.exe" ]; then
    .venv/Scripts/python.exe -m hooks.git_tracker
elif command -v py >/dev/null 2>&1; then
    py -m hooks.git_tracker
else
    python -m hooks.git_tracker
fi
"""

def install_hook():
    git_dir = os.path.join(os.getcwd(), ".git")
    if not os.path.isdir(git_dir):
        print("Error: Not a git repository (.git folder not found).", file=sys.stderr)
        return 1

    hooks_dir = os.path.join(git_dir, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    post_commit_path = os.path.join(hooks_dir, "post-commit")

    with open(post_commit_path, "w", encoding="utf-8") as f:
        f.write(POST_COMMIT_SCRIPT)

    # Try setting executable permission on Unix-like environments
    try:
        os.chmod(post_commit_path, 0o755)
    except Exception:
        pass

    print(f"[Observer Hook] Installed post-commit hook at: {post_commit_path}")
    return 0

if __name__ == "__main__":
    sys.exit(install_hook())
