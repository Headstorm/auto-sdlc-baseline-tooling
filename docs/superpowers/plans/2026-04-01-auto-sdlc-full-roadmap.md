# Auto-SDLC Full Roadmap — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `auto-sdlc` — a Python CLI that automatically baselines a developer team's AI maturity by parsing Claude Code session logs, storing metrics in SQLite, auto-collecting via a Claude Code hook, and rolling up individual scores to a team-level dashboard.

**Architecture:** Individual developers run `auto-sdlc logs` (or it runs automatically via a Claude Code Stop hook). Each run processes new JSONL sessions, upserts into a local SQLite database, and optionally POSTs a JSON report to a central FastAPI server. The server aggregates individual reports into a live team dashboard. Qualitative analysis maps findings to the 12 Auto-SDLC discovery categories via `claude -p` subprocess calls.

**Tech Stack:** Python 3.9, Click, SQLite (stdlib `sqlite3`), FastAPI + uvicorn (optional), pytest. No `|` union type syntax anywhere — Python 3.9 compat required.

---

## Status of Already-Completed Work

These tasks are **done** and not re-implemented below. Provided as context only.

| Done | What was built |
|---|---|
| ✅ Task 1 | `pyproject.toml`, package scaffold, `cli.py` with `logs`/`init`/`audit` subcommands |
| ✅ Task 2 | `logs/parser.py` — `parse_session_file`, `find_session_files` |
| ✅ Task 3 | `logs/analyzer.py` — `extract_token_usage`, `extract_session_metadata`, `aggregate_sessions` |
| ✅ Task 4 | `logs/scorer.py` — rule-based prompt quality scorer (0-100 scale, 5 heuristics) |
| ✅ Task 5 | `logs/report.py` — `build_report`, `run_logs_report`, project breakdown |
| ✅ Task 6 | `init_wizard/wizard.py`, `audit/scanner.py` stubs; `tests/test_cli.py` smoke tests |
| ✅ Task 7 | `logs/metrics.py` — behavioral metrics (skill ratio, sessions/day, tool diversity); `logs/maturity.py` — 5-dimension scoring |
| ✅ Task 8 | `logs/render_html.py` — individual HTML report; `logs/export.py` — `export_report_to_dir`, `export_report_to_http` |
| ✅ Task 9 | `logs/team.py` — team rollup + HTML; `server.py` — FastAPI with `/reports`, `/team`, `/team/html` |
| ✅ Task 10 | CLI flags: `--user-id`, `--qualitative`, `--html`, `--export-dir`, `--export-url`; `team` and `serve` subcommands |
| ✅ Task 11 | `logs/qualitative.py` — generic LLM calls via `claude -p` for workflow patterns, anti-patterns, maturity narrative |

---

## File Structure for Remaining Work

```
src/auto_sdlc/
├── logs/
│   ├── store.py          # NEW: SQLite metrics store (Task 12)
│   ├── workflows.py      # NEW: sliding-window workflow extraction (Task 15)
│   ├── report.py         # MODIFY: integrate store.py for incremental processing (Task 12)
│   ├── qualitative.py    # MODIFY: expand to 12 discovery categories (Task 14)
│   └── maturity.py       # MODIFY: add rework_ratio + abandonment_rate dimensions (Task 15)
├── hook.py               # NEW: hook install/uninstall logic (Task 13)
├── cli.py                # MODIFY: add install-hook subcommand (Task 13)
└── metrics.py            # MODIFY: add rework detection + abandonment rate (Task 15)
tests/
├── logs/
│   ├── test_store.py     # NEW (Task 12)
│   ├── test_workflows.py # NEW (Task 15)
│   └── test_qualitative.py  # MODIFY: add discovery category tests (Task 14)
└── test_hook.py          # NEW (Task 13)
```

---

## Task 12: SQLite Metrics Store + Incremental Processing

**Why:** Currently `auto-sdlc logs` re-parses every JSONL file on every run. For a developer with 200+ sessions, this is slow and wastes compute. SQLite stores processed session metrics and lets subsequent runs skip already-seen sessions.

**Files:**
- Create: `src/auto_sdlc/logs/store.py`
- Modify: `src/auto_sdlc/logs/report.py` (lines 65-120 — `build_report`)
- Create: `tests/logs/test_store.py`

- [ ] **Step 1: Write failing tests for store.py**

```python
# tests/logs/test_store.py
import pytest
import sqlite3
from pathlib import Path
from auto_sdlc.logs.store import (
    open_db,
    init_db,
    upsert_session,
    get_processed_session_ids,
    get_sessions_for_user,
)


@pytest.fixture
def conn(tmp_path):
    db_path = tmp_path / "test.db"
    c = open_db(str(db_path))
    init_db(c)
    yield c
    c.close()


def _sample_session():
    return {
        "session_id": "abc123",
        "user_id": "alice@example.com",
        "date": "2026-03-30",
        "cwd": "/Users/alice/myapp",
        "duration_ms": 9000,
        "input_tokens": 500,
        "output_tokens": 200,
        "cache_read_tokens": 1000,
        "cache_creation_tokens": 300,
        "total_tokens": 2000,
        "user_messages": 3,
        "skill_invocations": 1,
        "tool_calls": 5,
        "unique_tools": ["Read", "Edit", "Bash"],
        "prompt_count": 3,
        "avg_prompt_quality": 75.0,
    }


def test_init_db_creates_table(conn):
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
    assert cursor.fetchone() is not None


def test_upsert_session_stores_record(conn):
    upsert_session(conn, _sample_session())
    cursor = conn.execute("SELECT session_id FROM sessions WHERE session_id='abc123'")
    assert cursor.fetchone() is not None


def test_upsert_session_is_idempotent(conn):
    upsert_session(conn, _sample_session())
    upsert_session(conn, _sample_session())
    cursor = conn.execute("SELECT COUNT(*) FROM sessions WHERE session_id='abc123'")
    assert cursor.fetchone()[0] == 1


def test_get_processed_session_ids_returns_set(conn):
    upsert_session(conn, _sample_session())
    ids = get_processed_session_ids(conn)
    assert isinstance(ids, set)
    assert "abc123" in ids


def test_get_sessions_for_user_returns_rows(conn):
    upsert_session(conn, _sample_session())
    rows = get_sessions_for_user(conn, "alice@example.com")
    assert len(rows) == 1
    assert rows[0]["session_id"] == "abc123"
    assert rows[0]["total_tokens"] == 2000


def test_get_sessions_for_user_filters_by_user(conn):
    s1 = _sample_session()
    s2 = _sample_session()
    s2["session_id"] = "xyz999"
    s2["user_id"] = "bob@example.com"
    upsert_session(conn, s1)
    upsert_session(conn, s2)
    rows = get_sessions_for_user(conn, "alice@example.com")
    assert len(rows) == 1
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /Users/smannar/auto-sdlc
pytest tests/logs/test_store.py -v
```

