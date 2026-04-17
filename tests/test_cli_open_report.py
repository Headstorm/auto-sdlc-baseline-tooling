import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from auto_sdlc.cli import open_report


def test_open_report_command_help():
    result = subprocess.run(
        [sys.executable, "-m", "auto_sdlc.cli", "open-report", "--help"],
        capture_output=True, text=True
    )
    assert "--team-name" in result.stdout
    assert "--user-name" in result.stdout
    assert "--id" in result.stdout


def test_open_report_by_team_and_user(tmp_path):
    """Open most recent report for a specific team/user."""
    pdf_path = tmp_path / "report.pdf"
    pdf_path.touch()

    runner = CliRunner()
    with patch("auto_sdlc.cli._get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.get_reports_by_team.return_value = [
            {"id": 1, "team_name": "testteam", "user_name": "testuser", "pdf_path": str(pdf_path)}
        ]

        result = runner.invoke(
            open_report,
            [
                "--team-name", "testteam",
                "--user-name", "testuser",
            ],
        )

    assert result.exit_code == 0, f"Unexpected exit code {result.exit_code}:\n{result.output}"
    assert "Opening:" in result.output


def test_open_report_by_id(tmp_path):
    """Open a specific report by ID."""
    pdf_path = tmp_path / "report.pdf"
    pdf_path.touch()

    runner = CliRunner()
    with patch("auto_sdlc.cli._get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.get_all_reports.return_value = [
            {"id": 3, "team_name": "testteam", "user_name": "testuser", "pdf_path": str(pdf_path)}
        ]

        result = runner.invoke(
            open_report,
            [
                "--id", "3",
            ],
        )

    assert result.exit_code == 0, f"Unexpected exit code {result.exit_code}:\n{result.output}"
    assert "Opening:" in result.output


def test_open_report_fails_when_no_reports():
    """Error when no reports found."""
    runner = CliRunner()
    with patch("auto_sdlc.cli._get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.get_reports_by_team.return_value = []

        result = runner.invoke(
            open_report,
            [
                "--team-name", "nobody",
            ],
        )

    assert result.exit_code != 0
    assert "No reports found" in result.output


def test_open_report_fails_when_pdf_missing(tmp_path):
    """Error when PDF file no longer exists."""
    runner = CliRunner()
    with patch("auto_sdlc.cli._get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.get_reports_by_team.return_value = [
            {"id": 1, "team_name": "testteam", "user_name": "testuser", "pdf_path": "/nonexistent/report.pdf"}
        ]

        result = runner.invoke(
            open_report,
            [
                "--team-name", "testteam",
                "--user-name", "testuser",
            ],
        )

    assert result.exit_code != 0
    assert "not found" in result.output.lower()
