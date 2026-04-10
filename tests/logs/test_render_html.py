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


def test_render_contains_dimension_details_dropdowns():
    """Test that dimensions have collapsible details sections."""
    report = _sample_report()
    result = render_individual_html(report)
    assert "<details class='dimension-details'>" in result
    assert "<summary" in result


def test_render_contains_metrics_tables():
    """Test that metric details are present for dimensions."""
    report = _sample_report()
    result = render_individual_html(report)
    # Check for metrics table
    assert "Avg Prompt Quality" in result
    assert "Skill Invocation Ratio" in result
    assert "Sessions Per Day" in result
    assert "Total Sessions" in result


def test_render_contains_context_efficiency_metrics():
    """Test that context efficiency metrics are rendered when dimension present."""
    report = _sample_report()
    # Add context efficiency dimension and cache tokens
    report["maturity_scores"]["dimensions"]["context_efficiency"] = {
        "label": "Context Efficiency",
        "level": 2,
        "level_label": "Intermediate",
    }
    report["summary"]["total_cache_read_tokens"] = 50000
    report["summary"]["total_cache_creation_tokens"] = 10000
    result = render_individual_html(report)
    assert "Cache Hit Ratio" in result
    assert "Cache Read Tokens" in result


def test_render_html_escaping_xss_prevention():
    """Test that user-provided values are HTML-escaped to prevent XSS."""
    report = _sample_report()
    # Add special characters that could be used in XSS attacks
    report["user_id"] = "test<script>alert('xss')</script>"
    report["project_breakdown"][0]["project"] = "project&<script>"
    report["qualitative_analysis"]["narrative"] = "test<img src=x onerror='alert(1)'>"
    report["qualitative_analysis"]["workflow_patterns"]["workflows"][0]["pattern"] = "pattern<svg>"
    report["qualitative_analysis"]["anti_patterns"]["anti_patterns"][0]["name"] = "name&quot;script"

    result = render_individual_html(report)

    # Verify special characters are escaped, not rendered as HTML
    assert "&lt;script&gt;" in result
    assert "&amp;" in result
    assert "<script>" not in result
    # Verify safe content is still rendered
    assert "Auto-SDLC Developer Report" in result


def test_render_with_zero_total_tokens():
    """Test that cache hit ratio handles zero total tokens without division by zero."""
    report = _sample_report()
    # Add context efficiency dimension with zero tokens
    report["maturity_scores"]["dimensions"]["context_efficiency"] = {
        "label": "Context Efficiency",
        "level": 2,
        "level_label": "Intermediate",
    }
    report["summary"]["total_tokens"] = 0
    report["summary"]["total_cache_read_tokens"] = 0

    # Should not raise ZeroDivisionError
    result = render_individual_html(report)
    assert isinstance(result, str)
    assert "Cache Hit Ratio" in result
    assert "0.0%" in result


def test_render_with_missing_metric_values():
    """Test that missing metric values default to em-dash."""
    report = _sample_report()
    # Remove optional metric values
    report["summary"]["avg_session_duration_ms"] = None
    report["behavioral_metrics"]["sessions_per_day"] = None
    report["behavioral_metrics"]["avg_messages_per_session"] = None
    report["project_breakdown"][0]["avg_prompt_quality"] = None

    result = render_individual_html(report)
    # Verify em-dashes are rendered for missing values
    assert "—" in result
    # Verify the report still renders successfully
    assert "Auto-SDLC Developer Report" in result


def test_render_with_unrecognized_dimension():
    """Test that unrecognized dimensions have graceful fallback."""
    report = _sample_report()
    # Add a custom/unrecognized dimension
    report["maturity_scores"]["dimensions"]["custom_dimension"] = {
        "label": "Custom Metric",
        "level": 2,
        "level_label": "Good",
    }

    result = render_individual_html(report)
    # Should render without error and include fallback message
    assert "Metrics not available" in result
    assert "Custom Metric" in result
