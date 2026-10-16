"""
Unit tests for ObserverCoder CLI package.
"""
import io
import json
import os
import sys
import time
from unittest.mock import MagicMock, patch
import pytest

from cli.main import (
    cmd_models,
    cmd_code,
    cmd_chat,
    main,
    main_coder,
    OBSERVER_CODER_CATALOG,
    query_observer_coder,
    ThinkingIndicator,
)


def test_models_catalog_definition():
    assert len(OBSERVER_CODER_CATALOG) == 5
    specialist_names = [s["specialist"] for s in OBSERVER_CODER_CATALOG]
    assert "fast_coder" in specialist_names
    assert "heavy_coder" in specialist_names
    assert "deep_reasoner" in specialist_names
    assert "math_specialist" in specialist_names
    assert "vision_specialist" in specialist_names


def test_cmd_models_output(capsys):
    mock_args = MagicMock()
    mock_args.server = "https://volt-ai-lmgz.onrender.com"
    ret = cmd_models(mock_args)
    assert ret == 0
    captured = capsys.readouterr().out
    assert "VOLT-AI - Multi-Model Coordination Engine Roster" in captured
    assert "fast_coder" in captured
    assert "deep_reasoner" in captured
    assert "two_pass_reasoning" in captured


def test_cmd_code_no_prompt_fails(capsys):
    mock_args = MagicMock()
    mock_args.prompt = ""
    mock_args.file = None
    mock_args.image = None
    with patch("sys.stdin.isatty", return_value=True):
        ret = cmd_code(mock_args)
    assert ret == 1
    err = capsys.readouterr().err
    assert "Error: No prompt provided" in err


def test_cmd_code_streaming_mocked(capsys):
    mock_args = MagicMock()
    mock_args.prompt = "Write hello world in python"
    mock_args.file = None
    mock_args.image = None
    mock_args.output = None
    mock_args.no_stream = False
    mock_args.temperature = 0.0
    mock_args.server = "http://testserver"
    mock_args.key = "sk-test"
    mock_args.user = "tester"
    mock_args.project = "testproj"

    # Simulate SSE response
    sse_lines = [
        b'data: {"id":"1","choices":[{"delta":{"role":"assistant"}}]}\n\n',
        b'data: {"id":"1","choices":[{"delta":{"content":"print(\'hello world\')"}}]}\n\n',
        b'data: [DONE]\n\n'
    ]
    mock_resp = MagicMock()
    mock_resp.headers = {
        "x-observer-track": "fast_coding",
        "x-observer-specialists": "fast_coder",
        "x-observer-latency-ms": "120"
    }
    mock_resp.__iter__.return_value = iter(sse_lines)
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        ret = cmd_code(mock_args)

    assert ret == 0
    captured = capsys.readouterr().out
    assert "print('hello world')" in captured
    assert "Track       : fast_coding" in captured
    assert "Specialists : fast_coder" in captured


