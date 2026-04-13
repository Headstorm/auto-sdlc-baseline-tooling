"""Tests for the Log Evidence Extractor module."""

import json
import pytest
from pathlib import Path

from auto_sdlc.reports.evidence_extractor import LogEvidence, LogEvidenceExtractor


@pytest.fixture
def multi_session_logs(tmp_path):
    """Create a multi-session project structure for testing."""
    proj_dir = tmp_path / "-Users-test-project"
    proj_dir.mkdir()

    # Session 1: Tool-heavy session
    session1 = [
        {
            "type": "user",
            "isMeta": False,
            "message": {"role": "user", "content": "Fix the login bug in src/auth.py line 42"},
            "timestamp": "2026-03-30T08:00:01.000Z",
            "sessionId": "session1",
        },
        {
            "type": "assistant",
            "isMeta": False,
            "message": {
                "content": [
                    {"type": "tool_use", "name": "grep", "input": {"pattern": "login"}},
                    {"type": "text", "text": "Found the issue"}
                ],
                "usage": {
                    "input_tokens": 500,
                    "output_tokens": 200,
                    "cache_read_input_tokens": 100,
                    "cache_creation_input_tokens": 50,
                }
            },
            "timestamp": "2026-03-30T08:00:10.000Z",
            "sessionId": "session1",
        },
        {
            "type": "system",
            "subtype": "turn_duration",
            "durationMs": 9000,
            "messageCount": 2,
            "slug": "fix-login",
            "timestamp": "2026-03-30T08:00:10.000Z",
            "sessionId": "session1",
            "cwd": "/Users/test/project",
            "gitBranch": "fix/login-bug",
        },
    ]

    # Session 2: Quality-focused session
    session2 = [
        {
            "type": "user",
            "isMeta": False,
            "message": {
                "role": "user",
                "content": "Add comprehensive test coverage to src/utils.py for all edge cases and error scenarios with detailed error handling"
            },
            "timestamp": "2026-03-31T08:00:01.000Z",
            "sessionId": "session2",
        },
        {
            "type": "user",
            "isMeta": True,
            "message": {"role": "user", "content": "/review"},
            "timestamp": "2026-03-31T08:00:02.000Z",
            "sessionId": "session2",
        },
        {
            "type": "assistant",
            "isMeta": False,
            "message": {
                "content": [
                    {"type": "tool_use", "name": "write", "input": {"path": "tests/test_utils.py"}},
                    {"type": "text", "text": "Created comprehensive tests"}
                ],
                "usage": {
                    "input_tokens": 600,
                    "output_tokens": 300,
                    "cache_read_input_tokens": 800,
                    "cache_creation_input_tokens": 0,
                }
            },
            "timestamp": "2026-03-31T08:00:15.000Z",
            "sessionId": "session2",
        },
        {
            "type": "system",
            "subtype": "turn_duration",
            "durationMs": 14000,
            "messageCount": 3,
            "slug": "add-tests",
            "timestamp": "2026-03-31T08:00:15.000Z",
            "sessionId": "session2",
            "cwd": "/Users/test/project",
            "gitBranch": "feat/test-coverage",
        },
    ]

    # Session 3: Low-quality session
    session3 = [
        {
            "type": "user",
            "isMeta": False,
            "message": {"role": "user", "content": "help"},
            "timestamp": "2026-03-31T09:00:01.000Z",
            "sessionId": "session3",
        },
        {
            "type": "assistant",
            "isMeta": False,
            "message": {
                "content": [{"type": "text", "text": "What would you like help with?"}],
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "cache_read_input_tokens": 0,
                    "cache_creation_input_tokens": 20,
                }
            },
            "timestamp": "2026-03-31T09:00:05.000Z",
            "sessionId": "session3",
        },
        {
            "type": "system",
            "subtype": "turn_duration",
            "durationMs": 4000,
            "messageCount": 2,
            "slug": "help-request",
            "timestamp": "2026-03-31T09:00:05.000Z",
            "sessionId": "session3",
            "cwd": "/Users/test/project",
            "gitBranch": "main",
        },
    ]

    # Write session files
    (proj_dir / "session1.jsonl").write_text("\n".join(json.dumps(line) for line in session1))
    (proj_dir / "session2.jsonl").write_text("\n".join(json.dumps(line) for line in session2))
    (proj_dir / "session3.jsonl").write_text("\n".join(json.dumps(line) for line in session3))

    return tmp_path


def test_log_evidence_dataclass():
    """Test LogEvidence dataclass structure."""
    evidence = LogEvidence(
        dimension="Test Dimension",
        signals={"signal1": 0.5, "signal2": 0.8},
        raw_metrics={"metric1": 100},
        confidence="high",
    )
    assert evidence.dimension == "Test Dimension"
    assert evidence.signals == {"signal1": 0.5, "signal2": 0.8}
    assert evidence.raw_metrics == {"metric1": 100}
    assert evidence.confidence == "high"


