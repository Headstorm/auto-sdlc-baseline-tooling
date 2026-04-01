import pytest
from auto_sdlc.logs.render_html import render_individual_html


def _sample_report():
    """Generate a sample report matching the actual report.py output structure."""
    return {
        "user_id": "user_12345",
        "generated_at": "2024-01-15T10:00:00+00:00",
        "summary": {
            "total_sessions": 42,
            "total_tokens": 125000,
            "avg_prompt_quality_score": 65.0,
        },
        "behavioral_metrics": {
            "total_user_messages": 300,
            "total_skill_invocations": 30,
            "skill_invocation_ratio": 0.09,
            "sessions_per_day": 2.1,
            "avg_messages_per_session": 7.1,
        },
        "maturity_scores": {
            "overall_level": 3,
            "overall_label": "Advanced",
            "dimensions": {
                "prompting_sophistication": {
                    "label": "Prompting Sophistication",
                    "level": 3,
                    "level_label": "Advanced",
                },
                "tooling_adoption": {
                    "label": "Tooling Adoption",
                    "level": 2,
                    "level_label": "Intermediate",
                },
                "usage_frequency": {
                    "label": "Usage Frequency",
                    "level": 3,
                    "level_label": "Advanced",
                },
                "session_depth": {
                    "label": "Session Depth",
                    "level": 2,
                    "level_label": "Intermediate",
                },
            },
        },
        "project_breakdown": [
            {"project": "Project A", "sessions": 20, "total_tokens": 50000, "avg_prompt_quality": 70.0},
            {"project": "Project B", "sessions": 15, "total_tokens": 45000, "avg_prompt_quality": 60.0},
            {"project": "Project C", "sessions": 7, "total_tokens": 30000, "avg_prompt_quality": None},
        ],
        "qualitative_analysis": {
            "narrative": "User demonstrates strong technical foundation and consistent improvement in testing practices.",
            "workflow_patterns": {
                "workflows": [
                    {"pattern": "Iterative Refinement", "evidence": "Prefers iterative refinement"},
                    {"pattern": "Code Quality Focus", "evidence": "Focuses on code quality"},
                ]
            },
            "anti_patterns": {
                "anti_patterns": [
                    {"name": "Skips Documentation", "recommendation": "Occasionally skips documentation"},
                ]
            },
        },
    }


def test_render_returns_string():
    report = _sample_report()
    result = render_individual_html(report)
    assert isinstance(result, str)


def test_render_contains_user_id():
    report = _sample_report()
    result = render_individual_html(report)
    assert "user_12345" in result


def test_render_contains_maturity_label():
    report = _sample_report()
    result = render_individual_html(report)
    assert "Advanced" in result


def test_render_contains_project_names():
    report = _sample_report()
    result = render_individual_html(report)
    assert "Project A" in result
    assert "Project B" in result
    assert "Project C" in result


def test_render_contains_dimension_labels():
    report = _sample_report()
    result = render_individual_html(report)
    assert "Prompting Sophistication" in result
    assert "Tooling Adoption" in result
    assert "Usage Frequency" in result
    assert "Session Depth" in result


def test_render_is_valid_html_skeleton():
    report = _sample_report()
    result = render_individual_html(report)
    assert result.startswith("<!DOCTYPE html>")
    assert "<html" in result
    assert "</html>" in result
    assert "<head>" in result
    assert "</head>" in result
    assert "<body>" in result
    assert "</body>" in result


def test_render_qualitative_section_when_present():
    report = _sample_report()
    result = render_individual_html(report)
    assert "Qualitative Analysis" in result
    assert "User demonstrates strong technical foundation" in result
    assert "Workflow Patterns" in result
    assert "Anti-Patterns" in result


def test_render_no_qualitative_section_when_absent():
    report = _sample_report()
    del report["qualitative_analysis"]
    result = render_individual_html(report)
    assert "Qualitative Analysis" not in result
