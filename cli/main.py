#!/usr/bin/env python3
"""
AI Observer CLI - Developer terminal companion.
Activates local/team terminals to route through AI Observer and displays personal API usage.
"""
import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import threading
import time
import urllib.request
import urllib.error
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

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


# ────────── ObserverCoder-1.0 Multi-Model Engine ──────────

OBSERVER_CODER_CATALOG = [
    {
        "specialist": "fast_coder",
        "primary": "local/qwen2.5-coder:1.5b",
        "fallback": "qwen/qwen-2.5-coder-32b-instruct",
        "role": "Fast code generation & syntax repair",
        "license": "Apache 2.0",
        "track": "fast_coding (Default single-pass)"
    },
    {
        "specialist": "heavy_coder",
        "primary": "local/qwen2.5-coder:7b",
        "fallback": "qwen/qwen-2.5-coder-32b-instruct",
        "role": "Complex systems refactoring & multi-file architectures",
        "license": "Apache 2.0",
        "track": "two_pass_reasoning (Pass 2 Implementation)"
    },
    {
        "specialist": "deep_reasoner",
        "primary": "local/deepseek-r1:7b",
        "fallback": "deepseek-reasoner (DeepSeek-R1)",
        "role": "Chain-of-thought, algorithm design & system planning",
        "license": "MIT",
        "track": "two_pass_reasoning (Pass 1 Architecture Blueprint)"
    },
    {
        "specialist": "math_specialist",
        "primary": "local/qwen2.5-math:7b",
        "fallback": "qwen/qwen-2.5-coder-32b-instruct",
        "role": "Numerical formulas, proofs & algorithmic proofs",
        "license": "Apache 2.0",
        "track": "two_pass_reasoning (Pass 1 Mathematical Proof)"
    },
    {
        "specialist": "vision_specialist",
        "primary": "local/qwen2-vl:7b",
        "fallback": "qwen/qwen-2-vl-72b-instruct",
        "role": "UI mockups, screenshot analysis & visual inspection",
        "license": "Apache 2.0",
        "track": "vision (Multimodal Image Input)"
    }
]


class ThinkingIndicator:
    """
    Threaded terminal spinner showing 'Thinking...' with elapsed time.
    Erases itself cleanly the moment the first streaming token arrives.
    """
    def __init__(self, message: str = "Thinking...", interval: float = 0.08):
        self.message = message
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._is_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
        self._last_len = 0
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        try:
            "⠋".encode(getattr(sys.stdout, "encoding", None) or "utf-8")
        except Exception:
            self.frames = ["-", "\\", "|", "/"]

    def _spin(self) -> None:
        t0 = time.time()
        idx = 0
        while not self._stop_event.is_set():
            elapsed = time.time() - t0
            frame = self.frames[idx % len(self.frames)]
            idx += 1
            text = f"\r{frame} {self.message} ({elapsed:.1f}s)"
            self._last_len = max(self._last_len, len(text))
            try:
                sys.stdout.write(text)
                sys.stdout.flush()
            except Exception:
                break
            if self._stop_event.wait(self.interval):
                break

    def start(self) -> "ThinkingIndicator":
        if not self._is_tty:
            return self
        self._stop_event.clear()
        self._last_len = 0
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        if not self._is_tty:
            return
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        clear_len = max(self._last_len + 5, 50)
        try:
            sys.stdout.write("\r" + " " * clear_len + "\r")
            sys.stdout.flush()
        except Exception:
            pass

    def __enter__(self) -> "ThinkingIndicator":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


