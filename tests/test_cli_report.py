import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from auto_sdlc.cli import report


def test_report_command_help_shows_new_options():
    result = subprocess.run(
        [sys.executable, "-m", "auto_sdlc.cli", "report", "--help"],
        capture_output=True, text=True
    )
    assert "--team-name" in result.stdout
    assert "--user-name" in result.stdout
    assert "--report-type" in result.stdout


def test_report_command_accepts_team_name_flag(tmp_path):
    """Individual report with --team-name and --user-name exits 0 when ReportService succeeds."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "session.jsonl").write_text(
        '{"type":"system","subtype":"turn_duration","durationMs":5000,"sessionId":"abc",'
        '"message_count":10,"cwd":"/tmp","gitBranch":"main"}\n'
    )

    fake_report = MagicMock()
    fake_pdf = tmp_path / "reports" / "testteam" / "report.pdf"

    runner = CliRunner()
    with patch("auto_sdlc.cli.ReportService") as MockService:
        instance = MockService.return_value
        instance.generate_report.return_value = (fake_report, fake_pdf)

        result = runner.invoke(
            report,
            [
                str(logs_dir),
                "--team-name", "testteam",
                "--user-name", "testuser",
                "--report-type", "individual",
                "--output-dir", str(tmp_path / "reports"),
            ],
        )

    assert result.exit_code == 0, f"Unexpected exit code {result.exit_code}:\n{result.output}"
    instance.generate_report.assert_called_once()


def test_report_command_accepts_team_type(tmp_path):
    """Team report with --team-name exits 0 when ReportService succeeds."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "session.jsonl").write_text(
        '{"type":"system","subtype":"turn_duration","durationMs":5000,"sessionId":"abc",'
        '"message_count":10,"cwd":"/tmp","gitBranch":"main"}\n'
    )

    fake_report = MagicMock()
    fake_pdf = tmp_path / "reports" / "testteam" / "report.pdf"

    runner = CliRunner()
    with patch("auto_sdlc.cli.ReportService") as MockService:
        instance = MockService.return_value
        instance.generate_report.return_value = (fake_report, fake_pdf)

        result = runner.invoke(
            report,
            [
                str(logs_dir),
                "--team-name", "testteam",
                "--report-type", "team",
                "--output-dir", str(tmp_path / "reports"),
            ],
        )

    assert result.exit_code == 0, f"Unexpected exit code {result.exit_code}:\n{result.output}"
    instance.generate_report.assert_called_once()


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
