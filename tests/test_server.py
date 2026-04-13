import io
import json
import zipfile
import pytest
from fastapi.testclient import TestClient
from auto_sdlc.server import create_app, _find_projects_dir


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


# --- Upload & Dashboard Tests ---

def _make_zip(session_lines):
    """Create an in-memory ZIP with a minimal projects/ layout."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        content = "\n".join(json.dumps(line) for line in session_lines)
        zf.writestr("projects/myapp/session.jsonl", content)
    buf.seek(0)
    return buf


def test_upload_form_returns_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "<form" in r.text
    assert "upload" in r.text.lower()


def test_upload_zip_redirects_to_dashboard(client, sample_session_lines):
    zip_buf = _make_zip(sample_session_lines)
    r = client.post(
        "/upload",
        data={"user_id": "alice@test.com"},
        files={"logs_zip": ("projects.zip", zip_buf, "application/zip")},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "alice_at_test.com" in r.headers["location"]


def test_upload_creates_report_file(client, tmp_path, sample_session_lines):
    zip_buf = _make_zip(sample_session_lines)
    client.post(
        "/upload",
        data={"user_id": "alice@test.com"},
        files={"logs_zip": ("projects.zip", zip_buf, "application/zip")},
    )
    files = list(tmp_path.glob("alice_at_test.com_*.json"))
    assert len(files) == 1
    report = json.loads(files[0].read_text())
    assert report["user_id"] == "alice@test.com"


def test_dashboard_returns_individual_html(client, sample_session_lines):
    zip_buf = _make_zip(sample_session_lines)
    client.post(
        "/upload",
        data={"user_id": "alice@test.com"},
        files={"logs_zip": ("projects.zip", zip_buf, "application/zip")},
    )
    r = client.get("/dashboard/alice_at_test.com")
    assert r.status_code == 200
    assert "<!DOCTYPE html>" in r.text
    assert "Team Dashboard" in r.text  # injected nav link


def test_upload_rejects_non_zip(client):
    r = client.post(
        "/upload",
        data={"user_id": "test@test.com"},
        files={"logs_zip": ("file.txt", b"not a zip", "text/plain")},
    )
    assert r.status_code == 400


def test_dashboard_404_for_unknown_user(client):
    r = client.get("/dashboard/nobody")
    assert r.status_code == 404


def test_find_projects_dir_with_projects_subdir(tmp_path):
    """_find_projects_dir should return the projects/ subdir if it exists."""
    projects = tmp_path / "projects" / "myapp"
    projects.mkdir(parents=True)
    (projects / "s.jsonl").write_text('{"type":"say"}\n')
    result = _find_projects_dir(tmp_path)
    assert result == tmp_path / "projects"


def test_find_projects_dir_flat_layout(tmp_path):
    """_find_projects_dir should return root when jsonl files are at top level."""
    (tmp_path / "s.jsonl").write_text('{"type":"say"}\n')
    result = _find_projects_dir(tmp_path)
    assert result == tmp_path


# ============================================================================
# REPORT API ENDPOINT TESTS
# ============================================================================

def test_report_status_endpoint(client):
    """GET /api/report/status returns server status and capabilities."""
    r = client.get("/api/report/status")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ready"
    assert data["version"] == "1.0"
    assert "team_reports" in data["capabilities"]
    assert "individual_reports" in data["capabilities"]
    assert "assessment_integration" in data["capabilities"]


def test_report_validate_endpoint_valid_inputs(tmp_path):
    """POST /api/report/validate with valid inputs returns validation success."""
    # Create a test project directory structure
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    (project_dir / "logs").mkdir()
    (project_dir / "CLAUDE.md").write_text("# Test")

    app = create_app(str(tmp_path))
    client = TestClient(app)

    r = client.post("/api/report/validate", json={
        "user_id": "test_user",
        "project_path": str(project_dir),
        "report_type": "team",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is True
    assert len(data["errors"]) == 0
    assert data["data_sources"]["logs"] is True
    assert data["data_sources"]["configs"] is True


def test_report_validate_endpoint_invalid_report_type(tmp_path):
    """POST /api/report/validate returns error for invalid report_type."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    app = create_app(str(tmp_path))
    client = TestClient(app)

    r = client.post("/api/report/validate", json={
        "user_id": "test_user",
        "project_path": str(project_dir),
        "report_type": "invalid_type",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is False
    assert any("report_type" in err for err in data["errors"])


def test_report_validate_endpoint_missing_project_path(tmp_path):
    """POST /api/report/validate returns error for missing project path."""
    app = create_app(str(tmp_path))
    client = TestClient(app)

    r = client.post("/api/report/validate", json={
        "user_id": "test_user",
        "project_path": "/nonexistent/path",
        "report_type": "team",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is False
    assert any("does not exist" in err for err in data["errors"])


def test_report_validate_endpoint_invalid_assessment_responses(tmp_path):
    """POST /api/report/validate returns error for invalid assessment responses file."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    app = create_app(str(tmp_path))
    client = TestClient(app)

    r = client.post("/api/report/validate", json={
        "user_id": "test_user",
        "project_path": str(project_dir),
        "report_type": "team",
        "assessment_responses": "/nonexistent/responses.json",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is False
    assert any("assessment_responses" in err for err in data["errors"])


def test_report_generate_endpoint_missing_user_id(tmp_path):
    """POST /api/report/generate returns 422 for missing user_id."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    app = create_app(str(tmp_path))
    client = TestClient(app)

    r = client.post("/api/report/generate", json={
        "user_id": "",
        "project_path": str(project_dir),
        "report_type": "team",
    })
    # Pydantic validation catches empty user_id with 422
    assert r.status_code == 422


def test_report_generate_endpoint_invalid_report_type(tmp_path):
    """POST /api/report/generate returns 400 for invalid report_type."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    app = create_app(str(tmp_path))
    client = TestClient(app)

    r = client.post("/api/report/generate", json={
        "user_id": "test_user",
        "project_path": str(project_dir),
        "report_type": "invalid_type",
    })
    assert r.status_code == 400
    data = r.json()
    assert "detail" in data


def test_report_generate_endpoint_missing_project_path(tmp_path):
    """POST /api/report/generate returns 400 for missing project path."""
    app = create_app(str(tmp_path))
    client = TestClient(app)

    r = client.post("/api/report/generate", json={
        "user_id": "test_user",
        "project_path": "/nonexistent/path",
        "report_type": "team",
    })
    assert r.status_code == 400
    data = r.json()
    assert "detail" in data
