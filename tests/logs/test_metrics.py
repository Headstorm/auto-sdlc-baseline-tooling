import pytest
from auto_sdlc.logs.metrics import extract_behavioral_metrics, aggregate_behavioral_metrics


@pytest.fixture
def session_with_tools():
    return [
        {"type": "user", "isMeta": False,
         "message": {"role": "user", "content": "fix the bug"},
         "sessionId": "s1", "timestamp": "2026-03-01T09:00:00.000Z"},
        {"type": "user", "isMeta": True,
         "message": {"role": "user", "content": "<local-command-caveat>/compact</local-command-caveat>"},
         "sessionId": "s1", "timestamp": "2026-03-01T09:00:01.000Z"},
        {"type": "assistant", "isMeta": False,
         "message": {
             "content": [
                 {"type": "tool_use", "name": "Bash", "id": "t1"},
                 {"type": "tool_use", "name": "Read", "id": "t2"},
             ],
             "usage": {"input_tokens": 100, "output_tokens": 50,
                       "cache_read_input_tokens": 200, "cache_creation_input_tokens": 80}
         },
         "sessionId": "s1", "timestamp": "2026-03-01T09:00:10.000Z"},
    ]


def test_extract_counts_user_messages(session_with_tools):
    result = extract_behavioral_metrics(session_with_tools)
    assert result["user_messages"] == 1


def test_extract_counts_skill_invocations(session_with_tools):
    result = extract_behavioral_metrics(session_with_tools)
    assert result["skill_invocations"] == 1


def test_extract_counts_tool_calls(session_with_tools):
    result = extract_behavioral_metrics(session_with_tools)
    assert result["tool_calls"] == 2


def test_extract_unique_tools(session_with_tools):
    result = extract_behavioral_metrics(session_with_tools)
    assert set(result["unique_tools"]) == {"Bash", "Read"}


def test_aggregate_skill_ratio():
    # 1 skill invocation, 1 user message → ratio = 0.5
    session = [
        {"type": "user", "isMeta": False,
         "message": {"role": "user", "content": "hello"},
         "sessionId": "x", "timestamp": "2026-03-01T09:00:00.000Z"},
        {"type": "user", "isMeta": True,
         "message": {"role": "user", "content": "/compact"},
         "sessionId": "x", "timestamp": "2026-03-01T09:00:01.000Z"},
    ]
    result = aggregate_behavioral_metrics([session, session], total_days_active=2)
    assert result["skill_invocation_ratio"] == 0.5
    assert result["sessions_per_day"] == 1.0


def test_aggregate_avg_messages_per_session():
    session_a = [
        {"type": "user", "isMeta": False,
         "message": {"role": "user", "content": "a"},
         "sessionId": "a", "timestamp": "2026-03-01T09:00:00.000Z"},
        {"type": "user", "isMeta": False,
         "message": {"role": "user", "content": "b"},
         "sessionId": "a", "timestamp": "2026-03-01T09:00:01.000Z"},
    ]
    session_b = [
        {"type": "user", "isMeta": False,
         "message": {"role": "user", "content": "c"},
         "sessionId": "b", "timestamp": "2026-03-01T09:00:00.000Z"},
    ]
    result = aggregate_behavioral_metrics([session_a, session_b], total_days_active=1)
    assert result["avg_messages_per_session"] == 1.5   # (2+1)/2