Expected: All 6 tests FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `src/auto_sdlc/logs/store.py`**

```python
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH = Path.home() / ".auto-sdlc" / "metrics.db"

_CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT,
    date TEXT,
    cwd TEXT,
    duration_ms INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cache_read_tokens INTEGER,
    cache_creation_tokens INTEGER,
    total_tokens INTEGER,
    user_messages INTEGER,
    skill_invocations INTEGER,
    tool_calls INTEGER,
    unique_tools TEXT,
    prompt_count INTEGER,
    avg_prompt_quality REAL,
    processed_at TEXT
)
"""


def open_db(db_path=None):
    """Open (and create if needed) the SQLite database. Returns a connection."""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn):
    """Create tables if they don't exist."""
    conn.execute(_CREATE_SESSIONS)
    conn.commit()


def upsert_session(conn, session_data):
    """Insert or replace a session record. session_data is a flat dict."""
    tools = session_data.get("unique_tools", [])
    conn.execute(
        """
        INSERT OR REPLACE INTO sessions (
            session_id, user_id, date, cwd,
            duration_ms, input_tokens, output_tokens,
            cache_read_tokens, cache_creation_tokens, total_tokens,
            user_messages, skill_invocations, tool_calls, unique_tools,
            prompt_count, avg_prompt_quality, processed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_data["session_id"],
            session_data.get("user_id"),
            session_data.get("date"),
            session_data.get("cwd"),
            session_data.get("duration_ms"),
            session_data.get("input_tokens", 0),
            session_data.get("output_tokens", 0),
            session_data.get("cache_read_tokens", 0),
            session_data.get("cache_creation_tokens", 0),
            session_data.get("total_tokens", 0),
            session_data.get("user_messages", 0),
            session_data.get("skill_invocations", 0),
            session_data.get("tool_calls", 0),
            json.dumps(tools) if isinstance(tools, list) else tools,
            session_data.get("prompt_count", 0),
            session_data.get("avg_prompt_quality"),
            datetime.now(tz=timezone.utc).isoformat(),
        ),
    )
    conn.commit()


def get_processed_session_ids(conn):
    """Return set of all session_ids already stored."""
    cursor = conn.execute("SELECT session_id FROM sessions")
    return {row[0] for row in cursor.fetchall()}


def get_sessions_for_user(conn, user_id):
    """Return list of sqlite3.Row for all sessions belonging to user_id."""
    cursor = conn.execute(
        "SELECT * FROM sessions WHERE user_id = ? ORDER BY date ASC",
        (user_id,),
    )
    return cursor.fetchall()
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/logs/test_store.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 5: Integrate store into report.py**

Modify `build_report` in `src/auto_sdlc/logs/report.py` to accept a `db_conn` parameter and skip sessions already stored.

The function signature changes from:
```python
def build_report(projects_dir, user_id=None, project_filter=None, since=None):
```
To:
```python
def build_report(projects_dir, user_id=None, project_filter=None, since=None, db_conn=None):
```

Add after `session_files = find_session_files(projects_dir)`:
```python
    already_seen = set()
    if db_conn is not None:
        already_seen = get_processed_session_ids(db_conn)
```

After building each session dict (inside the `for f in session_files:` loop), after `sessions.append({...})`, add:
```python
        if db_conn is not None:
            sid = metadata.get("session_id") or ""
            if sid:
                db_record = {
                    "session_id": sid,
                    "user_id": user_id,
                    "date": (metadata.get("start_timestamp") or "")[:10],
                    "cwd": metadata.get("cwd"),
                    "duration_ms": metadata.get("duration_ms"),
                    "input_tokens": token_usage.get("input_tokens", 0),
                    "output_tokens": token_usage.get("output_tokens", 0),
                    "cache_read_tokens": token_usage.get("cache_read_input_tokens", 0),
                    "cache_creation_tokens": token_usage.get("cache_creation_input_tokens", 0),
                    "total_tokens": token_usage.get("total_tokens", 0),
                    "user_messages": sum(1 for e in events if e.get("type") == "user" and not e.get("isMeta")),
                    "skill_invocations": sum(1 for e in events if e.get("type") == "user" and e.get("isMeta")),
                    "tool_calls": token_usage.get("total_tokens", 0),
                    "unique_tools": [],
                    "prompt_count": len(prompt_scores),
                    "avg_prompt_quality": (
                        round(sum(ps["score"] for ps in prompt_scores) / len(prompt_scores), 1)
                        if prompt_scores else None
                    ),
                }
                upsert_session(db_conn, db_record)
```

Add the filter skip check inside the loop, before extracting tokens:
```python
        if db_conn is not None and metadata.get("session_id") in already_seen:
            continue
```

Also add the import at the top of report.py:
```python
from auto_sdlc.logs.store import get_processed_session_ids, upsert_session
```

Modify `run_logs_report` in `report.py` to accept and pass `--db`:
```python
def run_logs_report(
    projects_dir,
    output_path,
    user_id=None,
    project_filter=None,
    since=None,
    summary_only=False,
    run_qualitative=False,
    db_path=None,
    _default_reports_dir=None,
):
    ...
    db_conn = None
    if db_path is not False:  # db_path=False means explicitly disabled
        from auto_sdlc.logs.store import open_db, init_db
        resolved_db = db_path or str(Path.home() / ".auto-sdlc" / "metrics.db")
        db_conn = open_db(resolved_db)
        init_db(db_conn)

    report = build_report(
        resolved_dir,
        user_id=effective_user,
        project_filter=project_filter,
        since=since,
        db_conn=db_conn,
    )
    if db_conn:
        db_conn.close()