def test_evidence_extractor_extraction(multi_session_logs):
    """Test full extraction across all dimensions."""
    extractor = LogEvidenceExtractor()
    evidence_list = extractor.extract_from_project(multi_session_logs)

    # Should have exactly 12 dimensions
    assert len(evidence_list) == 12

    # Verify all dimensions are present
    dimensions = {e.dimension for e in evidence_list}
    expected_dims = {
        "AI Tool Adoption",
        "Prompt & Context Engineering",
        "Agent Configuration",
        "CI/CD Integration",
        "Ticketing & Planning",
        "Cross-System Connectivity",
        "Quality Controls",
        "Security & Compliance",
        "Measurement & KPIs",
        "Ways of Working",
        "Accountability & Ownership",
        "Scalability & Knowledge Transfer",
    }
    assert dimensions == expected_dims


def test_ai_tool_adoption_extraction(multi_session_logs):
    """Test AI Tool Adoption dimension extraction."""
    extractor = LogEvidenceExtractor()
    evidence_list = extractor.extract_from_project(multi_session_logs)

    tool_adoption = next(e for e in evidence_list if e.dimension == "AI Tool Adoption")

    # Verify signal structure
    assert "tool_usage_pct" in tool_adoption.signals
    assert "tool_consistency" in tool_adoption.signals
    assert "tool_diversity" in tool_adoption.signals

    # Session 1 has tool calls, so tool_usage_pct should be > 0
    assert tool_adoption.signals["tool_usage_pct"] >= 0
    assert tool_adoption.signals["tool_consistency"] >= 0
    assert tool_adoption.signals["tool_diversity"] >= 0

    # Check raw metrics
    assert "total_tool_calls" in tool_adoption.raw_metrics
    assert "unique_tools" in tool_adoption.raw_metrics

    # Confidence should be high with sessions
    assert tool_adoption.confidence == "high"


def test_prompt_context_engineering_extraction(multi_session_logs):
    """Test Prompt & Context Engineering dimension extraction."""
    extractor = LogEvidenceExtractor()
    evidence_list = extractor.extract_from_project(multi_session_logs)

    prompt_eng = next(e for e in evidence_list if e.dimension == "Prompt & Context Engineering")

    # Verify signal structure
    assert "avg_quality_score" in prompt_eng.signals
    assert "file_ref_frequency" in prompt_eng.signals
    assert "line_ref_frequency" in prompt_eng.signals

    # Session 1 has file reference (src/auth.py) and line reference (line 42)
    # Session 2 has file reference (src/utils.py) but no line reference
    # Session 3 has no file references
    assert prompt_eng.signals["avg_quality_score"] >= 0
    assert prompt_eng.signals["file_ref_frequency"] > 0
    assert prompt_eng.signals["line_ref_frequency"] > 0

    # Raw metrics
    assert "total_prompts_analyzed" in prompt_eng.raw_metrics
    assert prompt_eng.raw_metrics["total_prompts_analyzed"] == 3


def test_quality_controls_extraction(multi_session_logs):
    """Test Quality Controls dimension extraction."""
    extractor = LogEvidenceExtractor()
    evidence_list = extractor.extract_from_project(multi_session_logs)

    quality = next(e for e in evidence_list if e.dimension == "Quality Controls")

    # Session 2 has a /review command
    assert "review_usage_pct" in quality.signals
    assert "test_pattern_prevalence" in quality.signals
    assert "error_recovery_rate" in quality.signals

    # Session 2 mentions "test", so test_pattern_prevalence should be > 0
    assert quality.signals["review_usage_pct"] > 0
    assert quality.signals["test_pattern_prevalence"] > 0

    # Raw metrics
    assert "review_invocations" in quality.raw_metrics
    assert quality.raw_metrics["review_invocations"] > 0


def test_security_compliance_extraction(multi_session_logs):
    """Test Security & Compliance dimension extraction."""
    extractor = LogEvidenceExtractor()
    evidence_list = extractor.extract_from_project(multi_session_logs)

    security = next(e for e in evidence_list if e.dimension == "Security & Compliance")

    # Verify signal structure
    assert "pii_handling_awareness" in security.signals
    assert "cache_hit_ratio" in security.signals

    # Cache ratio should be calculated from token usage
    assert security.signals["cache_hit_ratio"] >= 0
    assert security.signals["cache_hit_ratio"] <= 100

    # Raw metrics
    assert "total_tokens" in security.raw_metrics
    assert "cache_read_tokens" in security.raw_metrics


