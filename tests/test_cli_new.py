import json
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner
from ai_maturity.cli import cli

SAMPLE_SESSION_RECORD = {
    "type": "user", "isMeta": False,
    "message": {"role": "user", "content": "help me debug this"},
    "timestamp": "2026-04-25T10:00:00Z", "sessionId": "s1"
}

FAKE_JUDGE = {
    "level": 2, "confidence": "medium",
    "evidence": ["debug request"], "matched_signals": ["ad-hoc"],
    "reasoning": "Basic usage."
}

def test_submit_creates_developer(tmp_path):
    db = tmp_path / "test.db"
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    (session_dir / "abc123.jsonl").write_text(json.dumps(SAMPLE_SESSION_RECORD) + "\n")
    runner = CliRunner()
    result = runner.invoke(cli, [
        "submit", str(session_dir),
        "--name", "alice", "--email", "alice@co.com", "--team", "platform",
        "--db", str(db),
    ])
    assert result.exit_code == 0, result.output
    assert "alice" in result.output
    from ai_maturity.store import Store
    store = Store(db)
    assert store.get_developer("alice@co.com") is not None
    assert len(store.get_records("alice@co.com")) > 0

def test_assess_grades_developer(tmp_path):
    db = tmp_path / "test.db"
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    (session_dir / "abc123.jsonl").write_text(json.dumps(SAMPLE_SESSION_RECORD) + "\n")
    runner = CliRunner()
    runner.invoke(cli, [
        "submit", str(session_dir),
        "--name", "alice", "--email", "alice@co.com", "--team", "eng",
        "--db", str(db),
    ])
    with patch("ai_maturity.grader.call_claude_judge", return_value=FAKE_JUDGE):
        result = runner.invoke(cli, ["assess", "--email", "alice@co.com", "--db", str(db)])
    assert result.exit_code == 0, result.output
    assert "Overall" in result.output
    from ai_maturity.store import Store
    store = Store(db)
    scores = store.get_scores("alice@co.com")
    assert len(scores) == 12

def test_report_generates_output(tmp_path):
    db = tmp_path / "test.db"
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    (session_dir / "abc123.jsonl").write_text(json.dumps(SAMPLE_SESSION_RECORD) + "\n")
    runner = CliRunner()
    runner.invoke(cli, [
        "submit", str(session_dir),
        "--name", "alice", "--email", "alice@co.com", "--team", "eng",
        "--db", str(db),
    ])
    with patch("ai_maturity.grader.call_claude_judge", return_value=FAKE_JUDGE):
        runner.invoke(cli, ["assess", "--email", "alice@co.com", "--db", str(db)])
    report_dir = tmp_path / "reports"
    with patch("ai_maturity.report.call_claude_writer", return_value="Narrative."):
        with patch("ai_maturity.report.extract_project_context", return_value="Context."):
            result = runner.invoke(cli, [
                "report", "--email", "alice@co.com",
                "--db", str(db), "--output-dir", str(report_dir), "--format", "md",
            ])
    assert result.exit_code == 0, result.output
    assert len(list(report_dir.glob("*.md"))) >= 1

def test_list_shows_developers(tmp_path):
    db = tmp_path / "test.db"
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    (session_dir / "abc123.jsonl").write_text(json.dumps(SAMPLE_SESSION_RECORD) + "\n")
    runner = CliRunner()
    runner.invoke(cli, [
        "submit", str(session_dir),
        "--name", "alice", "--email", "alice@co.com", "--team", "platform",
        "--db", str(db),
    ])
    runner.invoke(cli, [
        "submit", str(session_dir),
        "--name", "bob", "--email", "bob@co.com", "--team", "infra",
        "--db", str(db),
    ])
    result = runner.invoke(cli, ["list", "--db", str(db)])
    assert result.exit_code == 0
    assert "alice" in result.output
    assert "bob" in result.output

def test_assess_unknown_developer(tmp_path):
    db = tmp_path / "test.db"
    runner = CliRunner()
    result = runner.invoke(cli, ["assess", "--email", "nobody@co.com", "--db", str(db)])
    assert result.exit_code == 0
    assert "not found" in result.output.lower()