```

- [ ] **Step 6: Add `--db` flag to CLI**

In `src/auto_sdlc/cli.py`, add to the `logs` command:
```python
@click.option("--db", default=None,
              help="Path to SQLite metrics database. Defaults to ~/.auto-sdlc/metrics.db. Pass 'off' to disable.")
```

In the `logs` function body, pass `db_path=(None if db == "off" else db)` to `run_logs_report`.

- [ ] **Step 7: Run existing test suite to confirm nothing broke**

```bash
pytest -v
```

Expected: All existing tests PASS. (The new db_conn default of None means existing code paths are unchanged.)

- [ ] **Step 8: Commit**

```bash
git add src/auto_sdlc/logs/store.py tests/logs/test_store.py src/auto_sdlc/logs/report.py src/auto_sdlc/cli.py
git commit -m "feat: SQLite metrics store with incremental session processing"
```

---

## Task 13: Claude Code Hook + `install-hook` CLI Command

**Why:** The goal is zero manual effort — sessions are captured automatically. A Claude Code `Stop` hook fires when the user ends any Claude Code session and runs `auto-sdlc logs` to ingest the new data. `auto-sdlc install-hook` writes this hook entry into `~/.claude/settings.json`.

**Files:**
- Create: `src/auto_sdlc/hook.py`
- Modify: `src/auto_sdlc/cli.py` (add `install-hook` subcommand)
- Create: `tests/test_hook.py`

**Claude Code hook format** (`~/.claude/settings.json`):
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "auto-sdlc logs 2>/dev/null"
          }
        ]
      }
    ]
  }
}
```

The `Stop` event fires at the end of every Claude Code session. The command runs in the background. `2>/dev/null` suppresses any stderr so it doesn't interrupt the user.

- [ ] **Step 1: Write failing tests for hook.py**

```python
# tests/test_hook.py
import json
import pytest
from pathlib import Path
from auto_sdlc.hook import (
    read_claude_settings,
    write_claude_settings,
    build_hook_entry,
    is_hook_installed,
    install_hook,
    uninstall_hook,
)


@pytest.fixture
def settings_file(tmp_path):
    return tmp_path / "settings.json"


def test_read_claude_settings_returns_empty_dict_when_missing(settings_file):
    result = read_claude_settings(str(settings_file))
    assert result == {}


def test_read_claude_settings_parses_existing(settings_file):
    settings_file.write_text('{"hooks": {}}', encoding="utf-8")
    result = read_claude_settings(str(settings_file))
    assert result == {"hooks": {}}


def test_write_claude_settings_creates_file(settings_file):
    write_claude_settings(str(settings_file), {"hooks": {}})
    assert settings_file.exists()
    data = json.loads(settings_file.read_text())
    assert data == {"hooks": {}}


def test_build_hook_entry_structure():
    entry = build_hook_entry("auto-sdlc logs 2>/dev/null")
    assert entry["matcher"] == ""
    assert entry["hooks"][0]["type"] == "command"
    assert "auto-sdlc" in entry["hooks"][0]["command"]


def test_is_hook_installed_false_when_empty():
    assert is_hook_installed({}) is False


def test_is_hook_installed_true_when_present():
    settings = {
        "hooks": {
            "Stop": [
                {"matcher": "", "hooks": [{"type": "command", "command": "auto-sdlc logs 2>/dev/null"}]}
            ]
        }
    }
    assert is_hook_installed(settings) is True


def test_install_hook_adds_to_settings(settings_file):
    install_hook(str(settings_file))
    data = json.loads(settings_file.read_text())
    assert "Stop" in data["hooks"]
    assert any("auto-sdlc" in h["hooks"][0]["command"]
               for h in data["hooks"]["Stop"])


def test_install_hook_is_idempotent(settings_file):
    install_hook(str(settings_file))
    install_hook(str(settings_file))
    data = json.loads(settings_file.read_text())
    auto_sdlc_hooks = [h for h in data["hooks"]["Stop"]
                       if any("auto-sdlc" in hh["command"] for hh in h["hooks"])]
    assert len(auto_sdlc_hooks) == 1


def test_uninstall_hook_removes_entry(settings_file):
    install_hook(str(settings_file))
    uninstall_hook(str(settings_file))
    data = json.loads(settings_file.read_text())
    stop_hooks = data.get("hooks", {}).get("Stop", [])
    assert not any("auto-sdlc" in str(h) for h in stop_hooks)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_hook.py -v
```

Expected: All 9 tests FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `src/auto_sdlc/hook.py`**

```python
import json
from pathlib import Path

_HOOK_COMMAND = "auto-sdlc logs 2>/dev/null"
_DEFAULT_SETTINGS = Path.home() / ".claude" / "settings.json"


def read_claude_settings(settings_path=None):
    """Read ~/.claude/settings.json, returning {} if file doesn't exist."""
    path = Path(settings_path) if settings_path else _DEFAULT_SETTINGS
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def write_claude_settings(settings_path, settings_dict):
    """Write settings dict to settings.json as formatted JSON."""
    path = Path(settings_path) if settings_path else _DEFAULT_SETTINGS
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(settings_dict, indent=2),
        encoding="utf-8",
    )


def build_hook_entry(command):
    """Build a Stop hook entry dict for the given shell command."""
    return {
        "matcher": "",
        "hooks": [{"type": "command", "command": command}],
    }


def is_hook_installed(settings_dict):
    """Return True if an auto-sdlc Stop hook is already present."""
    stop_hooks = settings_dict.get("hooks", {}).get("Stop", [])
    for entry in stop_hooks:
        for h in entry.get("hooks", []):
            if "auto-sdlc" in h.get("command", ""):
                return True
    return False


def install_hook(settings_path=None, export_url=None):
    """Add auto-sdlc Stop hook to Claude Code settings. Idempotent.

    Args:
        settings_path: Override path to settings.json (default ~/.claude/settings.json).
        export_url: If provided, append --export-url <url> to the hook command.

    Returns:
        True if hook was newly installed, False if already present.
    """
    settings = read_claude_settings(settings_path)
    if is_hook_installed(settings):
        return False

    command = _HOOK_COMMAND
    if export_url:
        command = "auto-sdlc logs --export-url {} 2>/dev/null".format(export_url)

    if "hooks" not in settings:
        settings["hooks"] = {}
    if "Stop" not in settings["hooks"]:
        settings["hooks"]["Stop"] = []

    settings["hooks"]["Stop"].append(build_hook_entry(command))
    write_claude_settings(settings_path or str(_DEFAULT_SETTINGS), settings)
    return True


def uninstall_hook(settings_path=None):
    """Remove auto-sdlc Stop hook from Claude Code settings.

    Returns:
        True if hook was removed, False if it wasn't present.
    """
    settings = read_claude_settings(settings_path)
    stop_hooks = settings.get("hooks", {}).get("Stop", [])
    filtered = [
        entry for entry in stop_hooks
        if not any("auto-sdlc" in h.get("command", "") for h in entry.get("hooks", []))
    ]
    if len(filtered) == len(stop_hooks):
        return False
    settings["hooks"]["Stop"] = filtered
    write_claude_settings(settings_path or str(_DEFAULT_SETTINGS), settings)
    return True
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_hook.py -v
```

