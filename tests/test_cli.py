"""
Unit tests for ObserverCoder CLI package.
"""
import io
import json
import sys
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
    mock_args.server = "https://ai-observer-8wcb.onrender.com"
    ret = cmd_models(mock_args)
    assert ret == 0
    captured = capsys.readouterr().out
    assert "ObserverCoder-1.0 - Multi-Model Coordination Engine Roster" in captured
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
    assert "ObserverCoder-1.0 - Interactive Multi-Model Terminal" in captured
    assert "Goodbye!" in captured


def test_main_coder_argv_shorthand():
    with patch.object(sys, "argv", ["observer-coder", "Write quicksort in python"]):
        with patch("cli.main.cmd_code", return_value=0) as mock_code:
            ret = main_coder()
            assert ret == 0
            assert mock_code.called
            called_args = mock_code.call_args[0][0]
            assert called_args.prompt == "Write quicksort in python"
