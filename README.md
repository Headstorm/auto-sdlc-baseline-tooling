# Auto-SDLC Baseline Tooling

A Python CLI for baselining developer AI maturity — parse Claude Code session logs, score prompt quality, measure behavioral patterns, generate individual and team-level maturity reports, and collect data centrally for team-wide analysis.

Built to automate the discovery process used in Auto-SDLC engagements: instead of interviewing developers about how they use Claude, we read the actual logs.

---

## Installation

**Requirements:** Python 3.9+

```bash
git clone https://github.com/Headstorm/auto-sdlc-baseline-tooling.git
cd auto-sdlc-baseline-tooling
pip3 install -e .
```

For the central collection server, also install server dependencies:
```bash
pip3 install -e ".[server]"
```

Add to PATH (add to your `~/.zshrc` or `~/.bashrc`):
```bash
export PATH="$PATH:/Users/<you>/Library/Python/3.9/bin"
```

---

## Commands

### `auto-sdlc logs`

Analyze Claude Code JSONL session files from `~/.claude/projects/`. Generates a full maturity report with behavioral metrics, dimension scores, and optional LLM qualitative analysis.

```bash
auto-sdlc logs [OPTIONS]
```

| Option | Description |
|---|---|
| `--projects-dir PATH` | Override the default `~/.claude/projects/` path |
| `--output PATH` | Save JSON report to this path. Defaults to `~/.auto-sdlc/reports/<user>/<timestamp>.json` |
| `--project TEXT` | Filter sessions where working directory contains this string |
| `--since YYYY-MM-DD` | Only include sessions on or after this date |
| `--user-id TEXT` | Tag the report with a developer identifier (email or name) |
| `--summary-only` | Print a short summary to stdout instead of saving the full report |
| `--html` | Also render a self-contained HTML report alongside the JSON |
| `--qualitative` | Run LLM qualitative analysis via `claude -p` (slow, requires claude CLI) |
| `--export-dir PATH` | Copy the report JSON to this directory (for team aggregation via shared folder) |
| `--export-url URL` | POST the report JSON to this URL (for central server collection) |

**Examples:**

```bash
# Run and save to default location (~/.auto-sdlc/reports/)
auto-sdlc logs

# Quick summary to stdout
auto-sdlc logs --summary-only

# Full report with HTML visualization
auto-sdlc logs --html

# Full report with LLM qualitative analysis
auto-sdlc logs --qualitative --html

# Filter to a specific project and date range
auto-sdlc logs --project semios --since 2026-01-01

# Tag report with your identity
auto-sdlc logs --user-id alice@company.com --html

# Export to shared folder for team rollup
auto-sdlc logs --user-id alice@company.com --export-dir /shared/reports/

# Send to central collection server
auto-sdlc logs --user-id alice@company.com --export-url http://your-server:8000/reports
```

**Report structure:**

```json
{
  "generated_at": "2026-04-01T10:00:00+00:00",
  "user_id": "alice@company.com",
  "filters": { "project": null, "since": null },
  "summary": {
    "total_sessions": 114,
    "total_tokens": 220000000,
    "avg_prompt_quality_score": 33.5
  },
  "behavioral_metrics": {
    "total_user_messages": 1760,
    "total_skill_invocations": 56,
    "skill_invocation_ratio": 0.031,
    "sessions_per_day": 14.25,
    "avg_messages_per_session": 15.9,
    "unique_tools_used": ["Bash", "Edit", "Read", "Skill", "..."]
  },
  "maturity_scores": {
    "overall_level": 2,
    "overall_label": "Intermediate",
    "dimensions": {
      "prompting_sophistication": { "level": 2, "level_label": "Intermediate" },
      "tooling_adoption":         { "level": 1, "level_label": "Basic" },
      "usage_frequency":          { "level": 4, "level_label": "Expert" },
      "session_depth":            { "level": 3, "level_label": "Advanced" },
      "context_efficiency":       { "level": 2, "level_label": "Intermediate" }
    }
  },
  "project_breakdown": [
    { "project": "semios/backend", "sessions": 40, "total_tokens": 80000000, "avg_prompt_quality": 38.0 }
  ],
  "qualitative_analysis": {
    "narrative": "Developer shows strong usage frequency...",
    "workflow_patterns": { "workflows": [{ "pattern": "Debugging", "evidence": "..." }] },
    "anti_patterns":     { "anti_patterns": [{ "name": "Vague prompts", "recommendation": "..." }] }
  }
}
```

---

### `auto-sdlc team`

Aggregate individual user JSON reports into a team-level maturity report.

```bash
auto-sdlc team --reports-dir PATH [OPTIONS]
```

| Option | Description |
|---|---|
| `--reports-dir PATH` | **(Required)** Directory containing individual user JSON report files |
| `--output PATH` | Save team report to this path. Defaults to `<reports-dir>/team_report.json` |
| `--html` | Also render a team HTML dashboard |

**Typical team workflow:**

```bash
# Each developer runs on their own machine:
auto-sdlc logs --user-id alice@company.com --export-dir /shared/reports/
auto-sdlc logs --user-id bob@company.com   --export-dir /shared/reports/

# Team lead aggregates:
auto-sdlc team --reports-dir /shared/reports/ --html
```

**Team report includes:**
- Overall team maturity level and label
- Maturity by dimension (averaged across all members)
- Per-member table (sessions, prompt quality, skill adoption, maturity)
- Total sessions and tokens across the team

