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


def test_render_team_html_with_dimension_details():
    """Test that team dimensions have collapsible details sections."""
    reports = [("alice", _user_report("alice", 2)), ("bob", _user_report("bob", 3))]
    team_report = build_team_report(reports)
    report_dicts = [r for _, r in reports]
    html = render_team_html(team_report, report_dicts)
    assert "<details class='dimension-details'>" in html
    assert "<summary" in html
    assert "▼</span>" in html


def test_render_team_html_contains_team_metrics():
    """Test that team HTML includes aggregated team metrics."""
    reports = [("alice", _user_report("alice", 2)), ("bob", _user_report("bob", 3))]
    team_report = build_team_report(reports)
    report_dicts = [r for _, r in reports]
    html = render_team_html(team_report, report_dicts)
    assert "Team Avg Prompt Quality" in html
    assert "Team Avg Skill Ratio" in html
    # Verify dimension dropdowns are present with metrics
    assert "<details class='dimension-details'>" in html


def test_render_team_html_prompting_sophistication_metrics():
    """Test prompting sophistication dimension metrics in team report."""
    reports = [("alice", _user_report("alice", 2)), ("bob", _user_report("bob", 3))]
    team_report = build_team_report(reports)
    report_dicts = [r for _, r in reports]
    html = render_team_html(team_report, report_dicts)
    # Should have prompting sophistication details
    assert "Prompting Sophistication" in html
    assert "Team Avg Prompt Quality" in html
    assert "Developers at Level 3+" in html


def test_render_team_html_tooling_adoption_metrics():
    """Test tooling adoption dimension metrics in team report."""
    reports = [("alice", _user_report("alice", 2)), ("bob", _user_report("bob", 3))]
    team_report = build_team_report(reports)
    report_dicts = [r for _, r in reports]
    html = render_team_html(team_report, report_dicts)
    # Should have tooling adoption details
    assert "Tooling Adoption" in html
    assert "Team Avg Skill Ratio" in html
    assert "Developers Using Tools" in html


def test_render_team_html_usage_frequency_metrics():
    """Test usage frequency dimension metrics in team report."""
    r1 = _user_report("alice", 2)
    r1["maturity_scores"]["dimensions"]["usage_frequency"] = {
        "label": "Usage Frequency",
        "level": 3,
        "level_label": "Advanced",
    }
    r2 = _user_report("bob", 3)
    r2["maturity_scores"]["dimensions"]["usage_frequency"] = {
        "label": "Usage Frequency",
        "level": 2,
        "level_label": "Intermediate",
    }
    reports = [("alice", r1), ("bob", r2)]
    team_report = build_team_report(reports)
    report_dicts = [r for _, r in reports]
    html = render_team_html(team_report, report_dicts)
    # Should have usage frequency details
    assert "Usage Frequency" in html
    assert "Team Avg Sessions/Day" in html
    assert "Range (Min-Max)" in html


def test_render_team_html_without_user_reports():
    """Test that team HTML renders without user_reports parameter (backward compatibility)."""
    reports = [("alice", _user_report("alice", 2))]
    team_report = build_team_report(reports)
    # Should work even without passing user_reports
    html = render_team_html(team_report)
    assert isinstance(html, str)
    assert "<!DOCTYPE html>" in html
    assert "alice" in html


def test_render_team_html_escaping_xss_prevention():
    """Test that team HTML escapes special characters to prevent XSS."""
    reports = [
        ("alice<script>", _user_report("alice<script>", 2)),
        ("bob&name", _user_report("bob&name", 3)),
    ]
    team_report = build_team_report(reports)
    report_dicts = [r for _, r in reports]
    html = render_team_html(team_report, report_dicts)
    # Verify special characters are escaped
    assert "&lt;script&gt;" in html
    assert "&amp;" in html
    assert "<script>" not in html
    assert "Auto-SDLC Team Report" in html


def test_render_team_html_with_context_efficiency_dimension():
    """Test context efficiency metrics when dimension is present."""
    r1 = _user_report("alice", 2)
    r1["maturity_scores"]["dimensions"]["context_efficiency"] = {
        "label": "Context Efficiency",
        "level": 2,
        "level_label": "Intermediate",
    }
    r1["summary"]["total_cache_read_tokens"] = 50000
    r1["summary"]["total_tokens"] = 100000

    r2 = _user_report("bob", 3)
    r2["maturity_scores"]["dimensions"]["context_efficiency"] = {
        "label": "Context Efficiency",
        "level": 3,
        "level_label": "Advanced",
    }
    r2["summary"]["total_cache_read_tokens"] = 60000
    r2["summary"]["total_tokens"] = 120000

    reports = [("alice", r1), ("bob", r2)]
    team_report = build_team_report(reports)
    report_dicts = [r for _, r in reports]
    html = render_team_html(team_report, report_dicts)
    assert "Context Efficiency" in html
    assert "Team Cache Hit Ratio" in html
    assert "Cache Read Tokens" in html