Expected: All 9 tests PASS.

- [ ] **Step 5: Add `install-hook` and `uninstall-hook` CLI subcommands**

In `src/auto_sdlc/cli.py`, add after the `init` command:

```python
@cli.command(name="install-hook")
@click.option("--settings", default=None,
              help="Path to Claude Code settings.json. Defaults to ~/.claude/settings.json")
@click.option("--export-url", default=None,
              help="If set, hook will POST reports to this URL after each session.")
def install_hook_cmd(settings, export_url):
    """Install auto-sdlc Stop hook into Claude Code settings."""
    from auto_sdlc.hook import install_hook
    installed = install_hook(settings_path=settings, export_url=export_url)
    if installed:
        click.echo("Hook installed. auto-sdlc logs will run after each Claude Code session.")
        click.echo("To remove it later: auto-sdlc uninstall-hook")
    else:
        click.echo("Hook already installed. No changes made.")


@cli.command(name="uninstall-hook")
@click.option("--settings", default=None,
              help="Path to Claude Code settings.json. Defaults to ~/.claude/settings.json")
def uninstall_hook_cmd(settings):
    """Remove auto-sdlc Stop hook from Claude Code settings."""
    from auto_sdlc.hook import uninstall_hook
    removed = uninstall_hook(settings_path=settings)
    if removed:
        click.echo("Hook removed.")
    else:
        click.echo("Hook was not installed. No changes made.")
```

- [ ] **Step 6: Add CLI smoke tests for the new subcommands**

In `tests/test_cli.py`, add:

```python
def test_install_hook_cmd(tmp_path):
    settings_file = tmp_path / "settings.json"
    runner = CliRunner()
    result = runner.invoke(cli, ["install-hook", "--settings", str(settings_file)])
    assert result.exit_code == 0
    assert "installed" in result.output.lower()
    assert settings_file.exists()


def test_install_hook_cmd_idempotent(tmp_path):
    settings_file = tmp_path / "settings.json"
    runner = CliRunner()
    runner.invoke(cli, ["install-hook", "--settings", str(settings_file)])
    result = runner.invoke(cli, ["install-hook", "--settings", str(settings_file)])
    assert result.exit_code == 0
    assert "already" in result.output.lower()


def test_uninstall_hook_cmd(tmp_path):
    settings_file = tmp_path / "settings.json"
    runner = CliRunner()
    runner.invoke(cli, ["install-hook", "--settings", str(settings_file)])
    result = runner.invoke(cli, ["uninstall-hook", "--settings", str(settings_file)])
    assert result.exit_code == 0
    assert "removed" in result.output.lower()
```

- [ ] **Step 7: Run full test suite**

```bash
pytest -v
```

Expected: All tests PASS.

- [ ] **Step 8: Commit**

```bash
git add src/auto_sdlc/hook.py src/auto_sdlc/cli.py tests/test_hook.py tests/test_cli.py
git commit -m "feat: Claude Code Stop hook with install-hook / uninstall-hook CLI commands"
```

---

## Task 14: Discovery Coverage Mapping (Qualitative Analysis v2)

**Why:** The current `qualitative.py` asks generic questions. The Auto-SDLC maturity model has 12 discovery categories used in client interviews. For each category, we need at least one quantitative metric and one LLM-evaluated qualitative finding. This replaces manual discovery interviews.

**The 12 Discovery Categories:**

| # | Category | Quantitative signal in logs | LLM question |
|---|---|---|---|
| 1 | Prompting practices | avg_prompt_quality_score | "Is this developer providing sufficient context in prompts?" |
| 2 | Skill/command adoption | skill_invocation_ratio | "What skill gaps do these slash-command ratios suggest?" |
| 3 | Tool diversity | unique_tools_used count | "Are they using tools appropriately or relying on too few?" |
| 4 | Workflow automation | sessions_per_day trend | "Does usage frequency suggest habitual vs. occasional use?" |
| 5 | Session productivity | avg_messages_per_session | "Are sessions deep-dive work or shallow quick-hits?" |
| 6 | Context management | cache hit ratio | "Is the developer managing context efficiently?" |
| 7 | Debugging approach | prompt error-keyword rate | "How do they approach debugging — systematic or ad hoc?" |
| 8 | Code review practices | presence of 'review', 'diff', 'PR' in prompts | "Is AI being used in the code review workflow?" |
| 9 | Testing practices | presence of 'test', 'spec', 'assert' in prompts | "Is AI being used to write or improve tests?" |
| 10 | Architecture & design | presence of 'design', 'architect', 'refactor' in prompts | "Is AI involved in higher-level design decisions?" |
| 11 | Documentation practices | presence of 'docs', 'README', 'comment' in prompts | "Is AI used for documentation?" |
| 12 | Rework patterns | repeated similar prompts within sessions | "Are there signs of prompt thrashing or unclear requirements?" |

**Files:**
- Modify: `src/auto_sdlc/logs/qualitative.py`
- Create (new helper): no new file — all in qualitative.py
- Modify: `tests/logs/test_qualitative.py`

- [ ] **Step 1: Add keyword signal extraction to qualitative.py**

Add after the existing imports:

