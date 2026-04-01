import json
import pytest
from pathlib import Path
from auto_sdlc.logs.team import build_team_report, build_team_report_from_dir, render_team_html


def _user_report(user_id, overall_level, sessions=5, tokens=100000):
    return {
        "user_id": user_id,
        "summary": {
            "total_sessions": sessions,
            "total_tokens": tokens,
            "avg_prompt_quality_score": 50,
        },
        "behavioral_metrics": {
            "skill_invocation_ratio": 0.20,
            "sessions_per_day": 1.0,
            "avg_messages_per_session": 8.0,
        },
        "maturity_scores": {
            "overall_level": overall_level,
            "overall_label": ["Beginner", "Basic", "Intermediate", "Advanced", "Expert"][overall_level],
            "dimensions": {
                "prompting_sophistication": {
                    "label": "Prompting Sophistication",
                    "description": "Quality of prompts",
                    "raw_value": 50,
                    "level": 3,
                    "level_label": "Advanced",
                },
                "tooling_adoption": {
                    "label": "Tooling Adoption",
                    "description": "Skill usage ratio",
                    "raw_value": 0.20,
                    "level": 2,
                    "level_label": "Intermediate",
                },
            },
        },
        "project_breakdown": [
            {"project": "myapp/src", "sessions": sessions, "total_tokens": tokens, "avg_prompt_quality": 50}
        ],
        "sessions": [],
    }


def test_build_team_report_structure():
    reports = [("alice", _user_report("alice", 2)), ("bob", _user_report("bob", 3))]
    result = build_team_report(reports)
    assert result["team_size"] == 2
    assert "overall_maturity_level" in result
    assert "overall_maturity_label" in result
    assert "members" in result
    assert "maturity_by_dimension" in result


def test_build_team_report_overall_is_avg():
    reports = [("a", _user_report("a", 2)), ("b", _user_report("b", 4))]
    result = build_team_report(reports)
    assert result["overall_maturity_level"] == 3  # round((2+4)/2)


def test_build_team_report_member_summary():
    reports = [("alice", _user_report("alice", 2))]
    result = build_team_report(reports)
    alice = result["members"][0]
    assert alice["user_id"] == "alice"
    assert alice["overall_maturity_level"] == 2
    assert alice["sessions"] == 5


def test_build_team_report_token_totals():
    reports = [
        ("a", _user_report("a", 2, tokens=100000)),
        ("b", _user_report("b", 2, tokens=200000)),
    ]
    result = build_team_report(reports)
    assert result["total_tokens"] == 300000


def test_build_team_report_from_dir(tmp_path):
    r1 = _user_report("alice", 2)
    r2 = _user_report("bob", 3)
    (tmp_path / "alice_2026.json").write_text(json.dumps(r1), encoding="utf-8")
    (tmp_path / "bob_2026.json").write_text(json.dumps(r2), encoding="utf-8")
    result = build_team_report_from_dir(str(tmp_path))
    assert result["team_size"] == 2


def test_render_team_html_returns_string():
    reports = [("alice", _user_report("alice", 2))]
    team_report = build_team_report(reports)
    html = render_team_html(team_report)
    assert isinstance(html, str)
    assert "<!DOCTYPE html>" in html
    assert "alice" in html
