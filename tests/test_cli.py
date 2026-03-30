import json
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


def test_logs_command_with_custom_dir(sample_projects_dir):
    runner = CliRunner()
    result = runner.invoke(cli, ["logs", "--projects-dir", str(sample_projects_dir)])
    assert result.exit_code == 0
    data = json.loads(result.output)
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