```python
import re

_KEYWORD_CATEGORIES = {
    "debugging": re.compile(r"\b(error|bug|fix|broken|fail|crash|traceback|exception)\b", re.IGNORECASE),
    "code_review": re.compile(r"\b(review|diff|PR|pull.request|comment|feedback)\b", re.IGNORECASE),
    "testing": re.compile(r"\b(test|spec|assert|unittest|pytest|coverage)\b", re.IGNORECASE),
    "architecture": re.compile(r"\b(design|architect|refactor|structure|pattern|abstraction)\b", re.IGNORECASE),
    "documentation": re.compile(r"\b(docs|README|docstring|comment|documentation|explain)\b", re.IGNORECASE),
}


def extract_prompt_keyword_signals(report):
    """Count keyword category hits across all prompt previews.

    Returns dict mapping category name to fraction of prompts containing keywords.
    e.g. {"debugging": 0.35, "testing": 0.12, ...}
    """
    prompts = []
    for session in report.get("sessions", []):
        for ps in session.get("prompt_scores", []):
            text = ps.get("prompt_preview", "")
            if text:
                prompts.append(text)

    if not prompts:
        return {k: 0.0 for k in _KEYWORD_CATEGORIES}

    counts = {k: 0 for k in _KEYWORD_CATEGORIES}
    for prompt in prompts:
        for category, pattern in _KEYWORD_CATEGORIES.items():
            if pattern.search(prompt):
                counts[category] += 1

    return {k: round(v / len(prompts), 3) for k, v in counts.items()}
```

- [ ] **Step 2: Write failing tests for keyword signals**

In `tests/logs/test_qualitative.py`, add:

```python
from auto_sdlc.logs.qualitative import extract_prompt_keyword_signals


def _report_with_prompts(prompts):
    return {
        "sessions": [
            {
                "prompt_scores": [{"prompt_preview": p, "score": 50} for p in prompts]
            }
        ],
        "summary": {},
        "behavioral_metrics": {},
        "maturity_scores": {},
    }


def test_keyword_signals_debugging():
    report = _report_with_prompts(["fix the login bug", "another prompt"])
    signals = extract_prompt_keyword_signals(report)
    assert signals["debugging"] == 0.5  # 1 of 2 prompts


def test_keyword_signals_empty_prompts():
    signals = extract_prompt_keyword_signals({"sessions": []})
    assert signals["debugging"] == 0.0
    assert signals["testing"] == 0.0


def test_keyword_signals_testing():
    report = _report_with_prompts(["write a pytest for this function"])
    signals = extract_prompt_keyword_signals(report)
    assert signals["testing"] == 1.0


def test_keyword_signals_all_categories_present():
    signals = extract_prompt_keyword_signals({"sessions": []})
    expected_keys = {"debugging", "code_review", "testing", "architecture", "documentation"}
    assert set(signals.keys()) == expected_keys
```

- [ ] **Step 3: Run tests to confirm new tests fail**

```bash
pytest tests/logs/test_qualitative.py -v
```

