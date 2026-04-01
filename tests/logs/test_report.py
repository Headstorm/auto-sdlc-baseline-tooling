import json
import pytest
from pathlib import Path
from auto_sdlc.logs.report import build_report, run_logs_report


def test_build_report_includes_user_id(sample_projects_dir):
    report = build_report(sample_projects_dir, user_id="alice@example.com")
    assert report["user_id"] == "alice@example.com"


def test_build_report_defaults_user_id(sample_projects_dir):
    report = build_report(sample_projects_dir)
    assert report["user_id"] is not None


def test_build_report_includes_behavioral_metrics(sample_projects_dir):
    report = build_report(sample_projects_dir)
    bm = report["behavioral_metrics"]
    assert "skill_invocation_ratio" in bm
    assert "sessions_per_day" in bm
    assert "avg_messages_per_session" in bm


def test_build_report_includes_maturity_scores(sample_projects_dir):
    report = build_report(sample_projects_dir)
    ms = report["maturity_scores"]
    assert "overall_level" in ms
    assert "overall_label" in ms
    assert len(ms["dimensions"]) == 5


def test_build_report_includes_project_breakdown(sample_projects_dir):
    report = build_report(sample_projects_dir)
    pb = report["project_breakdown"]
    assert isinstance(pb, list)
    assert len(pb) >= 1
    assert "project" in pb[0]
    assert "sessions" in pb[0]
    assert "total_tokens" in pb[0]


def test_build_report_no_qualitative_by_default(sample_projects_dir):
    report = build_report(sample_projects_dir)
    assert "qualitative_analysis" not in report


def test_run_logs_report_saves_to_default_path(sample_projects_dir, tmp_path):
    default_dir = tmp_path / "reports"
    report = run_logs_report(
        projects_dir=str(sample_projects_dir),
        output_path=None,
        user_id="test_user",
        _default_reports_dir=str(default_dir),
    )
    files = list((default_dir / "test_user").glob("*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text())
    assert data["user_id"] == "test_user"


def test_run_logs_report_output_path_overrides_default(sample_projects_dir, tmp_path):
    custom_path = tmp_path / "custom.json"
    run_logs_report(
        projects_dir=str(sample_projects_dir),
        output_path=str(custom_path),
        user_id="test_user",
    )
    assert custom_path.exists()
    data = json.loads(custom_path.read_text())
    assert "summary" in data


def test_run_logs_report_returns_report_dict(sample_projects_dir, tmp_path):
    result = run_logs_report(
        projects_dir=str(sample_projects_dir),
        output_path=str(tmp_path / "r.json"),
        user_id="u1",
    )
    assert result["summary"]["total_sessions"] == 1
