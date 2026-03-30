import json
import pytest
from auto_sdlc.logs.report import build_report, run_logs_report


def test_build_report_structure(sample_projects_dir):
    report = build_report(sample_projects_dir)
    assert "generated_at" in report
    assert "projects_dir" in report
    assert "summary" in report
    assert "sessions" in report
    summary = report["summary"]
    assert "total_sessions" in summary
    assert "total_tokens" in summary
    assert "avg_prompt_quality_score" in summary


def test_build_report_sessions_list(sample_projects_dir):
    report = build_report(sample_projects_dir)
    assert len(report["sessions"]) == 1
    session = report["sessions"][0]
    assert "session_id" in session
    assert "token_usage" in session
    assert "prompt_scores" in session
    assert "metadata" in session


def test_build_report_prompt_scores(sample_projects_dir):
    report = build_report(sample_projects_dir)
    session = report["sessions"][0]
    assert len(session["prompt_scores"]) == 1
    # "Fix the login bug in src/auth.py line 42": file_ref(25)+line_ref(15)+action_verb(15) = 55
    assert session["prompt_scores"][0]["score"] == 55


def test_run_logs_report_writes_json(sample_projects_dir, tmp_path):
    output_path = tmp_path / "report.json"
    run_logs_report(projects_dir=str(sample_projects_dir), output_path=str(output_path))
    assert output_path.exists()
    data = json.loads(output_path.read_text())
    assert data["summary"]["total_sessions"] == 1


def test_run_logs_report_prints_when_no_output(sample_projects_dir, capsys):
    run_logs_report(projects_dir=str(sample_projects_dir), output_path=None)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "summary" in data
