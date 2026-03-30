import json
import pytest
from pathlib import Path


@pytest.fixture
def sample_session_lines():
    """Minimal set of JSONL lines representing one session."""
    return [
        # system start
        {"type": "system", "subtype": "local_command", "content": "/help",
         "timestamp": "2026-03-30T08:00:00.000Z", "sessionId": "abc123",
         "isMeta": False},
        # real user prompt
        {"type": "user", "isMeta": False,
         "message": {"role": "user", "content": "Fix the login bug in src/auth.py line 42"},
         "timestamp": "2026-03-30T08:00:01.000Z", "sessionId": "abc123",
         "uuid": "u1"},
        # meta user (slash command wrapper — excluded from prompt scoring)
        {"type": "user", "isMeta": True,
         "message": {"role": "user", "content": "<local-command-caveat>ignore</local-command-caveat>"},
         "timestamp": "2026-03-30T08:00:02.000Z", "sessionId": "abc123",
         "uuid": "u2"},
        # assistant with token usage
        {"type": "assistant", "isMeta": False,
         "message": {
             "model": "claude-sonnet-4-6",
             "usage": {
                 "input_tokens": 500,
                 "output_tokens": 200,
                 "cache_read_input_tokens": 1000,
                 "cache_creation_input_tokens": 300,
             }
         },
         "timestamp": "2026-03-30T08:00:10.000Z", "sessionId": "abc123",
         "uuid": "a1"},
        # session end marker
        {"type": "system", "subtype": "turn_duration",
         "durationMs": 9000, "messageCount": 3,
         "slug": "fix-login-session",
         "timestamp": "2026-03-30T08:00:10.000Z",
         "sessionId": "abc123", "cwd": "/Users/smannar/myproject",
         "gitBranch": "main"},
    ]


@pytest.fixture
def sample_jsonl_file(tmp_path, sample_session_lines):
    """Write sample session lines to a .jsonl file."""
    f = tmp_path / "abc123.jsonl"
    f.write_text("\n".join(json.dumps(line) for line in sample_session_lines))
    return f


@pytest.fixture
def sample_projects_dir(tmp_path, sample_session_lines):
    """Create a fake ~/.claude/projects/ layout with one project and one session."""
    proj_dir = tmp_path / "-Users-smannar-myproject"
    proj_dir.mkdir()
    session_file = proj_dir / "abc123.jsonl"
    session_file.write_text("\n".join(json.dumps(line) for line in sample_session_lines))
    return tmp_path
