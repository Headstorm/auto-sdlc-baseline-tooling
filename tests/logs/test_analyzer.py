import pytest
from auto_sdlc.logs.analyzer import (
    extract_token_usage,
    extract_session_metadata,
    aggregate_sessions,
)


def test_extract_token_usage_sums_assistant_turns(sample_session_lines):
    result = extract_token_usage(sample_session_lines)
    assert result["input_tokens"] == 500
    assert result["output_tokens"] == 200
    assert result["cache_read_input_tokens"] == 1000
    assert result["cache_creation_input_tokens"] == 300
    assert result["total_tokens"] == 2000   # 500+200+1000+300


def test_extract_token_usage_empty():
    result = extract_token_usage([])
    assert result["total_tokens"] == 0


def test_extract_session_metadata_uses_turn_duration(sample_session_lines):
    meta = extract_session_metadata(sample_session_lines)
    assert meta["session_id"] == "abc123"
    assert meta["duration_ms"] == 9000
    assert meta["message_count"] == 3
    assert meta["slug"] == "fix-login-session"
    assert meta["cwd"] == "/Users/smannar/myproject"
    assert meta["git_branch"] == "main"


def test_extract_session_metadata_missing_turn_duration():
    events = [{"type": "user", "sessionId": "xyz", "timestamp": "2026-01-01T00:00:00.000Z"}]
    meta = extract_session_metadata(events)
    assert meta["session_id"] == "xyz"
    assert meta["duration_ms"] is None
    assert meta["message_count"] is None


def test_aggregate_sessions_combines_multiple(sample_session_lines):
    sessions = aggregate_sessions([sample_session_lines, sample_session_lines])
    assert sessions["total_sessions"] == 2
    assert sessions["total_input_tokens"] == 1000   # 500 * 2
    assert sessions["total_output_tokens"] == 400   # 200 * 2
