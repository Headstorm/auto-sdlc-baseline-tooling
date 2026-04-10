# Plan: Bulk Ingest for Organization Analysis

## Context

**Problem**: The tool only processes one developer's logs at a time. An admin analyzing the whole team must manually run `auto-sdlc logs` for each developer individually. No single command for "collect and analyze everyone at once."

**User's need**: One-time bulk ingestion — run one command, process all users, get team dashboard. No continuous monitoring. No hooks.

**What's already built**: All analysis modules work (parser, scorer, metrics, maturity, HTML, export, team rollup). The missing piece is a command that **discovers users from a directory and processes them all in one shot**.

---

## Implementation

### New Command: `auto-sdlc ingest`

```bash
# Most common usage
auto-sdlc ingest --logs-root /shared/claude-logs/ --output-dir ./reports --html

# With CSV mapping
auto-sdlc ingest --users-file users.csv --output-dir ./reports --html

# Time-filtered
auto-sdlc ingest --logs-root /exports/ --since 2025-01-01 --output-dir ./q1-reports
```

### Directory Layouts Supported

**Layout A** — standard (each user has `projects/`):
```
/shared/claude-logs/
├── alice/
│   └── projects/
│       └── myapp/
│           └── sessions.jsonl
└── bob/
    └── projects/
        └── backend/
            └── sessions.jsonl
```

**Layout B** — flat (JSONL directly in user dir):
```
/shared/claude-logs/
├── alice@company.com/
│   ├── session_001.jsonl
│   └── session_002.jsonl
└── bob@company.com/
    └── session_001.jsonl
```

**CSV users-file**:
```csv
# users.csv
alice@company.com,/data/alice/.claude/projects/
bob@company.com,/data/bob/.claude/projects/
carol@company.com,/exports/carol/
```

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `src/auto_sdlc/cli.py` | Add `ingest` command (+25 lines) | CLI entry point |
| `src/auto_sdlc/logs/ingest.py` | **New** (~110 lines) | Orchestration: discover users → process each → aggregate |
| `tests/test_ingest.py` | **New** (~90 lines) | 5 test cases covering both layouts + CSV |

### What Gets Reused (no changes needed)

- `build_report(projects_dir, user_id, since)` — parse one user's logs
- `run_full_qualitative_analysis(report)` — optional LLM analysis
- `export_report_to_dir(report, dest_dir)` — save JSON
- `render_individual_html(report)` — per-user HTML
- `build_team_report_from_dir(output_dir)` — aggregate all reports
- `render_team_html(team_report)` — team HTML dashboard

### Execution Order

1. Write `tests/test_ingest.py` (TDD)
2. Write `src/auto_sdlc/logs/ingest.py`
3. Add `ingest` command to `cli.py`
4. Run full test suite
5. Manual smoke test
6. Commit

---

## Expected Behavior After Implementation

```bash
$ auto-sdlc ingest --logs-root /shared/claude-logs/ --output-dir ./reports --html

Processing 3 users from /shared/claude-logs/

  alice@company.com        42 sessions   Intermediate   ✓
  bob@company.com          17 sessions   Basic          ✓
  carol@company.com        91 sessions   Advanced       ✓

Reports saved to: ./reports/
  alice_at_company_com_2026-04-08_120000.json
  bob_at_company_com_2026-04-08_120001.json
  carol_at_company_com_2026-04-08_120002.json
  team_report.json
  team_report.html
```

---

## Future Enhancements (Deferred)

| Task | What it adds |
|------|-------------|
| SQLite store | Skip re-processing sessions on repeated runs (Task 12) |
| Discovery mapping | Map LLM output to 12 discovery categories (Task 14) |
| Workflow extraction | Detect multi-session patterns, rework, abandoned tasks (Task 15) |
| Updated HTML | Add workflow + discovery sections to reports (Task 16) |
| Hook system | **Out of scope** — user doesn't want continuous monitoring |

---

## Implementation Details: `ingest.py`

```python
def discover_users_from_dir(logs_root: Path) -> list[tuple[str, Path]]:
    """Walk logs_root. Each subdir = one user. Auto-detect layout A vs B."""
    
def load_users_from_csv(users_file: Path) -> list[tuple[str, Path]]:
    """Read CSV: user_id,logs_path. Supports # comments."""

def run_bulk_ingest(logs_root, output_dir, since=None, html=False,
                   qualitative=False, users_file=None):
    """
    1. Discover users from dir structure or CSV
    2. For each user:
       - build_report(projects_dir, user_id, since=since)
       - optionally run qualitative analysis
       - save JSON via export_report_to_dir()
       - optionally render individual HTML
    3. build_team_report_from_dir(output_dir)
    4. save team_report.json + team_report.html
    5. print summary table to stdout
    """
```

---

## Verification

1. Create test structure:
   ```bash
   mkdir -p /tmp/test-logs/alice/projects/myapp
   echo '{"type":"say","message":{"role":"user","content":"test"}}' > /tmp/test-logs/alice/projects/myapp/s.jsonl
   ```

2. Run:
   ```bash
   auto-sdlc ingest --logs-root /tmp/test-logs --output-dir /tmp/results --html
   ```

3. Check:
   ```bash
   ls /tmp/results/  # should have alice's JSON + team_report.json + team_report.html
   cat /tmp/results/team_report.json | grep team_size  # should be 1
   ```

4. Open `/tmp/results/team_report.html` in browser — verify styling and content