---

### `auto-sdlc serve`

Start a central collection server. Developers POST their reports to it; the server computes the live team report on demand.

```bash
auto-sdlc serve [OPTIONS]
```

| Option | Description |
|---|---|
| `--reports-dir PATH` | Directory to store received reports. Defaults to `~/.auto-sdlc/server/reports/` |
| `--host TEXT` | Host to bind to. Default: `0.0.0.0` |
| `--port INT` | Port to listen on. Default: `8000` |

**API endpoints:**

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/reports` | POST | Receive a developer JSON report |
| `/reports` | GET | List all stored reports |
| `/team` | GET | Live team report as JSON |
| `/team/html` | GET | Live team HTML dashboard |

**Example workflow with server:**

```bash
# On a shared machine or server:
auto-sdlc serve --port 8000

# Each developer sends their report:
auto-sdlc logs --user-id alice@company.com --export-url http://your-server:8000/reports

# Team dashboard always live at:
# http://your-server:8000/team/html
```

---

### `auto-sdlc init` *(coming soon)*

Interactive wizard to generate baseline SDLC config files:
- `CLAUDE.md` — project-level Claude Code instructions
- `AGENTS.md` — agent behavior rules
- `.rules` — coding constraints
- `settings.json` — Claude Code settings (hooks, permissions, model preferences)

### `auto-sdlc audit` *(coming soon)*

Scan installed Claude Code capabilities (skills, MCP servers, agents) against the Auto-SDLC baseline and report gaps.

---

## Maturity Model

Each developer report is scored across **5 dimensions**, each rated 0–4:

| Dimension | What It Measures |
|---|---|
| **Prompting Sophistication** | Average prompt quality score (0–100 rule-based) |
| **Tooling Adoption** | Ratio of skill/command invocations to raw prompts |
| **Usage Frequency** | Sessions per day (how consistently Claude is being used) |
| **Session Depth** | Average messages per session (shallow Q&A vs deep collaboration) |
| **Context Efficiency** | Cache read ratio (how well context is being reused) |

**Maturity levels:**

| Level | Label |
|---|---|
| 0 | Beginner |
| 1 | Basic |
| 2 | Intermediate |
| 3 | Advanced |
| 4 | Expert |

---

## Prompt Quality Scoring

Every user prompt is scored **0–100** using rule-based heuristics:

| Criterion | Points | Signal |
|---|---|---|
| Word count ≥ 20 | +30 | Detailed, not vague |
| File path reference (`src/`, `.py`, `.ts`, etc.) | +25 | Grounded in codebase |
| Line number reference (`line 42`, `L42`) | +15 | Precise location |
| Error/exception text (`TypeError`, `Traceback`, etc.) | +15 | Debugging context |
| Action verb in first 5 words (`fix`, `add`, `refactor`, etc.) | +15 | Clear intent |

**0–30**: Vague. **70+**: High-quality, well-scoped prompts.

---

## How It Works

Claude Code writes a JSONL log file for every conversation at:
```
~/.claude/projects/<project-slug>/<session-id>.jsonl
```

`auto-sdlc logs` reads all `.jsonl` files recursively, extracts typed events (user turns, assistant turns, session metadata), and runs the full analysis pipeline:

```
JSONL files → parser → analyzer → scorer → metrics → maturity → report
                                                              ↓
                                                    render_html / export / serve
```

---

## Project Structure

```
src/auto_sdlc/
├── cli.py                  # All CLI commands
├── server.py               # FastAPI central collection server
├── logs/
│   ├── parser.py           # JSONL reader
│   ├── analyzer.py         # Token + session metadata extraction
│   ├── scorer.py           # Rule-based prompt quality scoring (0-100)
│   ├── metrics.py          # Behavioral metrics (skill ratio, sessions/day, etc.)
│   ├── maturity.py         # 5-dimension maturity scoring (0-4 per dim)
│   ├── qualitative.py      # LLM qualitative analysis via claude -p
│   ├── report.py           # Report assembly + default file output
│   ├── render_html.py      # Individual HTML report renderer
│   ├── team.py             # Team rollup + team HTML renderer
│   └── export.py           # Export to dir or HTTP POST
├── init_wizard/
│   └── wizard.py           # Config wizard (stub)
└── audit/
    └── scanner.py          # Capabilities auditor (stub)
```

---

## Running Tests

```bash
pip3 install pytest httpx
python3 -m pytest tests/ -v
```

76 tests across all modules.

---

## Coming Soon

- **`auto-sdlc init`** — Interactive wizard to generate `CLAUDE.md`, `AGENTS.md`, `.rules`, and `settings.json` tailored to the team's maturity level
- **`auto-sdlc audit`** — Scan installed skills, MCPs, and agents against the Auto-SDLC baseline; report coverage gaps
- **Claude Code Hook integration** — Zero-action data collection: a post-session hook auto-fires `auto-sdlc logs --export-url` after every Claude session, no developer action required
- **Persistent database backend** — Replace flat JSON file storage with SQLite/Postgres for historical trending and multi-run comparisons
- **Trending and delta reports** — Show maturity score changes over time per developer and per team
- **Gemini CLI support** — Swap `claude -p` for `gemini` CLI in qualitative analysis with a single config flag
- **Discovery coverage mapping** — Map every Auto-SDLC discovery question and Maturity Model criterion to specific metrics and qualitative checks, with a coverage report showing gaps
