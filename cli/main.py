#!/usr/bin/env python3
"""
AI Observer CLI - Developer terminal companion.
Activates local/team terminals to route through AI Observer and displays personal API usage.
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import webbrowser
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_DIR = Path.home() / ".ai-observer"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> Dict[str, Any]:
    """Load local client configuration."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(cfg: Dict[str, Any]) -> None:
    """Save local client configuration."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


DEFAULT_SERVER = os.environ.get("OBSERVER_SERVER_URL", "https://ai-observer-8wcb.onrender.com")


def normalize_url(url: str) -> str:
    """Ensure URL has scheme and trimmed trailing slashes."""
    raw = (url or "").strip().rstrip("/")
    if not raw or raw in ("hi", "test", "hello"):
        return DEFAULT_SERVER
    if not raw.startswith("http://") and not raw.startswith("https://"):
        return f"http://{raw}"
    return raw


def get_server_url(cfg: Dict[str, Any]) -> str:
    """Resolve active observer server base URL."""
    return normalize_url(
        os.environ.get("OBSERVER_SERVER_URL")
        or cfg.get("server_url")
        or DEFAULT_SERVER
    )


def cmd_activate(args: argparse.Namespace) -> int:
    """Activate or reconfigure AI Observer on the developer's computer."""
    cfg = load_config()
    raw_server = args.server or cfg.get("server_url")
    server = normalize_url(raw_server if raw_server and "://" in raw_server else DEFAULT_SERVER)
    user = args.user or cfg.get("user") or os.environ.get("USERNAME") or os.environ.get("USER") or "dev"
    project = args.project or cfg.get("project") or "default-project"
    key = args.key or cfg.get("api_key")

    if not args.non_interactive:
        print("=== AI Observer Client Setup ===")
        input_server = input(f"Central Observer Server URL [{server}]: ").strip()
        if input_server:
            server = normalize_url(input_server)
        input_user = input(f"Developer Name / Session ID [{user}]: ").strip()
        if input_user:
            user = input_user
        input_proj = input(f"Default Project Name [{project}]: ").strip()
        if input_proj:
            project = input_proj
        if not key:
            input_key = input("Your Personal API Key (e.g. Google Gemini AI Studio key) [press enter to keep empty]: ").strip()
            if input_key:
                key = input_key

    # Check connection to server
    print(f"\n[+] Verifying connection to AI Observer at {server}...")
    try:
        req = urllib.request.Request(f"{server}/health", headers={"User-Agent": "AI-Observer-CLI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                print("    Connected! Server status: READY")
            else:
                print(f"    Server replied: {data}")
    except Exception as exc:
        print(f"    [!] Warning: Could not reach server at {server}/health ({exc}).")
        print("    You can still save this configuration and verify network connection.")

    new_cfg = {
        "server_url": server,
        "user": user,
        "project": project,
        "api_key": key or "",
    }
    save_config(new_cfg)
    print(f"[+] Saved configuration to: {CONFIG_FILE}")

    proxy_v1 = f"{server}/v1"
    print("\n" + "=" * 60)
    print("AI Observer is activated for your terminal!")
    print("=" * 60)
    print(f"Developer ID : {user}")
    print(f"Project      : {project}")
    print(f"Proxy BaseURL: {proxy_v1}")
    print("=" * 60)

    print("\nTo route your current terminal session through the Observer, run:")
    if sys.platform == "win32":
        print("  PowerShell:")
        print(f'    $env:OPENAI_BASE_URL="{proxy_v1}"')
        if key:
            print(f'    $env:OPENAI_API_KEY="{key}"')
        print(f'    $env:OBSERVER_TASK_ID="{project}"')
    else:
        print("  Bash / Zsh:")
        print(f'    export OPENAI_BASE_URL="{proxy_v1}"')
        if key:
            print(f'    export OPENAI_API_KEY="{key}"')
        print(f'    export OBSERVER_TASK_ID="{project}"')

    print("\nFor IDEs (Cursor / VS Code Continue / Cline):")
    print(f"  - Override Base URL: {proxy_v1}")
    print(f"  - Model            : gemini-3.1-flash-lite-preview (or gemini-3.8-flash)")
    print(f"  - API Key          : your personal key")
    print("=" * 60)
    return 0


def cmd_usage(args: argparse.Namespace) -> int:
    """Fetch and print API usage metrics for the active developer or team."""
    cfg = load_config()
    server = (args.server or get_server_url(cfg)).rstrip("/")
    user = args.user or (None if args.all else cfg.get("user"))
    project = args.project or cfg.get("project")

    query_params = []
    if user:
        query_params.append(f"session_id={urllib.parse.quote(user)}")
    if project and not args.all:
        query_params.append(f"project={urllib.parse.quote(project)}")

    url = f"{server}/stats"
    if query_params:
        url += "?" + "&".join(query_params)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AI-Observer-CLI/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            stats = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"Error: Unable to fetch usage from {url} ({exc})", file=sys.stderr)
        return 1

    scope_label = f"Developer: {user or 'Entire Team'}"
    if project and not args.all:
        scope_label += f" | Project: {project}"

    print("\n" + "=" * 70)
    print(f" AI Observer - Usage Analytics ({scope_label})")
    print(f" Server: {server}")
    print("=" * 70)

    if not stats:
        print(" No requests recorded yet for this filter.")
        print(f" Make requests using Base URL: {server}/v1")
        print("=" * 70)
        return 0

    header = f"{'Model':<30} {'Calls':<8} {'Avg Latency':<14} {'In Tokens':<12} {'Out Tokens':<12} {'Passes':<8}"
    print(header)
    print("-" * 70)

    total_calls = 0
    total_in = 0
    total_out = 0
    total_passes = 0
    total_fails = 0

    for row in stats:
        model = row.get("model", "unknown")[:28]
        calls = row.get("calls") or 0
        lat = f"{row.get('avg_latency_ms') or 0} ms"
        in_t = row.get("input_tokens") or 0
        out_t = row.get("output_tokens") or 0
        passes = row.get("passes") or 0
        fails = row.get("fails") or 0

        total_calls += calls
        total_in += in_t
        total_out += out_t
        total_passes += passes
        total_fails += fails

        print(f"{model:<30} {calls:<8} {lat:<14} {in_t:<12} {out_t:<12} {passes:<8}")

    print("-" * 70)
    print(f"{'TOTAL':<30} {total_calls:<8} {'-':<14} {total_in:<12} {total_out:<12} {total_passes:<8}")
    print("=" * 70)
    print(f"To open the interactive visual dashboard, run: observer dashboard\n")
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    """Open the web dashboard in the default browser."""
    cfg = load_config()
    server = (args.server or get_server_url(cfg)).rstrip("/")
    url = f"{server}/dashboard"
    if getattr(args, "admin", False):
        admin_token = getattr(args, "token", None) or os.environ.get("OBSERVER_ADMIN_KEY") or os.environ.get("ADMIN_TOKEN")
        if admin_token:
            url += f"?admin_token={urllib.parse.quote(admin_token)}"
        else:
            url += "?admin=true"
    else:
        user = getattr(args, "user", None) or cfg.get("user")
        if user:
            url += f"?user={urllib.parse.quote(user)}"
    print(f"[+] Opening AI Observer Dashboard: {url}")
    try:
        webbrowser.open(url)
    except Exception as exc:
        print(f"Could not open browser automatically: {exc}. Please visit: {url}")
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    """Send a minimal test request to verify end-to-end proxy connectivity."""
    cfg = load_config()
    server = (args.server or get_server_url(cfg)).rstrip("/")
    key = args.key or cfg.get("api_key") or os.environ.get("OPENAI_API_KEY")
    if not key:
        print("[!] Note: No personal API key found in ~/.ai-observer/config.json.")
        print("    If BYOK is enabled on the server, please set your Gemini key via 'observer activate', or pass --key <KEY>.")
        key = "test-key"
    user = args.user or cfg.get("user") or "cli-tester"
    project = args.project or cfg.get("project") or "test-project"
    model = args.model or "gemini-3.1-flash-lite-preview"

    print(f"[+] Testing proxy route at {server}/v1/chat/completions using model '{model}'...")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Respond with the single word: PONG"}],
        "max_tokens": 10,
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        "X-Session-Id": user,
        "X-Project": project,
        "X-Task-Id": "cli-healthcheck",
    }

    try:
        req = urllib.request.Request(f"{server}/v1/chat/completions", data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            content = body["choices"][0]["message"]["content"]
            usage = body.get("usage", {})
            print(f"[+] Success! Response from {model}: {repr(content)}")
            print(f"    Tokens: {usage.get('prompt_tokens', 0)} in / {usage.get('completion_tokens', 0)} out")
            print(f"    Captured and logged into Observer database!")
            return 0
    except urllib.error.HTTPError as err:
        error_msg = err.read().decode("utf-8", errors="replace")
        print(f"[!] HTTP Error {err.code}: {error_msg}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[!] Test failed: {exc}", file=sys.stderr)
        return 1


def cmd_env(args: argparse.Namespace) -> int:
    """Print export commands for terminal environments."""
    cfg = load_config()
    server = (args.server or get_server_url(cfg)).rstrip("/")
    key = cfg.get("api_key") or "your-api-key"
    proxy_v1 = f"{server}/v1"

    if args.shell == "powershell":
        print(f'$env:OPENAI_BASE_URL="{proxy_v1}"')
        print(f'$env:OPENAI_API_KEY="{key}"')
    else:
        print(f'export OPENAI_BASE_URL="{proxy_v1}"')
        print(f'export OPENAI_API_KEY="{key}"')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="observer",
        description="AI Model Observer CLI - Activate terminal proxying and track LLM usage.",
    )
    parser.add_argument("--admin", action="store_true", help="Open visual dashboard in Admin mode")
    parser.add_argument("--token", help="Admin secret token")
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # activate
    p_act = subparsers.add_parser("activate", help="Configure and activate Observer in this terminal")
    p_act.add_argument("--server", help="Observer server URL (default: https://ai-observer-8wcb.onrender.com)")
    p_act.add_argument("--user", help="Your developer username / session ID")
    p_act.add_argument("--project", help="Default project tag")
    p_act.add_argument("--key", help="Your personal API key")
    p_act.add_argument("-y", "--non-interactive", action="store_true", help="Skip interactive prompts")

    # usage / stats
    p_usage = subparsers.add_parser("usage", aliases=["stats"], help="View your API token usage and stats")
    p_usage.add_argument("--server", help="Observer server URL")
    p_usage.add_argument("--user", help="Filter by specific developer username")
    p_usage.add_argument("--project", help="Filter by project")
    p_usage.add_argument("--all", action="store_true", help="Show all team usage instead of just yours")

    # dashboard
    p_dash = subparsers.add_parser("dashboard", help="Open visual web dashboard in browser")
    p_dash.add_argument("--server", help="Observer server URL")
    p_dash.add_argument("--user", help="Developer username to view scoped personal dashboard")
    p_dash.add_argument("--admin", action="store_true", help="Open in Admin mode with full system visibility")
    p_dash.add_argument("--token", help="Admin secret token")

    # test
    p_test = subparsers.add_parser("test", help="Test connection and model response through proxy")
    p_test.add_argument("--server", help="Observer server URL")
    p_test.add_argument("--model", default="gemini-3.1-flash-lite-preview", help="Model name to test")
    p_test.add_argument("--key", help="Your personal API key")
    p_test.add_argument("--user", help="Developer username")
    p_test.add_argument("--project", help="Project name")

    # env
    p_env = subparsers.add_parser("env", help="Print shell export statements for OPENAI_BASE_URL")
    p_env.add_argument("--shell", choices=["bash", "zsh", "powershell"], default="powershell" if sys.platform == "win32" else "bash")
    p_env.add_argument("--server", help="Observer server URL")

    args = parser.parse_args()

    if not args.subcommand:
        if getattr(args, "admin", False) or getattr(args, "token", None):
            return cmd_dashboard(args)
        parser.print_help()
        return 0

    if args.subcommand == "activate":
        return cmd_activate(args)
    elif args.subcommand in ("usage", "stats"):
        return cmd_usage(args)
    elif args.subcommand == "dashboard":
        return cmd_dashboard(args)
    elif args.subcommand == "test":
        return cmd_test(args)
    elif args.subcommand == "env":
        return cmd_env(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