def test_confidence_level_assignment(multi_session_logs):
    """Test confidence level assignment based on available data."""
    extractor = LogEvidenceExtractor()
    evidence_list = extractor.extract_from_project(multi_session_logs)

    # With real data, confidence should be high or medium
    confidence_levels = [e.confidence for e in evidence_list]
    assert all(c in ["high", "medium", "low"] for c in confidence_levels)

    # With sessions loaded, most should be high confidence
    high_confidence_count = sum(1 for c in confidence_levels if c == "high")
    assert high_confidence_count >= 6


def test_empty_logs_handling():
    """Test handling of missing/incomplete data."""
    extractor = LogEvidenceExtractor()
    evidence_list = extractor.extract_from_project(Path("/nonexistent/path"))

    # Should still return 12 dimensions
    assert len(evidence_list) == 12

    # All should have low confidence
    assert all(e.confidence == "low" for e in evidence_list)

    # All signals should be 0
    for evidence in evidence_list:
        assert all(v == 0.0 for v in evidence.signals.values())


def test_measurement_kpis_extraction(multi_session_logs):
    """Test Measurement & KPIs dimension extraction."""
    extractor = LogEvidenceExtractor()
    evidence_list = extractor.extract_from_project(multi_session_logs)

    kpis = next(e for e in evidence_list if e.dimension == "Measurement & KPIs")

    # Verify signals
    assert "adoption_trend" in kpis.signals
    assert "cycle_time_avg_ms" in kpis.signals

    # Adoption trend: should be sessions per day
    assert kpis.signals["adoption_trend"] > 0

    # Cycle time: should be average of durations
    assert kpis.signals["cycle_time_avg_ms"] > 0

    # Raw metrics
    assert "unique_days" in kpis.raw_metrics
    assert kpis.raw_metrics["unique_days"] > 0


def test_accountability_ownership_extraction(multi_session_logs):
    """Test Accountability & Ownership dimension extraction."""
    extractor = LogEvidenceExtractor()
    evidence_list = extractor.extract_from_project(multi_session_logs)

    accountability = next(e for e in evidence_list if e.dimension == "Accountability & Ownership")

    # Verify signals
    assert "git_consistency" in accountability.signals
    assert "branch_discipline" in accountability.signals

    # We have 3 different branches: fix/login-bug, feat/test-coverage, main
    # This should give us measurable scores
    assert accountability.signals["git_consistency"] >= 0
    assert accountability.signals["branch_discipline"] >= 0

    # Raw metrics
    assert "unique_branches" in accountability.raw_metrics
    assert accountability.raw_metrics["unique_branches"] == 3


def test_signal_values_are_floats(multi_session_logs):
    """Test that all signal values are floats or properly typed."""
    extractor = LogEvidenceExtractor()
    evidence_list = extractor.extract_from_project(multi_session_logs)

    for evidence in evidence_list:
        for signal_name, signal_value in evidence.signals.items():
            assert isinstance(signal_value, float), (
                f"{evidence.dimension}.{signal_name} = {signal_value} is not float"
            )


def test_raw_metrics_transparency(multi_session_logs):
    """Test that raw_metrics provides transparency into calculations."""
    extractor = LogEvidenceExtractor()
    evidence_list = extractor.extract_from_project(multi_session_logs)

    tool_adoption = next(e for e in evidence_list if e.dimension == "AI Tool Adoption")

    # raw_metrics should contain underlying data
    assert len(tool_adoption.raw_metrics) > 0

    # Should include counts and other raw data
    assert "total_tool_calls" in tool_adoption.raw_metrics
    assert "total_messages" in tool_adoption.raw_metrics

    # Verify the data is consistent
    metrics = tool_adoption.raw_metrics
    if metrics["total_messages"] > 0:
        calculated_usage = (metrics["total_tool_calls"] / metrics["total_messages"]) * 100
        assert abs(calculated_usage - tool_adoption.signals["tool_usage_pct"]) < 0.1


def test_ways_of_working_extraction(multi_session_logs):
    """Test Ways of Working dimension extraction."""
    extractor = LogEvidenceExtractor()
    evidence_list = extractor.extract_from_project(multi_session_logs)

    ways = next(e for e in evidence_list if e.dimension == "Ways of Working")

    # Verify signals
    assert "session_opening_pattern" in ways.signals
    assert "plan_mode_usage" in ways.signals

    # Both should be measurable
    assert ways.signals["session_opening_pattern"] >= 0
    assert ways.signals["plan_mode_usage"] >= 0

    # Raw metrics
    assert "total_sessions" in ways.raw_metrics
    assert ways.raw_metrics["total_sessions"] == 3