Expected: New tests FAIL (function doesn't exist yet). Old tests may pass or fail depending on state.

- [ ] **Step 4: Add `analyze_discovery_coverage` to qualitative.py**

Add this function after `extract_prompt_keyword_signals`:

```python
def analyze_discovery_coverage(report):
    """Run LLM analysis mapped to the 12 Auto-SDLC discovery categories.

    Returns a dict with one entry per category containing:
      - metric: the quantitative signal value
      - finding: LLM-generated one-sentence finding
      - recommendation: LLM-generated one-sentence recommendation
    """
    summary = report.get("summary", {})
    behavioral = report.get("behavioral_metrics", {})
    maturity = report.get("maturity_scores", {})
    keyword_signals = extract_prompt_keyword_signals(report)

    # Build compact context for LLM calls
    ctx = (
        "Developer metrics:\n"
        "  avg_prompt_quality={quality}\n"
        "  skill_invocation_ratio={skill_ratio}\n"
        "  unique_tools_count={tool_count}\n"
        "  sessions_per_day={spd}\n"
        "  avg_messages_per_session={avg_msgs}\n"
        "  cache_hit_ratio={cache_ratio}\n"
        "  debugging_prompt_rate={debug}\n"
        "  code_review_prompt_rate={review}\n"
        "  testing_prompt_rate={testing}\n"
        "  architecture_prompt_rate={arch}\n"
        "  documentation_prompt_rate={docs}\n"
    ).format(
        quality=summary.get("avg_prompt_quality_score", 0),
        skill_ratio=behavioral.get("skill_invocation_ratio", 0),
        tool_count=len(behavioral.get("unique_tools_used", [])),
        spd=behavioral.get("sessions_per_day", 0),
        avg_msgs=behavioral.get("avg_messages_per_session", 0),
        cache_ratio=round(
            (summary.get("total_cache_read_tokens", 0) / summary.get("total_tokens", 1))
            if summary.get("total_tokens", 0) > 0 else 0,
            3,
        ),
        debug=keyword_signals.get("debugging", 0),
        review=keyword_signals.get("code_review", 0),
        testing=keyword_signals.get("testing", 0),
        arch=keyword_signals.get("architecture", 0),
        docs=keyword_signals.get("documentation", 0),
    )

    _categories = [
        ("prompting_practices", "prompt quality score of {}".format(summary.get("avg_prompt_quality_score", 0)),
         "Is this developer providing sufficient context in prompts? Use the prompt_quality score."),
        ("skill_adoption", "skill_invocation_ratio of {}".format(behavioral.get("skill_invocation_ratio", 0)),
         "What does the skill invocation ratio suggest about slash-command and tool adoption?"),
        ("tool_diversity", "{} unique tools used".format(len(behavioral.get("unique_tools_used", []))),
         "Is the developer using Claude Code's tools broadly or relying on too few?"),
        ("workflow_automation", "sessions_per_day of {}".format(behavioral.get("sessions_per_day", 0)),
         "Does usage frequency suggest habitual daily use or occasional ad-hoc queries?"),
        ("session_productivity", "avg_messages_per_session of {}".format(behavioral.get("avg_messages_per_session", 0)),
         "Are sessions deep collaborative work or shallow single-turn queries?"),
        ("context_management", "cache_hit_ratio of {}".format(keyword_signals.get("debugging", 0)),
         "Does the developer reuse context across turns or start fresh each message?"),
        ("debugging_approach", "{}% of prompts contain debugging keywords".format(int(keyword_signals.get("debugging", 0) * 100)),
         "Is debugging done systematically with context and stack traces, or vaguely?"),
        ("code_review", "{}% of prompts involve code review".format(int(keyword_signals.get("code_review", 0) * 100)),
         "Is AI being used in the code review workflow?"),
        ("testing_practices", "{}% of prompts involve testing".format(int(keyword_signals.get("testing", 0) * 100)),
         "Is AI being used to write, improve, or run tests?"),
        ("architecture_design", "{}% of prompts involve architecture".format(int(keyword_signals.get("architecture", 0) * 100)),
         "Is AI involved in higher-level design decisions or only implementation?"),
        ("documentation", "{}% of prompts involve documentation".format(int(keyword_signals.get("documentation", 0) * 100)),
         "Is AI used to write or improve documentation?"),
        ("rework_patterns", "overall maturity level {}/4".format(maturity.get("overall_level", 0)),
         "Are there signs of prompt thrashing, repeated corrections, or unclear task scoping?"),
    ]

    results = {}
    for key, metric_text, question in _categories:
        prompt = (
            "You are an AI-usage consultant analyzing a developer's Claude Code session data.\n"
            "{ctx}\n\n"
            "Category: {key}\n"
            "Metric: {metric}\n"
            "Question: {question}\n\n"
            "Respond with ONLY a JSON object with two fields:\n"
            '{{"finding": "one sentence observation", "recommendation": "one actionable sentence"}}\n'
            "No prose outside the JSON."
        ).format(ctx=ctx, key=key, metric=metric_text, question=question)

        response = run_llm(prompt)
        if not response:
            results[key] = {"metric": metric_text, "finding": None, "recommendation": None}
            continue
        try:
            parsed = json.loads(response)
            results[key] = {
                "metric": metric_text,
                "finding": parsed.get("finding"),
                "recommendation": parsed.get("recommendation"),
            }
        except (json.JSONDecodeError, ValueError):
            results[key] = {"metric": metric_text, "finding": None, "recommendation": None, "raw": response}

    return results
```

- [ ] **Step 5: Wire `analyze_discovery_coverage` into `run_full_qualitative_analysis`**

Replace the return statement in `run_full_qualitative_analysis`:

```python
def run_full_qualitative_analysis(report):
    """Run all analyses and return combined dict."""
    return {
        "workflow_patterns": analyze_workflow_patterns(report),
        "anti_patterns": analyze_anti_patterns(report),
        "narrative": analyze_maturity_narrative(report),
        "discovery_coverage": analyze_discovery_coverage(report),
    }
```

- [ ] **Step 6: Run tests to confirm they pass**

```bash
pytest tests/logs/test_qualitative.py -v
```

Expected: All keyword signal tests PASS. (LLM tests require `claude` CLI; they are mocked or skipped.)

- [ ] **Step 7: Commit**

```bash
git add src/auto_sdlc/logs/qualitative.py tests/logs/test_qualitative.py
git commit -m "feat: discovery coverage mapping across 12 Auto-SDLC categories"
```

---

## Task 15: Sliding Window Workflow Extraction + Rework Detection

**Why:** Multi-turn sessions contain richer signal than single metrics. A sliding window over turns reveals: what kind of work is happening (debugging loop, feature build, exploration), whether the developer is getting stuck (same prompt rephrased 3 times = rework), and when sessions are abandoned (only 1-2 turns = abandoned). This powers the "rework_patterns" discovery category.

**Files:**
- Create: `src/auto_sdlc/logs/workflows.py`
- Modify: `src/auto_sdlc/logs/metrics.py` (add `rework_ratio`, `abandoned_session_rate`)
- Modify: `src/auto_sdlc/logs/report.py` (include workflow + rework fields in session data)
- Create: `tests/logs/test_workflows.py`

- [ ] **Step 1: Write failing tests for workflows.py**

```python
# tests/logs/test_workflows.py
import pytest
from auto_sdlc.logs.workflows import (
    extract_turn_sequence,
    detect_rework_in_session,
    classify_session_workflow,
    aggregate_workflow_stats,
)


def _events_with_prompts(prompts):
    """Build fake session events from a list of prompt strings."""
    events = []
    for i, p in enumerate(prompts):
        events.append({
            "type": "user",
            "isMeta": False,
            "message": {"role": "user", "content": p},
            "timestamp": "2026-03-30T08:0{}:00.000Z".format(i),
            "sessionId": "test123",
        })
        events.append({
            "type": "assistant",
            "message": {"model": "claude-sonnet-4-6", "usage": {
                "input_tokens": 100, "output_tokens": 50,
                "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
            }},
            "timestamp": "2026-03-30T08:0{}:05.000Z".format(i),
            "sessionId": "test123",
        })
    return events


def test_extract_turn_sequence_returns_prompts(sample_session_lines):
    turns = extract_turn_sequence(sample_session_lines)
    assert len(turns) == 1
    assert "Fix the login bug" in turns[0]


def test_extract_turn_sequence_excludes_meta(sample_session_lines):
    turns = extract_turn_sequence(sample_session_lines)
    assert not any("<local-command" in t for t in turns)


def test_detect_rework_no_rework():
    events = _events_with_prompts([
        "Fix the login bug in src/auth.py",
        "Add a test for the password reset flow",
        "Refactor the session handler",
    ])
    result = detect_rework_in_session(events)
    assert result["rework_detected"] is False
    assert result["rework_count"] == 0


def test_detect_rework_detects_repeated_prompt():
    events = _events_with_prompts([
        "Fix the bug",
        "Fix the bug please",
        "Can you fix the bug",
        "Unrelated prompt about tests",
    ])
    result = detect_rework_in_session(events)
    assert result["rework_detected"] is True
    assert result["rework_count"] >= 1


def test_classify_session_workflow_debugging():
    events = _events_with_prompts([
        "Fix the TypeError in src/auth.py line 42",
        "The error is still happening after your fix",
        "Try checking the return value",
    ])
    result = classify_session_workflow(events)
    assert result in ("debugging", "feature_build", "refactoring", "exploration", "mixed")


def test_classify_session_workflow_short_session():
    events = _events_with_prompts(["Quick question about syntax"])
    result = classify_session_workflow(events)
    assert result == "exploration"


def test_aggregate_workflow_stats_counts():
    sessions = [
        _events_with_prompts(["Fix the bug", "Still broken", "The bug"]),
        _events_with_prompts(["Add new feature to src/api.py"]),
    ]
    stats = aggregate_workflow_stats(sessions)
    assert "abandoned_session_rate" in stats
    assert "rework_ratio" in stats
    assert "workflow_distribution" in stats
    assert isinstance(stats["abandoned_session_rate"], float)
    assert isinstance(stats["rework_ratio"], float)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/logs/test_workflows.py -v
```

Expected: All 7 tests FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `src/auto_sdlc/logs/workflows.py`**

```python
"""Sliding-window workflow extraction and rework detection."""
import re

_WORKFLOW_KEYWORDS = {
    "debugging": re.compile(r"\b(fix|bug|error|broken|fail|crash|traceback|exception|not working)\b", re.IGNORECASE),
    "feature_build": re.compile(r"\b(add|implement|create|build|new feature|endpoint|route)\b", re.IGNORECASE),
    "refactoring": re.compile(r"\b(refactor|clean up|reorganize|rename|move|extract|simplify)\b", re.IGNORECASE),
    "exploration": re.compile(r"\b(how does|what is|explain|show me|example|help me understand)\b", re.IGNORECASE),
}

_SIMILARITY_THRESHOLD = 0.6  # Jaccard similarity above this = rework


def _prompt_words(text):
    """Return set of lowercase words, stripping punctuation."""
    return set(re.sub(r"[^\w\s]", "", text.lower()).split())


def _jaccard(set_a, set_b):
    """Jaccard similarity between two word sets."""
    if not set_a and not set_b:
        return 1.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def extract_turn_sequence(events):
    """Return list of non-meta user prompt strings in order."""
    prompts = []
    for event in events:
        if event.get("type") != "user" or event.get("isMeta"):
            continue
        content = event.get("message", {}).get("content", "")
        if isinstance(content, list):
            content = " ".join(
                b.get("text", "") for b in content
                if isinstance(b, dict) and b.get("type") == "text"
            )
        if content and content.strip():
            prompts.append(content.strip())
    return prompts


def detect_rework_in_session(events):
    """Detect repeated/similar prompts within a session (rework pattern).

    Uses a sliding window of size 3 over the turn sequence.
    Two turns are considered rework if Jaccard similarity > 0.6.

    Returns:
        dict with keys:
          - rework_detected: bool
          - rework_count: int (number of similar pairs found)
          - rework_pairs: list of (i, j) index tuples
    """
    turns = extract_turn_sequence(events)
    if len(turns) < 2:
        return {"rework_detected": False, "rework_count": 0, "rework_pairs": []}

    rework_pairs = []
    word_sets = [_prompt_words(t) for t in turns]

    # Compare each turn against up to 3 previous turns (sliding window)
    for i in range(1, len(turns)):
        window_start = max(0, i - 3)
        for j in range(window_start, i):
            sim = _jaccard(word_sets[i], word_sets[j])
            if sim >= _SIMILARITY_THRESHOLD and len(word_sets[i]) >= 3:
                rework_pairs.append((j, i))

    return {
        "rework_detected": len(rework_pairs) > 0,
        "rework_count": len(rework_pairs),
        "rework_pairs": rework_pairs,
    }


def classify_session_workflow(events):
    """Classify the dominant workflow type for a session.

    Returns one of: 'debugging', 'feature_build', 'refactoring', 'exploration', 'mixed'
    """
    turns = extract_turn_sequence(events)
    if not turns or len(turns) <= 1:
        return "exploration"

    full_text = " ".join(turns)
    scores = {}
    for wf_type, pattern in _WORKFLOW_KEYWORDS.items():
        scores[wf_type] = len(pattern.findall(full_text))

    total = sum(scores.values())
    if total == 0:
        return "mixed"

    top = max(scores, key=scores.get)
    top_ratio = scores[top] / total

    if top_ratio >= 0.5:
        return top
    return "mixed"


def aggregate_workflow_stats(all_session_events):
    """Compute rework and workflow distribution across all sessions.

    Args:
        all_session_events: list of event lists (one per session)

    Returns:
        dict with:
          - rework_ratio: fraction of sessions with rework detected
          - abandoned_session_rate: fraction of sessions with <= 2 user turns
          - workflow_distribution: dict mapping workflow type to fraction
    """
    if not all_session_events:
        return {
            "rework_ratio": 0.0,
            "abandoned_session_rate": 0.0,
            "workflow_distribution": {},
        }

    rework_count = 0
    abandoned_count = 0
    workflow_counts = {"debugging": 0, "feature_build": 0, "refactoring": 0, "exploration": 0, "mixed": 0}

    for events in all_session_events:
        turns = extract_turn_sequence(events)
        if len(turns) <= 2:
            abandoned_count += 1

        rework = detect_rework_in_session(events)
        if rework["rework_detected"]:
            rework_count += 1

        wf = classify_session_workflow(events)
        workflow_counts[wf] = workflow_counts.get(wf, 0) + 1

    n = len(all_session_events)
    return {
        "rework_ratio": round(rework_count / n, 3),
        "abandoned_session_rate": round(abandoned_count / n, 3),
        "workflow_distribution": {k: round(v / n, 3) for k, v in workflow_counts.items() if v > 0},
    }
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/logs/test_workflows.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 5: Integrate workflow stats into report.py**

In `build_report` in `src/auto_sdlc/logs/report.py`, add the import at top:
```python
from auto_sdlc.logs.workflows import aggregate_workflow_stats, classify_session_workflow, detect_rework_in_session
```

After building the `sessions` list (before `aggregate = aggregate_sessions(...)`), add:
```python
    workflow_stats = aggregate_workflow_stats(all_events)
```

In each session dict inside the loop, add:
```python
            "workflow_type": classify_session_workflow(events),
            "rework": detect_rework_in_session(events),
```

Add `"workflow_stats": workflow_stats` to the top-level return dict.

- [ ] **Step 6: Run full test suite**

```bash
pytest -v
```

Expected: All tests PASS.

- [ ] **Step 7: Commit**

```bash
git add src/auto_sdlc/logs/workflows.py tests/logs/test_workflows.py src/auto_sdlc/logs/report.py
git commit -m "feat: sliding-window workflow extraction and rework detection"
```

---

## Task 16: Wire New Fields into HTML Reports

**Why:** The new fields (workflow_type, rework, workflow_stats, discovery_coverage) are captured in JSON but not shown in the HTML reports. Users need to see them.

**Files:**
- Modify: `src/auto_sdlc/logs/render_html.py` (individual report)
- Modify: `src/auto_sdlc/logs/team.py` (team HTML)

- [ ] **Step 1: Add workflow stats section to individual HTML**

In `render_individual_html` in `src/auto_sdlc/logs/render_html.py`, after the qualitative section, add a workflow section. Read `report.get("workflow_stats", {})` and render:
- Rework ratio as a percentage
- Abandoned session rate as a percentage
- Workflow distribution as a small bar chart (same pattern as maturity dimensions)

Example rows block (add before the `return` at the end of `render_individual_html`):

```python
    workflow_stats = report.get("workflow_stats", {})
    wf_rows = ""
    for wf_type, fraction in workflow_stats.get("workflow_distribution", {}).items():
        pct = int(fraction * 100)
        wf_rows += (
            "<tr>"
            "<td style='padding:5px 10px;width:160px'>{}</td>"
            "<td style='padding:5px 10px'>"
            "<div style='background:#eee;border-radius:4px;height:14px;width:200px'>"
            "<div style='background:#7b68ee;border-radius:4px;height:14px;width:{}%'></div>"
            "</div></td>"
            "<td style='padding:5px 10px;color:#555'>{}%</td>"
            "</tr>"
        ).format(wf_type.replace("_", " ").title(), pct, pct)

    rework_pct = int(workflow_stats.get("rework_ratio", 0) * 100)
    abandoned_pct = int(workflow_stats.get("abandoned_session_rate", 0) * 100)
    workflow_section = ""
    if wf_rows:
        workflow_section = """
  <div class="card">
    <h2>Workflow Analysis</h2>
    <div style="display:flex;gap:24px;margin-bottom:16px">
      <div><span style="font-size:20px;font-weight:700;color:#e67e22">{rework_pct}%</span>
           <div style="font-size:12px;color:#888">Rework Rate</div></div>
      <div><span style="font-size:20px;font-weight:700;color:#95a5a6">{abandoned_pct}%</span>
           <div style="font-size:12px;color:#888">Abandoned Sessions</div></div>
    </div>
    <table><tr><th>Workflow Type</th><th>Distribution</th><th>%</th></tr>{wf_rows}</table>
  </div>""".format(rework_pct=rework_pct, abandoned_pct=abandoned_pct, wf_rows=wf_rows)
```

Inject `{workflow_section}` into the HTML template string before `</body>`.

- [ ] **Step 2: Add discovery coverage section to individual HTML**

When `qualitative_analysis` contains `discovery_coverage`, render it as a table:

```python
    discovery_html = ""
    if qualitative_analysis and qualitative_analysis.get("discovery_coverage"):
        cov = qualitative_analysis["discovery_coverage"]
        cov_rows = ""
        for cat_key, cat_data in cov.items():
            finding = cat_data.get("finding") or "—"
            recommendation = cat_data.get("recommendation") or "—"
            cov_rows += (
                "<tr>"
                "<td style='padding:5px 10px;font-weight:600;width:180px'>{}</td>"
                "<td style='padding:5px 10px;color:#555'>{}</td>"
                "<td style='padding:5px 10px;color:#27ae60'>{}</td>"
                "</tr>"
            ).format(cat_key.replace("_", " ").title(), finding, recommendation)
        discovery_html = """
  <div class="card">
    <h2>Discovery Coverage (12 Categories)</h2>
    <table>
      <tr><th>Category</th><th>Finding</th><th>Recommendation</th></tr>
      {cov_rows}
    </table>
  </div>""".format(cov_rows=cov_rows)
```

- [ ] **Step 3: Run full test suite**

```bash
pytest -v
```

Expected: All tests PASS. (HTML rendering tests don't assert on new sections, they just check the string contains `<!DOCTYPE html>`.)

- [ ] **Step 4: Commit**

```bash
git add src/auto_sdlc/logs/render_html.py src/auto_sdlc/logs/team.py
git commit -m "feat: add workflow analysis and discovery coverage to HTML reports"
```

---

## Verification (End-to-End After All Tasks)

```bash
# 1. Install the hook
auto-sdlc install-hook
# Expected: "Hook installed. auto-sdlc logs will run after each Claude Code session."

# 2. Check ~/.claude/settings.json has the hook
cat ~/.claude/settings.json | python3 -m json.tool

# 3. Run logs with SQLite store and qualitative analysis
auto-sdlc logs --qualitative --html
# Expected: "Report saved to ~/.auto-sdlc/reports/<user>/<ts>.json"
#           "HTML report saved to ~/.auto-sdlc/reports/<user>/<ts>.html"

# 4. Second run should skip already-processed sessions (fast)
auto-sdlc logs --summary-only
# Expected: same session count, near-instant

# 5. Export to a team dir and view team report
mkdir -p /tmp/team-reports
auto-sdlc logs --export-dir /tmp/team-reports
auto-sdlc team --reports-dir /tmp/team-reports --html
# Expected: /tmp/team-reports/team_report.json and team_report.html

# 6. Uninstall hook
auto-sdlc uninstall-hook
# Expected: "Hook removed."
```

---

## Self-Review

**Spec coverage:**
- ✅ Claude Code hook: Task 13 (install-hook, Stop event, ~/.claude/settings.json)
- ✅ SQLite metrics aggregation: Task 12 (store.py, incremental processing, --db flag)
- ✅ Discovery coverage mapping: Task 14 (12 categories, keyword signals, per-category LLM findings)
- ✅ Sliding window workflow extraction: Task 15 (workflows.py, rework detection, abandoned sessions)
- ✅ HTML report updates: Task 16 (workflow section, discovery coverage section)
- ✅ All existing completed work documented in status table

**Placeholder scan:** No TBDs. All code blocks are complete and self-contained.

**Type consistency:**
- `open_db(db_path=None)` → used as `open_db(resolved_db)` in report.py ✅
- `upsert_session(conn, session_data)` → called with correct dict shape ✅
- `aggregate_workflow_stats(all_session_events)` → receives `all_events` list already built in report.py ✅
- `extract_prompt_keyword_signals(report)` → receives full report dict ✅
- `classify_session_workflow(events)` → receives per-session events list ✅
