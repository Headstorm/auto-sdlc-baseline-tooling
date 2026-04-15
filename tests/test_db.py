import os
import tempfile
import pytest
from pathlib import Path
from auto_sdlc.db import Database


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test.db"
    database = Database(str(db_path))
    database.init()
    yield database
    database.close()


def test_init_creates_tables(db):
    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = {row[0] for row in tables}
    assert "log_uploads" in table_names
    assert "reports" in table_names


def test_insert_upload(db):
    upload_id = db.insert_upload(
        team_name="platform_team",
        user_name="john.smith",
        logs_path="/tmp/logs",
        session_count=5,
        total_tokens=12000,
    )
    assert isinstance(upload_id, int)
    assert upload_id > 0


def test_get_all_uploads_empty(db):
    result = db.get_all_uploads()
    assert result == []


def test_get_all_uploads_returns_inserted(db):
    db.insert_upload("team_a", "alice", "/tmp/a", 3, 5000)
    db.insert_upload("team_b", "bob", "/tmp/b", 7, 9000)
    result = db.get_all_uploads()
    assert len(result) == 2
    assert result[0]["team_name"] == "team_b"
    assert result[1]["team_name"] == "team_a"


def test_get_uploads_by_team(db):
    db.insert_upload("team_a", "alice", "/tmp/a", 3, 5000)
    db.insert_upload("team_b", "bob", "/tmp/b", 7, 9000)
    result = db.get_uploads_by_team("team_a")
    assert len(result) == 1
    assert result[0]["user_name"] == "alice"


def test_get_upload_by_id(db):
    upload_id = db.insert_upload("team_a", "alice", "/tmp/a", 3, 5000)
    row = db.get_upload_by_id(upload_id)
    assert row is not None
    assert row["user_name"] == "alice"
    assert row["status"] == "pending"


def test_insert_report_and_update_upload_status(db):
    upload_id = db.insert_upload("team_a", "alice", "/tmp/a", 3, 5000)
    report_id = db.insert_report(
        upload_id=upload_id,
        team_name="team_a",
        user_name="alice",
        report_type="individual",
        pdf_path="/tmp/report.pdf",
        overall_maturity_level=2.5,
    )
    assert isinstance(report_id, int)

    upload = db.get_upload_by_id(upload_id)
    assert upload["status"] == "reported"


def test_get_reports_for_upload(db):
    upload_id = db.insert_upload("team_a", "alice", "/tmp/a", 3, 5000)
    db.insert_report(upload_id, "team_a", "alice", "individual", "/tmp/r.pdf", 2.0)
    reports = db.get_reports_for_upload(upload_id)
    assert len(reports) == 1
    assert reports[0]["pdf_path"] == "/tmp/r.pdf"
