from src.auto_sdlc.logs.parser import parse_session_file, find_session_files


def test_parse_session_file_returns_all_lines(sample_jsonl_file):
    events = parse_session_file(sample_jsonl_file)
    assert len(events) == 5


def test_parse_session_file_types(sample_jsonl_file):
    events = parse_session_file(sample_jsonl_file)
    types = [e["type"] for e in events]
    assert "user" in types
    assert "assistant" in types
    assert "system" in types


def test_parse_session_file_skips_invalid_json(tmp_path):
    f = tmp_path / "bad.jsonl"
    f.write_text('{"type": "user"}\nNOT JSON\n{"type": "assistant"}\n')
    events = parse_session_file(f)
    assert len(events) == 2


def test_find_session_files_finds_jsonl(sample_projects_dir):
    files = find_session_files(sample_projects_dir)
    assert len(files) == 1
    assert files[0].suffix == ".jsonl"


def test_find_session_files_returns_paths(sample_projects_dir):
    from pathlib import Path
    files = find_session_files(sample_projects_dir)
    assert all(isinstance(f, Path) for f in files)