def query_observer_coder(
    messages: list,
    server: str,
    key: Optional[str] = None,
    user: Optional[str] = None,
    project: Optional[str] = None,
    temperature: float = 0.2,
    stream: bool = True,
    timeout: int = 180,
    show_indicator: bool = True,
) -> Tuple[str, Dict[str, Any]]:
    """
    Sends request to /v1/chat/completions for observer-coder-1.0.
    Returns (response_text, metadata_dict).
    If stream=True, streams tokens directly to stdout.
    Shows animated ThinkingIndicator until the first token arrives.
    """
    url = f"{server.rstrip('/')}/v1/chat/completions"
    payload = {
        "model": "observer-coder-1.0",
        "messages": messages,
        "temperature": temperature,
        "stream": stream,
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "ObserverCoder-CLI/1.0",
        "X-Session-Id": user or "cli-user",
        "X-Project": project or "cli-project",
    }
    if key:
        headers["Authorization"] = f"Bearer {key}"

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    full_text = []
    meta: Dict[str, Any] = {}
    indicator = ThinkingIndicator("Thinking...") if show_indicator else None

    if stream:
        started_streaming = False
        if indicator:
            indicator.start()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                meta["track"] = resp.headers.get("x-observer-track")
                meta["specialists"] = resp.headers.get("x-observer-specialists")
                meta["latency_ms"] = resp.headers.get("x-observer-latency-ms")

                for raw_line in resp:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if line.startswith("data: "):
                        chunk_str = line[6:]
                        if chunk_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(chunk_str)
                            delta = chunk["choices"][0]["delta"]
                            if "content" in delta:
                                piece = delta["content"]
                                if not started_streaming:
                                    if indicator:
                                        indicator.stop()
                                        indicator = None
                                    started_streaming = True
                                full_text.append(piece)
                                sys.stdout.write(piece)
                                sys.stdout.flush()
                        except Exception:
                            pass
            if indicator:
                indicator.stop()
                indicator = None
            print()
            return "".join(full_text), meta
        except urllib.error.HTTPError as err:
            if indicator:
                indicator.stop()
                indicator = None
            err_body = err.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {err.code}: {err_body}")
        finally:
            if indicator:
                indicator.stop()
    else:
        if indicator:
            indicator.start()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if indicator:
                    indicator.stop()
                    indicator = None
                meta["track"] = resp.headers.get("x-observer-track")
                meta["specialists"] = resp.headers.get("x-observer-specialists")
                meta["latency_ms"] = resp.headers.get("x-observer-latency-ms")
                body = json.loads(resp.read().decode("utf-8"))
                choice = body.get("choices", [{}])[0]
                text = choice.get("message", {}).get("content", "")
                if "observer_coordination" in body:
                    meta.update(body["observer_coordination"])
                if "usage" in body:
                    meta["usage"] = body["usage"]
                return text, meta
        except urllib.error.HTTPError as err:
            if indicator:
                indicator.stop()
                indicator = None
            err_body = err.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {err.code}: {err_body}")
        finally:
            if indicator:
                indicator.stop()


LANGUAGE_DEFAULT_FILES = {
    "html": "index.html",
    "htm": "index.html",
    "css": "style.css",
    "js": "script.js",
    "javascript": "script.js",
    "ts": "app.ts",
    "typescript": "app.ts",
    "py": "app.py",
    "python": "app.py",
    "json": "data.json",
    "sql": "schema.sql",
    "sh": "script.sh",
    "bash": "script.sh",
    "powershell": "script.ps1",
    "ps1": "script.ps1",
    "go": "main.go",
    "rust": "main.rs",
    "rs": "main.rs",
    "c": "main.c",
    "cpp": "main.cpp",
    "java": "Main.java",
    "md": "README.md",
    "markdown": "README.md",
    "yaml": "config.yaml",
    "yml": "config.yml",
}


def extract_code_blocks(text: str) -> list[Dict[str, Any]]:
    """
    Extract code blocks from markdown text with intelligent filename detection.
    Returns list of dicts: {"filename": str, "language": str, "code": str, "bytes": int}
    """
    pattern = r"```([a-zA-Z0-9_\-\.\+]+)?(?:[ \t]+([^\n\r`]+))?\r?\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    blocks = []

    for i, (lang_raw, fname_raw, code_raw) in enumerate(matches):
        lang = (lang_raw or "").strip().lower()
        fname = (fname_raw or "").strip() if fname_raw else ""

        # Normalize clean code
        code = code_raw.rstrip() + "\n"

        # Check if first line contains a filename comment (e.g. <!-- file: index.html --> or // file: app.js)
        if not fname:
            first_line = code.split("\n", 1)[0].strip()
            comment_match = re.search(
                r"(?:<!--|//|#|/\*)\s*(?:file(?:name)?|path):\s*([a-zA-Z0-9_\-\.\/\\]+)",
                first_line,
                re.IGNORECASE,
            )
            if comment_match:
                fname = comment_match.group(1).strip()
                code = "\n".join(code.split("\n")[1:]).lstrip()

        # If still no filename, try to infer from language
        if not fname:
            fname = LANGUAGE_DEFAULT_FILES.get(lang, f"snippet_{i+1}.txt" if not lang else f"snippet_{i+1}.{lang}")

        # Sanitize filename (prevent escape outside current workspace)
        clean_fname = os.path.basename(fname) if ".." in fname else fname

        blocks.append({
            "filename": clean_fname,
            "language": lang,
            "code": code,
            "bytes": len(code.encode("utf-8")),
        })

    return blocks


