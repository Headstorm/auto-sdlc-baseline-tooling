import json
import pytest
from fastapi.testclient import TestClient
from auto_sdlc.server import create_app


def _sample_report(user_id="alice@example.com", overall_level=2, sessions=5, tokens=100000):
    return {
        "user_id": user_id,
        "generated_at": "2026-04-01T10:00:00+00:00",
        "summary": {
            "total_sessions": sessions,
            "total_tokens": tokens,
            "avg_prompt_quality_score": 50.0,
        },
        "behavioral_metrics": {
            "total_user_messages": 50,
            "total_skill_invocations": 5,
            "skill_invocation_ratio": 0.09,
            "sessions_per_day": 1.0,
            "avg_messages_per_session": 10.0,
        },
        "maturity_scores": {
            "overall_level": overall_level,
            "overall_label": ["Beginner", "Basic", "Intermediate", "Advanced", "Expert"][overall_level],
            "dimensions": {
                "prompting_sophistication": {"label": "Prompting", "level": 2, "level_label": "Intermediate"},
            },
        },
        "project_breakdown": [
            {"project": "myapp/src", "sessions": sessions, "total_tokens": tokens, "avg_prompt_quality": 50.0}
        ],
        "sessions": [],
    }


@pytest.fixture
def client(tmp_path):
    app = create_app(str(tmp_path))
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_post_report_saves_file(client, tmp_path):
    r = client.post("/reports", json=_sample_report())
    assert r.status_code == 200
    assert "saved" in r.json()
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1


def test_post_report_returns_user_id(client):
    r = client.post("/reports", json=_sample_report(user_id="bob@example.com"))
    assert r.json()["user_id"] == "bob@example.com"


def test_list_reports_empty(client):
    r = client.get("/reports")
    assert r.status_code == 200
    assert r.json()["count"] == 0


def test_list_reports_after_post(client):
    client.post("/reports", json=_sample_report("alice@example.com"))
    client.post("/reports", json=_sample_report("bob@example.com"))
    r = client.get("/reports")
    assert r.json()["count"] == 2


def test_team_json_404_when_empty(client):
    r = client.get("/team")
    assert r.status_code == 404


def test_team_json_after_reports(client):
    client.post("/reports", json=_sample_report("alice@example.com", overall_level=2))
    client.post("/reports", json=_sample_report("bob@example.com", overall_level=4))
    r = client.get("/team")
    assert r.status_code == 200
    data = r.json()
    assert data["team_size"] == 2
    assert "overall_maturity_label" in data


def test_team_html_after_reports(client):
    client.post("/reports", json=_sample_report("alice@example.com"))
    r = client.get("/team/html")
    assert r.status_code == 200
    assert "<!DOCTYPE html>" in r.text
    assert "alice" in r.text
