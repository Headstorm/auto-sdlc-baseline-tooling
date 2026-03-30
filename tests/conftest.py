"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_session_data():
    """Fixture providing sample Claude Code session data."""
    return {
        "session_id": "test-session-001",
        "created_at": "2026-03-30T10:00:00Z",
        "entries": [
            {
                "timestamp": "2026-03-30T10:00:00Z",
                "type": "user_message",
                "content": "Hello, help me scaffold a project"
            },
            {
                "timestamp": "2026-03-30T10:00:05Z",
                "type": "assistant_response",
                "content": "I'll help you scaffold the project structure"
            }
        ]
    }


@pytest.fixture
def sample_project_structure(tmp_path):
    """Fixture providing a sample project directory structure."""
    src_dir = tmp_path / "src" / "my_project"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text("")
    (tmp_path / "tests").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'my-project'")
    return tmp_path
