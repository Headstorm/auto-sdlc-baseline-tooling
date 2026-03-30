import json
from pathlib import Path

def parse_session_file(path):
    """Parse a .jsonl session file, skipping malformed lines."""
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events

def find_session_files(projects_dir):
    """Recursively find all .jsonl files under a projects directory."""
    return sorted(projects_dir.rglob("*.jsonl"))
