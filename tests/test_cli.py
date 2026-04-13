import json
import tempfile
from pathlib import Path
from click.testing import CliRunner
from auto_sdlc.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "logs" in result.output
    assert "init" in result.output
    assert "audit" in result.output


def test_init_stub_runs():
    runner = CliRunner()
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0
    assert "not yet implemented" in result.output


def test_audit_stub_runs():
    runner = CliRunner()
    result = runner.invoke(cli, ["audit"])
    assert result.exit_code == 0
    assert "not yet implemented" in result.output


def test_logs_command_with_custom_dir(sample_projects_dir, tmp_path):
    output_file = tmp_path / "report.json"
    runner = CliRunner()
    result = runner.invoke(cli, [
        "logs",
        "--projects-dir", str(sample_projects_dir),
        "--output", str(output_file),
    ])
    assert result.exit_code == 0
    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert data["summary"]["total_sessions"] == 1


def test_logs_command_output_flag(sample_projects_dir, tmp_path):
    output_file = tmp_path / "out.json"
    runner = CliRunner()
    result = runner.invoke(cli, [
        "logs",
        "--projects-dir", str(sample_projects_dir),
        "--output", str(output_file),
    ])
    assert result.exit_code == 0
    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert "summary" in data


def test_report_command_help():
    """Test that report command help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--help"])
    assert result.exit_code == 0
    assert "Generate an AI Maturity Report" in result.output
    assert "--user-id" in result.output
    assert "--project-path" in result.output
    assert "--report-type" in result.output


def test_report_command_missing_required_args():
    """Test that report command fails without required arguments."""
    runner = CliRunner()
    result = runner.invoke(cli, ["report"])
    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


def test_report_command_team_report():
    """Test team report generation via CLI."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as project_tmpdir:
        project_path = Path(project_tmpdir)

        # Create minimal project structure
        logs_dir = project_path / "logs"
        logs_dir.mkdir()

        session_file = logs_dir / "session_20260401_100000.json"
        session_data = {
            "session_id": "test_session_001",
            "start_timestamp": "2026-04-01T10:00:00Z",
            "events": [{"type": "message", "content": "Hello"}]
        }
        session_file.write_text(json.dumps(session_data))

        (project_path / "CLAUDE.md").write_text("# CLAUDE.md\n## AI Tool Adoption\nUsing Claude")

        with tempfile.TemporaryDirectory() as output_tmpdir:
            result = runner.invoke(cli, [
                "report",
                "--user-id", "test_team",
                "--project-path", str(project_path),
                "--output-dir", output_tmpdir,
                "--report-type", "team",
            ])

            assert result.exit_code == 0
            assert "Report generated successfully" in result.output
            assert "test_team" in result.output

            # Check that PDF was created
            pdfs = list(Path(output_tmpdir).glob("*.pdf"))
            assert len(pdfs) == 1
            assert "test_team" in pdfs[0].name


def test_report_command_individual_report():
    """Test individual report generation via CLI."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as project_tmpdir:
        project_path = Path(project_tmpdir)

        # Create minimal project structure
        logs_dir = project_path / "logs"
        logs_dir.mkdir()

        session_file = logs_dir / "session_20260401_100000.json"
        session_data = {
            "session_id": "test_session_001",
            "start_timestamp": "2026-04-01T10:00:00Z",
            "events": [{"type": "message", "content": "Hello"}]
        }
        session_file.write_text(json.dumps(session_data))

        (project_path / "CLAUDE.md").write_text("# CLAUDE.md\n## AI Tool Adoption\nUsing Claude")

        with tempfile.TemporaryDirectory() as output_tmpdir:
            result = runner.invoke(cli, [
                "report",
                "--user-id", "developer_1",
                "--project-path", str(project_path),
                "--output-dir", output_tmpdir,
                "--report-type", "individual",
            ])

            assert result.exit_code == 0
            assert "Report generated successfully" in result.output
            assert "developer_1" in result.output
            assert "individual" in result.output

            # Check that PDF was created
            pdfs = list(Path(output_tmpdir).glob("*.pdf"))
            assert len(pdfs) == 1
            assert "developer_1" in pdfs[0].name


def test_report_command_invalid_project_path():
    """Test that report command fails with non-existent project path."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as output_tmpdir:
        result = runner.invoke(cli, [
            "report",
            "--user-id", "test",
            "--project-path", "/nonexistent/path",
            "--output-dir", output_tmpdir,
        ])

        assert result.exit_code != 0
        assert "File not found" in result.output or "does not exist" in result.output