def write_code_blocks(blocks: list[Dict[str, Any]], target_file: Optional[str] = None) -> list[str]:
    """
    Write extracted code blocks to disk. Creates parent directories if needed.
    Returns list of written file paths.
    """
    written = []
    if target_file and blocks:
        block = blocks[0]
        p = Path(target_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(block["code"])
        written.append(str(p))
    else:
        for block in blocks:
            fname = block.get("filename")
            if not fname:
                continue
            p = Path(fname)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(block["code"])
            written.append(str(p))
    return written


def cmd_models(args: argparse.Namespace) -> int:

    """List the specialist models, fallback tiers, licenses, and tracks in ObserverCoder-1.0."""
    cfg = load_config()
    server = (getattr(args, "server", None) or get_server_url(cfg)).rstrip("/")

    print("\n" + "=" * 80)
    print(" ObserverCoder-1.0 - Multi-Model Coordination Engine Roster")
    print(f" Connected Server: {server}")
    print("=" * 80)

    header = f"{'Specialist':<18} {'Primary (Local)':<25} {'Fallback (Cloud)':<25} {'License':<10}"
    print(header)
    print("-" * 80)

    for spec in OBSERVER_CODER_CATALOG:
        print(f"{spec['specialist']:<18} {spec['primary']:<25} {spec['fallback']:<25} {spec['license']:<10}")
        print(f"  └─ Role: {spec['role']}")
        print(f"  └─ Activated by: {spec['track']}\n")

    print("-" * 80)
    print("Pipeline Tracks:")
    print("  • fast_coding        : Direct single-pass synthesis via Fast Coder (Qwen2.5-Coder)")
    print("  • two_pass_reasoning : DeepSeek-R1 / Qwen-Math Plan -> Qwen-Coder Implementation")
    print("  • vision             : Multimodal UI screenshot analysis via Qwen2-VL")
    print("=" * 80 + "\n")
    return 0


def cmd_code(args: argparse.Namespace) -> int:
    """Generate code or get technical answers via ObserverCoder-1.0."""
    cfg = load_config()
    server = (getattr(args, "server", None) or get_server_url(cfg)).rstrip("/")
    key = (
        getattr(args, "key", None)
        or cfg.get("api_key")
        or os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
    )
    user = getattr(args, "user", None) or cfg.get("user") or "cli-coder"
    project = getattr(args, "project", None) or cfg.get("project") or "cli-code"

    # Assemble prompt text
    prompt = getattr(args, "prompt", None) or ""

    # Check piped stdin if no prompt passed as argument
    if not prompt and not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()

    # Append file context if specified
    file_path = getattr(args, "file", None)
    if file_path:
        p = Path(file_path)
        if p.exists():
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                file_content = f.read()
            prompt = f"File Context (`{p.name}`):\n```\n{file_content}\n```\n\nTask: {prompt}"
        else:
            print(f"[!] Warning: File '{file_path}' not found.", file=sys.stderr)

    if not prompt:
        print('Error: No prompt provided. Usage: observer code "Your instruction here" [-f file.py]', file=sys.stderr)
        return 1

    # Check image attachment if specified
    image_path = getattr(args, "image", None)
    content_payload: Any = prompt
    if image_path:
        imp = Path(image_path)
        if imp.exists():
            mime, _ = mimetypes.guess_type(str(imp))
            mime = mime or "image/png"
            with open(imp, "rb") as imf:
                b64_data = base64.b64encode(imf.read()).decode("utf-8")
            content_payload = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64_data}"}}
            ]
        else:
            print(f"[!] Warning: Image file '{image_path}' not found.", file=sys.stderr)

    messages = [{"role": "user", "content": content_payload}]
    stream = not getattr(args, "no_stream", False)
    temperature = getattr(args, "temperature", 0.2)

    print(f"[ObserverCoder-1.0] Connecting to {server}...")

    t0 = time.perf_counter()
    try:
        text, meta = query_observer_coder(
            messages=messages,
            server=server,
            key=key,
            user=user,
            project=project,
            temperature=temperature,
            stream=stream,
        )
        if not stream:
            print(text)

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        track = meta.get("track") or "fast_coding"
        specialists = (
            meta.get("specialists")
            or (meta.get("specialists_used") and ", ".join(meta["specialists_used"]))
            or "fast_coder"
        )

        # Print badge summary
        print(f"\n[{'='*15} ObserverCoder-1.0 Trace {'='*15}]")
        print(f"Track       : {track}")
        print(f"Specialists : {specialists}")
        print(f"Duration    : {elapsed_ms} ms")
        if meta.get("usage"):
            u = meta["usage"]
            print(f"Tokens      : {u.get('prompt_tokens', 0)} in / {u.get('completion_tokens', 0)} out")
        print("=" * 55 + "\n")

        # Extract clean code blocks
        blocks = extract_code_blocks(text)

        # Save to output file if requested
        out_file = getattr(args, "output", None)
        if out_file:
            if blocks:
                write_code_blocks(blocks, target_file=out_file)
            else:
                with open(out_file, "w", encoding="utf-8") as out_f:
                    out_f.write(text)
            print(f"[+] Clean code written to: {out_file}")

        # Auto-write files if --write or --apply is specified
        if getattr(args, "write", False) or getattr(args, "apply", False):
            if blocks:
                written_paths = write_code_blocks(blocks)
                for wp in written_paths:
                    size = os.path.getsize(wp)
                    print(f"[+] Created/Updated: {wp} ({size:,} bytes)")
            else:
                print("[!] No code blocks found to write.")
        elif not out_file and blocks:
            file_names = ", ".join(b["filename"] for b in blocks)
            print(f"[Tip: Run with -w to automatically write detected file(s): {file_names}]")

        return 0
    except Exception as exc:
        print(f"\n[!] ObserverCoder Error: {exc}", file=sys.stderr)
        return 1