def test_same_name_different_emails(tmp_path):
    db = tmp_path / "test.db"
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    (session_dir / "abc123.jsonl").write_text(json.dumps(SAMPLE_SESSION_RECORD) + "\n")
    runner = CliRunner()
    runner.invoke(cli, [
        "submit", str(session_dir),
        "--name", "alice", "--email", "alice@platform.com", "--team", "platform",
        "--db", str(db),
    ])
    runner.invoke(cli, [
        "submit", str(session_dir),
        "--name", "alice", "--email", "alice@infra.com", "--team", "infra",
        "--db", str(db),
    ])
    result = runner.invoke(cli, ["list", "--db", str(db)])
    assert result.output.count("alice") >= 2
    from ai_maturity.store import Store
    store = Store(db)
    assert store.get_developer("alice@platform.com") is not None
    assert store.get_developer("alice@infra.com") is not None

def test_export_creates_file(tmp_path):
    db = tmp_path / "test.db"
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    (session_dir / "abc123.jsonl").write_text(json.dumps(SAMPLE_SESSION_RECORD) + "\n")
    runner = CliRunner()
    runner.invoke(cli, [
        "submit", str(session_dir),
        "--name", "alice", "--email", "alice@co.com", "--team", "platform",
        "--db", str(db),
    ])
    result = runner.invoke(cli, ["export", "--email", "alice@co.com", "--db", str(db),
                                  "--output-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    export_files = list(tmp_path.glob("alice_records.jsonl"))
    assert len(export_files) == 1
    lines = export_files[0].read_text().strip().split("\n")
    assert len(lines) >= 2
    meta = json.loads(lines[0])
    assert meta["type"] == "developer"
    assert meta["email"] == "alice@co.com"

def test_export_unknown_developer(tmp_path):
    db = tmp_path / "test.db"
    runner = CliRunner()
    result = runner.invoke(cli, ["export", "--email", "nobody@co.com", "--db", str(db),
                                  "--output-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "not found" in result.output.lower()

def test_import_loads_records(tmp_path):
    # Developer side: submit + export
    db_dev = tmp_path / "dev.db"
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    (session_dir / "abc123.jsonl").write_text(json.dumps(SAMPLE_SESSION_RECORD) + "\n")
    runner = CliRunner()
    runner.invoke(cli, [
        "submit", str(session_dir),
        "--name", "alice", "--email", "alice@co.com", "--team", "platform",
        "--db", str(db_dev),
    ])
    runner.invoke(cli, ["export", "--email", "alice@co.com", "--db", str(db_dev),
                         "--output-dir", str(tmp_path)])

    # Assessor side: import
    db_assessor = tmp_path / "assessor.db"
    export_file = tmp_path / "alice_records.jsonl"
    result = runner.invoke(cli, ["import", str(export_file), "--db", str(db_assessor)])
    assert result.exit_code == 0, result.output
    assert "alice" in result.output
    from ai_maturity.store import Store
    store = Store(db_assessor)
    assert store.get_developer("alice@co.com") is not None
    assert len(store.get_records("alice@co.com")) > 0

def test_import_missing_file(tmp_path):
    db = tmp_path / "test.db"
    runner = CliRunner()
    result = runner.invoke(cli, ["import", str(tmp_path / "nonexistent.jsonl"), "--db", str(db)])
    assert result.exit_code != 0  # Click path validation catches this

def test_import_invalid_file(tmp_path):
    db = tmp_path / "test.db"
    bad_file = tmp_path / "bad.jsonl"
    bad_file.write_text("not json\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["import", str(bad_file), "--db", str(db)])
    assert result.exit_code == 0
    assert "invalid" in result.output.lower()

def test_assess_stores_metrics(tmp_path):
    db = tmp_path / "test.db"
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    (session_dir / "abc123.jsonl").write_text(json.dumps(SAMPLE_SESSION_RECORD) + "\n")
    runner = CliRunner()
    runner.invoke(cli, [
        "submit", str(session_dir),
        "--name", "alice", "--email", "alice@co.com", "--team", "eng",
        "--db", str(db),
    ])
    with patch("ai_maturity.grader.call_claude_judge", return_value=FAKE_JUDGE):
        runner.invoke(cli, ["assess", "--email", "alice@co.com", "--db", str(db)])
    from ai_maturity.store import Store
    store = Store(db)
    metrics = store.get_metrics("alice@co.com")
    assert metrics is not None
    assert "session_count" in metrics
    assert "total_messages" in metrics
    assert "records_by_sub_dimension" in metrics

def test_report_passes_metrics_to_generator(tmp_path):
    db = tmp_path / "test.db"
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    (session_dir / "abc123.jsonl").write_text(json.dumps(SAMPLE_SESSION_RECORD) + "\n")
    runner = CliRunner()
    runner.invoke(cli, [
        "submit", str(session_dir),
        "--name", "alice", "--email", "alice@co.com", "--team", "eng",
        "--db", str(db),
    ])
    with patch("ai_maturity.grader.call_claude_judge", return_value=FAKE_JUDGE):
        runner.invoke(cli, ["assess", "--email", "alice@co.com", "--db", str(db)])

    report_dir = tmp_path / "reports"
    with patch("ai_maturity.report.call_claude_writer", return_value="Narrative."), \
         patch("ai_maturity.report.extract_project_context", return_value="Context."):
        result = runner.invoke(cli, [
            "report", "--email", "alice@co.com", "--db", str(db),
            "--output-dir", str(report_dir), "--format", "md",
        ])
    assert result.exit_code == 0, result.output
    md_files = list(report_dir.glob("*.md"))
    assert len(md_files) == 1
    content = md_files[0].read_text()
    assert "## Usage Analytics" in content


def test_export_excel_creates_file(tmp_path):
    db = tmp_path / "test.db"
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    (session_dir / "abc123.jsonl").write_text(json.dumps(SAMPLE_SESSION_RECORD) + "\n")
    runner = CliRunner()
    runner.invoke(cli, [
        "submit", str(session_dir),
        "--name", "alice", "--email", "alice@co.com", "--team", "eng",
        "--db", str(db),
    ])
    with patch("ai_maturity.grader.call_claude_judge", return_value=FAKE_JUDGE):
        runner.invoke(cli, ["assess", "--email", "alice@co.com", "--db", str(db)])
    report_dir = tmp_path / "reports"
    result = runner.invoke(cli, [
        "export-excel", "--email", "alice@co.com",
        "--db", str(db), "--output-dir", str(report_dir),
    ])
    assert result.exit_code == 0, result.output
    xlsx_files = list(report_dir.glob("*.xlsx"))
    assert len(xlsx_files) == 1
    assert xlsx_files[0].name == "alice_report.xlsx"
    assert "Exporting Excel for alice (eng)" in result.output
    assert "  Excel:" in result.output


def test_export_excel_requires_scores(tmp_path):
    db = tmp_path / "test.db"
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    (session_dir / "abc123.jsonl").write_text(json.dumps(SAMPLE_SESSION_RECORD) + "\n")
    runner = CliRunner()
    runner.invoke(cli, [
        "submit", str(session_dir),
        "--name", "alice", "--email", "alice@co.com", "--team", "eng",
        "--db", str(db),
    ])
    result = runner.invoke(cli, [
        "export-excel", "--email", "alice@co.com",
        "--db", str(db), "--output-dir", str(tmp_path),
    ])
    assert result.exit_code == 0
    assert "assess" in result.output.lower()


def test_export_excel_unknown_developer(tmp_path):
    db = tmp_path / "test.db"
    runner = CliRunner()
    result = runner.invoke(cli, [
        "export-excel", "--email", "nobody@co.com",
        "--db", str(db), "--output-dir", str(tmp_path),
    ])
    assert result.exit_code == 0
    assert "not found" in result.output.lower()
