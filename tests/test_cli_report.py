import subprocess
import sys
from pathlib import Path


def test_report_command_help_shows_new_options():
    result = subprocess.run(
        [sys.executable, "-m", "auto_sdlc.cli", "report", "--help"],
        capture_output=True, text=True
    )
    assert "--team-name" in result.stdout
    assert "--user-name" in result.stdout
    assert "--report-type" in result.stdout


def test_report_command_accepts_team_name_flag(tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "session.jsonl").write_text(
        '{"type":"system","subtype":"turn_duration","durationMs":5000,"sessionId":"abc",'
        '"message_count":10,"cwd":"/tmp","gitBranch":"main"}\n'
    )

    result = subprocess.run(
        [
            sys.executable, "-m", "auto_sdlc.cli", "report",
            str(logs_dir),
            "--team-name", "testteam",
            "--user-name", "testuser",
            "--report-type", "individual",
            "--output-dir", str(tmp_path / "reports"),
        ],
        capture_output=True, text=True,
    )
    assert "No such option" not in result.stderr
    assert "Error: Missing argument" not in result.stderr


def test_report_command_accepts_team_type(tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "session.jsonl").write_text(
        '{"type":"system","subtype":"turn_duration","durationMs":5000,"sessionId":"abc",'
        '"message_count":10,"cwd":"/tmp","gitBranch":"main"}\n'
    )

    result = subprocess.run(
        [
            sys.executable, "-m", "auto_sdlc.cli", "report",
            str(logs_dir),
            "--team-name", "testteam",
            "--report-type", "team",
            "--output-dir", str(tmp_path / "reports"),
        ],
        capture_output=True, text=True,
    )
    assert "No such option" not in result.stderr
    assert "Error: Missing argument" not in result.stderr


def test_report_rejects_invalid_report_type(tmp_path):
    result = subprocess.run(
        [
            sys.executable, "-m", "auto_sdlc.cli", "report",
            str(tmp_path),
            "--team-name", "t",
            "--report-type", "invalid",
        ],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "invalid" in result.stderr.lower() or "invalid" in result.stdout.lower()