def cmd_chat(args: argparse.Namespace) -> int:
    """Start an interactive multi-turn terminal chat with ObserverCoder-1.0."""
    cfg = load_config()
    server = (getattr(args, "server", None) or get_server_url(cfg)).rstrip("/")
    key = (
        getattr(args, "key", None)
        or cfg.get("api_key")
        or os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
    )
    user = getattr(args, "user", None) or cfg.get("user") or "cli-chat"
    project = getattr(args, "project", None) or cfg.get("project") or "cli-chat"

    print("\n" + "=" * 65)
    print(" ObserverCoder-1.0 - Interactive Multi-Model Terminal")
    print(f" Server: {server}")
    print(" Type your code instructions or questions below.")
    print(" Commands: /write [name], /apply, /ls, /models, /clear, exit")
    print("=" * 65 + "\n")

    history: list = []

    while True:
        try:
            prompt = input("observer-coder> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting ObserverCoder.")
            break

        if not prompt:
            continue
        if prompt.lower() in ("exit", "quit", ":q"):
            print("Goodbye!")
            break
        if prompt.lower() == "/clear":
            history.clear()
            print("[+] Conversation context cleared.\n")
            continue
        if prompt.lower() in ("/models", "/specialists"):
            cmd_models(args)
            continue
        if prompt.lower() in ("/help", "?"):
            print("\nCommands:")
            print("  /write [filename]  - Write extracted code from last response to disk")
            print("  /apply             - Auto-extract and write all files to current directory")
            print("  /ls or /dir        - List files in current directory")
            print("  /models            - Show specialist model roster and tracks")
            print("  /clear             - Clear conversation history")
            print("  exit or quit       - Exit chat session\n")
            continue
        if prompt.lower() in ("/ls", "/dir"):
            files = [f.name for f in Path(".").iterdir() if not f.name.startswith(".")]
            print(f"\nFiles in {os.getcwd()}:")
            for fn in files[:30]:
                print(f"  • {fn}")
            print()
            continue
        if prompt.lower().startswith("/write") or prompt.lower().startswith("/save") or prompt.lower() == "/apply":
            parts = prompt.split(None, 1)
            target_name = parts[1].strip() if len(parts) > 1 else None
            if history:
                last_reply = ""
                for msg in reversed(history):
                    if msg.get("role") == "assistant":
                        last_reply = msg.get("content", "")
                        break
                blocks = extract_code_blocks(last_reply)
                if blocks:
                    written = write_code_blocks(blocks, target_file=target_name)
                    for wp in written:
                        print(f"[+] Created/Updated: {os.path.abspath(wp)} ({os.path.getsize(wp):,} bytes)")
                    print()
                else:
                    if target_name and last_reply:
                        with open(target_name, "w", encoding="utf-8") as f:
                            f.write(last_reply)
                        print(f"[+] Saved text response to {target_name}\n")
                    else:
                        print("[!] No code blocks found in the last response.\n")
            else:
                print("[!] No response to write yet.\n")
            continue

        history.append({"role": "user", "content": prompt})
        print()

        try:
            text, meta = query_observer_coder(
                messages=history,
                server=server,
                key=key,
                user=user,
                project=project,
                stream=True,
            )
            history.append({"role": "assistant", "content": text})
            track = meta.get("track") or "fast_coding"
            specialists = meta.get("specialists") or "fast_coder"
            print(f"\n[Track: {track} | Specialist: {specialists}]")

            # Check if code blocks were generated and offer to write them
            blocks = extract_code_blocks(text)
            if blocks:
                auto_write = getattr(args, "write", False) or getattr(args, "apply", False)
                if auto_write:
                    written_paths = write_code_blocks(blocks)
                    for wp in written_paths:
                        print(f"    [+] Created: {os.path.abspath(wp)} ({os.path.getsize(wp):,} bytes)")
                else:
                    file_list = ", ".join(b["filename"] for b in blocks)
                    first_fname = blocks[0]["filename"]
                    print(f"\n[Detected {len(blocks)} code file(s): {file_list}]")
                    try:
                        choice = input(
                            f"[?] Write to disk now? (Press ENTER to write '{first_fname}', or type custom filename, or 'n' to skip): "
                        ).strip()
                        if choice.lower() in ("", "y", "yes"):
                            written_paths = write_code_blocks(blocks)
                            for wp in written_paths:
                                print(f"    [+] Created: {os.path.abspath(wp)} ({os.path.getsize(wp):,} bytes)")
                        elif choice.lower() not in ("n", "no", "skip"):
                            written_paths = write_code_blocks(blocks, target_file=choice)
                            for wp in written_paths:
                                print(f"    [+] Created: {os.path.abspath(wp)} ({os.path.getsize(wp):,} bytes)")
                        else:
                            print("    [Skipped file creation. You can write it later with: /write]")
                    except (KeyboardInterrupt, EOFError):
                        pass
        except KeyboardInterrupt:
            print("\n[Generation cancelled by user]\n")
            if history:
                history.pop()
            continue
        except Exception as exc:
            print(f"\n[!] Error: {exc}\n", file=sys.stderr)
            if history:
                history.pop()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="observer",
        description="AI Model Observer CLI - Activate terminal proxying and coordinate ObserverCoder-1.0 models.",
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

    # code / ask / run (ObserverCoder-1.0 single-turn synthesis)
    p_code = subparsers.add_parser("code", aliases=["ask", "run"], help="Generate code or solve tasks with ObserverCoder-1.0")
    p_code.add_argument("prompt", nargs="?", default="", help="Instruction or coding task (or pipe via stdin)")
    p_code.add_argument("-f", "--file", help="File context to attach to prompt")
    p_code.add_argument("-i", "--image", help="Image or UI mockup file for visual inspection (Qwen2-VL)")
    p_code.add_argument("-o", "--output", help="Save generated response directly to file")
    p_code.add_argument("-w", "--write", "-a", "--apply", action="store_true", help="Auto-write detected code blocks directly to files in the current directory")
    p_code.add_argument("--no-stream", action="store_true", help="Disable live streaming output")
    p_code.add_argument("--temperature", type=float, default=0.2, help="Sampling temperature (default: 0.2)")
    p_code.add_argument("--server", help="Observer server URL")
    p_code.add_argument("--key", help="API key")
    p_code.add_argument("--user", help="Developer username")
    p_code.add_argument("--project", help="Project name")

    # chat (ObserverCoder-1.0 multi-turn interactive session)
    p_chat = subparsers.add_parser("chat", help="Start an interactive multi-turn coding session with ObserverCoder-1.0")
    p_chat.add_argument("-w", "--write", "-a", "--apply", action="store_true", help="Automatically write all generated code blocks without prompting")
    p_chat.add_argument("--server", help="Observer server URL")
    p_chat.add_argument("--key", help="API key")
    p_chat.add_argument("--user", help="Developer username")
    p_chat.add_argument("--project", help="Project name")


    # models / specialists
    p_models = subparsers.add_parser("models", aliases=["specialists"], help="List specialist models and routing tracks in ObserverCoder-1.0")
    p_models.add_argument("--server", help="Observer server URL")

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
    p_test.add_argument("--model", default="observer-coder-1.0", help="Model name to test (default: observer-coder-1.0)")
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

    if args.subcommand in ("code", "ask", "run"):
        return cmd_code(args)
    elif args.subcommand == "chat":
        return cmd_chat(args)
    elif args.subcommand in ("models", "specialists"):
        return cmd_models(args)
    elif args.subcommand == "activate":
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


def main_coder() -> int:
    """Dedicated entry point for 'observer-coder' command line executable."""
    recognized = {
        "code", "ask", "run", "chat", "models", "specialists",
        "activate", "usage", "dashboard", "test", "env", "--help", "-h"
    }
    if len(sys.argv) > 1 and sys.argv[1] not in recognized:
        sys.argv.insert(1, "code")
    elif len(sys.argv) == 1:
        sys.argv.append("chat")
    return main()


if __name__ == "__main__":
    sys.exit(main())