def test_cmd_code_with_file_context(tmp_path, capsys):
    test_file = tmp_path / "hello.py"
    test_file.write_text("def sample(): pass", encoding="utf-8")

    mock_args = MagicMock()
    mock_args.prompt = "Refactor this"
    mock_args.file = str(test_file)
    mock_args.image = None
    mock_args.output = None
    mock_args.no_stream = True
    mock_args.temperature = 0.2
    mock_args.server = "http://testserver"
    mock_args.key = None
    mock_args.user = None
    mock_args.project = None

    mock_resp = MagicMock()
    mock_resp.headers = {
        "x-observer-track": "fast_coding",
        "x-observer-specialists": "fast_coder",
        "x-observer-latency-ms": "100"
    }
    mock_payload = {
        "choices": [{"message": {"content": "def sample_refactored(): return True"}}],
        "usage": {"prompt_tokens": 15, "completion_tokens": 8},
        "observer_coordination": {"track": "fast_coding", "specialists_used": ["fast_coder"]}
    }
    mock_resp.read.return_value = json.dumps(mock_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        ret = cmd_code(mock_args)
        req = mock_urlopen.call_args[0][0]
        sent_body = json.loads(req.data.decode("utf-8"))
        sent_prompt = sent_body["messages"][0]["content"]
        assert "File Context (`hello.py`)" in sent_prompt
        assert "def sample(): pass" in sent_prompt

    assert ret == 0
    captured = capsys.readouterr().out
    assert "def sample_refactored(): return True" in captured


def test_cmd_chat_exit(capsys):
    mock_args = MagicMock()
    mock_args.server = "http://testserver"
    mock_args.key = None
    mock_args.user = None
    mock_args.project = None

    with patch("builtins.input", side_effect=["exit"]):
        ret = cmd_chat(mock_args)
    assert ret == 0
    captured = capsys.readouterr().out
    assert "VOLT-AI - Interactive Multi-Model Terminal" in captured
    assert "Goodbye!" in captured


def test_main_coder_argv_shorthand():
    with patch.object(sys, "argv", ["observer-coder", "Write quicksort in python"]):
        with patch("cli.main.cmd_code", return_value=0) as mock_code:
            ret = main_coder()
            assert ret == 0
            assert mock_code.called
            called_args = mock_code.call_args[0][0]
            assert called_args.prompt == "Write quicksort in python"


def test_extract_code_blocks():
    from cli.main import extract_code_blocks

    sample = """
Here is your coffee shop webpage:

```html index.html
<!DOCTYPE html>
<html><body><h1>Coffee</h1></body></html>
```

And your style:

```css style.css
body { background: #333; }
```
"""
    blocks = extract_code_blocks(sample)
    assert len(blocks) == 2
    assert blocks[0]["filename"] == "index.html"
    assert blocks[0]["language"] == "html"
    assert "<h1>Coffee</h1>" in blocks[0]["code"]

    assert blocks[1]["filename"] == "style.css"
    assert blocks[1]["language"] == "css"
    assert "background: #333;" in blocks[1]["code"]


def test_extract_code_blocks_fallback_language():
    from cli.main import extract_code_blocks

    sample = """
```python
def add(a, b):
    return a + b
```
"""
    blocks = extract_code_blocks(sample)
    assert len(blocks) == 1
    assert blocks[0]["filename"] == "app.py"
    assert "def add(a, b):" in blocks[0]["code"]


def test_write_code_blocks(tmp_path):
    from cli.main import write_code_blocks

    blocks = [
        {"filename": "coffee.html", "code": "<h1>Coffee Shop</h1>\n"},
        {"filename": "sub/style.css", "code": "body { color: brown; }\n"},
    ]
    orig_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        written = write_code_blocks(blocks)
        assert len(written) == 2
        assert (tmp_path / "coffee.html").exists()
        assert (tmp_path / "coffee.html").read_text(encoding="utf-8") == "<h1>Coffee Shop</h1>\n"
        assert (tmp_path / "sub" / "style.css").exists()
    finally:
        os.chdir(orig_cwd)


def test_cmd_chat_write_command(tmp_path):
    orig_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        mock_args = MagicMock()
        mock_args.server = "http://testserver"
        mock_args.key = None
        mock_args.user = None
        mock_args.project = None
        mock_args.write = False
        mock_args.apply = False

        html_reply = "Sure! Here is the code:\n```html index.html\n<!DOCTYPE html><html><body>Coffee</body></html>\n```\nEnjoy!"
        # In chat session: user asks, model replies, then user types /write, then exit
        with patch("cli.main.query_observer_coder", return_value=(html_reply, {"track": "fast_coding", "specialists": "fast_coder"})):
            with patch("builtins.input", side_effect=[
                "build coffee website",
                "y",  # accept write prompt
                "exit"
            ]):
                ret = cmd_chat(mock_args)
                assert ret == 0
                assert (tmp_path / "index.html").exists()
                assert "Coffee" in (tmp_path / "index.html").read_text(encoding="utf-8")
    finally:
        os.chdir(orig_cwd)


def test_thinking_indicator_non_tty():
    ind = ThinkingIndicator("Thinking...")
    ind._is_tty = False
    ind.start()
    assert ind._thread is None
    ind.stop()


def test_thinking_indicator_lifecycle():
    stream = io.StringIO()
    ind = ThinkingIndicator("Testing...", interval=0.01)
    ind._is_tty = True
    with patch("sys.stdout", stream):
        ind.start()
        time.sleep(0.05)
        ind.stop()
    output = stream.getvalue()
    assert "Testing..." in output
    assert "\r" in output


def test_thinking_indicator_context_manager():
    ind = ThinkingIndicator("Testing...", interval=0.01)
    ind._is_tty = False
    with ind:
        pass
    assert ind._thread is None


def test_query_observer_coder_streaming_with_indicator():
    sse_lines = [
        b'data: {"choices":[{"delta":{"content":"Hello world"}}]}\n\n',
        b'data: [DONE]\n\n'
    ]
    mock_resp = MagicMock()
    mock_resp.headers = {
        "x-observer-track": "fast_coding",
        "x-observer-specialists": "fast_coder",
        "x-observer-latency-ms": "50",
    }
    mock_resp.__iter__.return_value = iter(sse_lines)
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        text, meta = query_observer_coder(
            messages=[{"role": "user", "content": "Hi"}],
            server="http://testserver",
            stream=True,
            show_indicator=True,
        )
    assert text == "Hello world"
    assert meta["track"] == "fast_coding"


def test_cmd_usage_personal(capsys):
    from cli.main import cmd_usage
    mock_args = MagicMock()
    mock_args.server = "http://testserver"
    mock_args.user = "dev1"
    mock_args.project = "proj1"
    mock_args.all = False
    mock_args.token = None

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps([
        {"model": "gpt-4o", "calls": 5, "avg_latency_ms": 200, "input_tokens": 100, "output_tokens": 50, "passes": 5, "fails": 0}
    ]).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        ret = cmd_usage(mock_args)
    assert ret == 0
    out = capsys.readouterr().out
    assert "gpt-4o" in out
    assert "Developer: dev1" in out


def test_cmd_usage_all_unauthorized_message(capsys):
    import urllib.error
    from cli.main import cmd_usage
    mock_args = MagicMock()
    mock_args.server = "http://testserver"
    mock_args.user = None
    mock_args.project = None
    mock_args.all = True
    mock_args.token = None

    err_fp = io.BytesIO(b'{"error": "unauthorized: admin privileges required"}')
    http_err = urllib.error.HTTPError("http://testserver/stats", 401, "Unauthorized", {}, err_fp)

    with patch("urllib.request.urlopen", side_effect=http_err):
        ret = cmd_usage(mock_args)
    assert ret == 1
    err = capsys.readouterr().err
    assert "Viewing organization-wide usage across all developers requires Administrator privileges" in err
    assert "--token <YOUR_ADMIN_KEY>" in err


def test_cmd_usage_all_with_token(capsys):
    from cli.main import cmd_usage
    mock_args = MagicMock()
    mock_args.server = "http://testserver"
    mock_args.user = None
    mock_args.project = None
    mock_args.all = True
    mock_args.token = "valid-secret"

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps([
        {"model": "claude-3-5", "calls": 12, "avg_latency_ms": 150, "input_tokens": 500, "output_tokens": 200, "passes": 10, "fails": 2}
    ]).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        ret = cmd_usage(mock_args)
        req = mock_urlopen.call_args[0][0]
        assert req.headers.get("X-admin-token") == "valid-secret"

    assert ret == 0
    out = capsys.readouterr().out
    assert "claude-3-5" in out
    assert "Developer: Entire Team" in out


