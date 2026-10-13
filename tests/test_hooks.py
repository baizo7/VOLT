import json
import pytest
from unittest.mock import patch, MagicMock
from hooks.git_tracker import detect_task_id, get_git_metadata, report_git_outcome
from hooks.ci_reporter import parse_test_output, send_outcome, run_and_report


def test_detect_task_id_from_env(monkeypatch):
    monkeypatch.setenv("OBSERVER_TASK_ID", "task_custom_env")
    assert detect_task_id() == "task_custom_env"


def test_detect_task_id_from_marker_file(tmp_path, monkeypatch):
    monkeypatch.delenv("OBSERVER_TASK_ID", raising=False)
    marker = tmp_path / ".observer_task"
    marker.write_text("task_from_file", encoding="utf-8")
    assert detect_task_id(repo_root=str(tmp_path)) == "task_from_file"


def test_detect_task_id_from_commit_msg(monkeypatch):
    monkeypatch.delenv("OBSERVER_TASK_ID", raising=False)
    with patch("hooks.git_tracker.run_git", return_git_mock("[task_456] implement feature")):
        assert detect_task_id() == "task_456"


def return_git_mock(commit_msg: str):
    def _mock(args):
        if "--format=%B" in args:
            return commit_msg
        if "--abbrev-ref" in args:
            return "master"
        return ""
    return _mock


def test_parse_test_output_pytest():
    output = "===== 37 passed, 3 failed, 1 skipped in 2.14s ====="
    metrics = parse_test_output(output)
    assert metrics["passed"] == 37
    assert metrics["failed"] == 3
    assert metrics["skipped"] == 1


def test_parse_test_output_jest():
    output = "Tests:  2 failed, 15 passed, 17 total\nSnapshots: 0 total"
    metrics = parse_test_output(output)
    assert metrics["passed"] == 15
    assert metrics["failed"] == 2


def test_report_git_outcome_sends_payload():
    with patch("hooks.git_tracker.get_git_metadata", return_value={"commit": "abc", "branch": "main"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            success = report_git_outcome(task_id="task_test_git", status="accepted")
            assert success is True
            assert mock_urlopen.called


def test_send_outcome_ci_reporter():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        success = send_outcome(
            task_id="task_ci_1",
            kind="test",
            status="pass",
            details={"passed": 10, "failed": 0}
        )
        assert success is True


def test_run_and_report_success():
    with patch("hooks.ci_reporter.send_outcome") as mock_send:
        # Run a simple echo command
        import sys
        code = run_and_report([sys.executable, "-c", "print('10 passed')"], task_id="task_1", kind="test")
        assert code == 0
        assert mock_send.called
        call_args = mock_send.call_args[1]
        assert call_args["status"] == "pass"
        assert call_args["details"]["passed"] == 10
