import json
import pytest
from pathlib import Path
from auto_sdlc.logs.ingest import (
    discover_users_from_dir,
    load_users_from_csv,
    run_bulk_ingest,
)


def test_discover_users_layout_a(tmp_path):
    """Layout A: user_dir/projects/*.jsonl (standard Claude Code structure)."""
    # Create: tmp_path/alice/projects/myapp/s.jsonl
    user_dir = tmp_path / "alice"
    projects_dir = user_dir / "projects" / "myapp"
    projects_dir.mkdir(parents=True)

    session_file = projects_dir / "s.jsonl"
    session_file.write_text('{"type":"say"}\n')

    users = discover_users_from_dir(tmp_path)

    assert len(users) == 1
    assert users[0][0] == "alice"
    assert users[0][1] == user_dir / "projects"


def test_discover_users_layout_b(tmp_path):
    """Layout B: user_dir/*.jsonl (flat, no projects/ subdir)."""
    # Create: tmp_path/bob/session.jsonl (flat)
    user_dir = tmp_path / "bob"
    user_dir.mkdir()

    session_file = user_dir / "session.jsonl"
    session_file.write_text('{"type":"say"}\n')

    users = discover_users_from_dir(tmp_path)

    assert len(users) == 1
    assert users[0][0] == "bob"
    assert users[0][1] == user_dir


def test_discover_users_mixed_layouts(tmp_path):
    """Both layouts in same root dir."""
    # Layout A user
    alice_dir = tmp_path / "alice"
    (alice_dir / "projects" / "myapp").mkdir(parents=True)
    (alice_dir / "projects" / "myapp" / "s.jsonl").write_text('{"type":"say"}\n')

    # Layout B user
    bob_dir = tmp_path / "bob"
    bob_dir.mkdir()
    (bob_dir / "s.jsonl").write_text('{"type":"say"}\n')

    users = discover_users_from_dir(tmp_path)

    assert len(users) == 2
    user_ids = [u[0] for u in users]
    assert "alice" in user_ids
    assert "bob" in user_ids


def test_load_users_from_csv(tmp_path):
    """Load user list from CSV: user_id,logs_path."""
    csv_file = tmp_path / "users.csv"
    csv_file.write_text("alice@company.com,/tmp/alice\nbob@company.com,/tmp/bob\n")

    users = load_users_from_csv(csv_file)

    assert len(users) == 2
    assert users[0] == ("alice@company.com", Path("/tmp/alice"))
    assert users[1] == ("bob@company.com", Path("/tmp/bob"))


def test_load_users_from_csv_skips_comments(tmp_path):
    """CSV with # comment lines should be ignored."""
    csv_file = tmp_path / "users.csv"
    csv_file.write_text(
        "# This is a comment\n"
        "alice@company.com,/tmp/alice\n"
        "# Another comment\n"
        "bob@company.com,/tmp/bob\n"
    )

    users = load_users_from_csv(csv_file)

    assert len(users) == 2
    assert users[0][0] == "alice@company.com"
    assert users[1][0] == "bob@company.com"


def test_load_users_from_csv_skips_empty_lines(tmp_path):
    """CSV with empty lines should be skipped."""
    csv_file = tmp_path / "users.csv"
    csv_file.write_text(
        "alice@company.com,/tmp/alice\n"
        "\n"
        "bob@company.com,/tmp/bob\n"
        "\n"
    )

    users = load_users_from_csv(csv_file)

    assert len(users) == 2


def test_load_users_from_csv_file_not_found(tmp_path):
    """CSV file that doesn't exist should raise error."""
    csv_file = tmp_path / "nonexistent.csv"

    with pytest.raises(FileNotFoundError):
        load_users_from_csv(csv_file)


def test_run_bulk_ingest_end_to_end(tmp_path, sample_session_lines):
    """Full ingest pipeline: discover 2 users, process, aggregate team."""
    # Create two user directories with minimal JSONL files

    # User 1: Layout A (with projects/)
    alice_dir = tmp_path / "logs" / "alice"
    alice_projects = alice_dir / "projects" / "myapp"
    alice_projects.mkdir(parents=True)
    alice_session = alice_projects / "s1.jsonl"
    alice_session.write_text("\n".join(json.dumps(line) for line in sample_session_lines))

    # User 2: Layout B (flat)
    bob_dir = tmp_path / "logs" / "bob"
    bob_dir.mkdir(parents=True)
    bob_session = bob_dir / "s1.jsonl"
    bob_session.write_text("\n".join(json.dumps(line) for line in sample_session_lines))

    # Run ingest
    output_dir = tmp_path / "output"
    run_bulk_ingest(
        logs_root=str(tmp_path / "logs"),
        output_dir=str(output_dir),
        since=None,
        html=False,
        qualitative=False,
        users_file=None,
    )

    # Verify output
    assert output_dir.exists()

    # Check individual reports exist
    json_files = list(output_dir.glob("*.json"))
    assert len(json_files) >= 2, f"Expected at least 2 JSON files, got {len(json_files)}: {json_files}"

    # Check team report exists
    team_report_path = output_dir / "team_report.json"
    assert team_report_path.exists(), f"team_report.json not found in {output_dir}"

    # Check team report content
    team_report = json.loads(team_report_path.read_text())
    assert team_report["team_size"] == 2
    assert "members" in team_report
    assert len(team_report["members"]) == 2


def test_run_bulk_ingest_with_html(tmp_path, sample_session_lines):
    """Ingest with --html flag should generate HTML reports."""
    # Create one user
    alice_dir = tmp_path / "logs" / "alice"
    alice_projects = alice_dir / "projects" / "myapp"
    alice_projects.mkdir(parents=True)
    alice_session = alice_projects / "s1.jsonl"
    alice_session.write_text("\n".join(json.dumps(line) for line in sample_session_lines))

    # Run ingest with html=True
    output_dir = tmp_path / "output"
    run_bulk_ingest(
        logs_root=str(tmp_path / "logs"),
        output_dir=str(output_dir),
        since=None,
        html=True,
        qualitative=False,
        users_file=None,
    )

    # Check HTML files exist
    html_files = list(output_dir.glob("*.html"))
    assert len(html_files) >= 1, f"Expected at least 1 HTML file, got {html_files}"

    team_html = output_dir / "team_report.html"
    assert team_html.exists(), "team_report.html not found"
    assert len(team_html.read_text()) > 0


def test_run_bulk_ingest_with_csv(tmp_path, sample_session_lines):
    """Ingest with --users-file CSV should use that instead of directory discovery."""
    # Create two user directories
    alice_dir = tmp_path / "alice_logs"
    alice_dir.mkdir()
    (alice_dir / "s1.jsonl").write_text("\n".join(json.dumps(line) for line in sample_session_lines))

    bob_dir = tmp_path / "bob_logs"
    bob_dir.mkdir()
    (bob_dir / "s1.jsonl").write_text("\n".join(json.dumps(line) for line in sample_session_lines))

    # Create CSV
    csv_file = tmp_path / "users.csv"
    csv_file.write_text(f"alice@company.com,{alice_dir}\nbob@company.com,{bob_dir}\n")

    # Run ingest with CSV
    output_dir = tmp_path / "output"
    run_bulk_ingest(
        logs_root=str(tmp_path),  # logs_root is ignored when users_file is provided
        output_dir=str(output_dir),
        since=None,
        html=False,
        qualitative=False,
        users_file=str(csv_file),
    )

    # Verify team report
    team_report_path = output_dir / "team_report.json"
    assert team_report_path.exists()
    team_report = json.loads(team_report_path.read_text())
    assert team_report["team_size"] == 2
