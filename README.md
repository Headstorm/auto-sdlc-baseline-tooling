# Auto-SDLC Baseline Tooling

Analyze your team's Claude Code usage to understand AI maturity. Upload logs through a web interface or CLI, get instant team dashboards showing prompt quality, behavioral patterns, and maturity scores across 5 dimensions.

Built to automate the discovery process used in Auto-SDLC engagements: instead of interviewing developers, we read the actual session logs.

---

## Quick Start: The Web Application

### Option A: Docker (Recommended)

```bash
# Clone and build
git clone https://github.com/Headstorm/auto-sdlc-baseline-tooling.git
cd auto-sdlc-baseline-tooling
docker build -t auto-sdlc:latest .

# Run the server
docker run -p 8000:8080 \
  -v reports:/data/reports \
  -e REPORTS_DIR=/data/reports \
  auto-sdlc:latest

# Open http://localhost:8000
```

Then push the image to your org's registry (Artifactory, Harbor, ECR, etc.) for deployment to internal servers or Kubernetes.

### Option B: Local Server

```bash
# Clone and install
git clone https://github.com/Headstorm/auto-sdlc-baseline-tooling.git
cd auto-sdlc-baseline-tooling
pip install -e ".[server]"

# Run the server
auto-sdlc serve --port 8000

# Open http://localhost:8000
```

Share the URL with your team if on the same network (e.g., `http://YOUR_IP:8000`).

### Step 2: Developers Submit Logs (One Command)

Each developer runs **once**:

```bash
auto-sdlc logs --user-id you@company.com \
               --export-url http://YOUR_SERVER_URL:8000/reports
```

Replace `YOUR_SERVER_URL` with:
- `localhost` if running locally
- Your machine's IP if sharing on the network
- Your internal server hostname if deployed internally

This reads their local `~/.claude/projects/` and sends the analysis to the server.

### Step 3: View Team Dashboard

Open the live team dashboard anytime:
```
http://YOUR_SERVER_URL:8000/team/html
```

Shows:
- Team maturity level (0-4)
- Per-developer breakdown (sessions, prompt quality, maturity score)
- Maturity by dimension (prompting, tooling, frequency, depth, efficiency)
- **Expandable dimension dropdowns** — Click any dimension to see underlying metrics:
  - **Prompting Sophistication**: Average quality score, % of high-quality prompts, ranges
  - **Tooling Adoption**: Skill invocation ratio, tools used, adoption rates
  - **Usage Frequency**: Sessions per day, activity distribution
  - **Session Depth**: Average messages per session, conversation patterns
  - **Context Efficiency**: Cache hit ratio, token usage patterns

---

## Workflows

### Scenario A: Quarterly Team Review (Recommended)

**Goal**: Understand team AI maturity at the end of a quarter with a live dashboard.

1. **Admin**: Deploy server via Docker or locally (one-time, 5 minutes)
2. **Each developer**: Run the one-command submit (one-time, takes 30 seconds)
3. **Team lead**: Open dashboard at `http://YOUR_SERVER:8000/team/html`, present results

**Timeline**: One hour total. No ongoing overhead. Reports persist on the server.

---

### Scenario B: One-Time Bulk Analysis (No Server)

**Goal**: Analyze the team without deploying a server.

```bash
# Collect all developers' logs into one folder
# Then run:
auto-sdlc ingest --logs-root /path/to/collected/logs \
                 --output-dir ./team-report \
                 --html

# Output: HTML dashboard at ./team-report/team_report.html
```

Good for: one-time snapshots, testing, organizations without cloud infrastructure.

---

### Scenario C: Personal Insights

**Goal**: Developer wants to see their own maturity score.

```bash
auto-sdlc logs --user-id you@company.com --html
```

Generates a personal HTML report at `~/.auto-sdlc/reports/`.

---

## Feature Comparison

| Use Case | Method | Setup | Per-Run Effort | Best For |
|----------|--------|-------|---|---|
| **Live team dashboard** | Docker/Local server → developers submit | 5 min | 30 sec/person | Team reviews, quarterly snapshots |
| **One-time analysis** | Bulk ingest | 0 min | 5 min (total) | No server needed, offline analysis |
| **Personal report** | Local CLI only | 0 min | 30 sec | Individual developer insight |

---

## Maturity Model

Each developer report scores 5 dimensions (0–4 each):

| Dimension | What It Measures |
|---|---|
| **Prompting Sophistication** | Average prompt quality (0–100 rule-based) |
| **Tooling Adoption** | Ratio of skill invocations to raw prompts |
| **Usage Frequency** | Sessions per day |
| **Session Depth** | Average messages per session |
| **Context Efficiency** | Cache read ratio |

**Levels**: 0=Beginner, 1=Basic, 2=Intermediate, 3=Advanced, 4=Expert

---

## Prompt Quality Scoring

Every user prompt is scored 0–100 using rule-based heuristics:

| Criterion | Points | Signal |
|---|---|---|
| Word count ≥ 20 | +30 | Detailed, not vague |
| File path reference (`src/`, `.py`) | +25 | Grounded in codebase |
| Line number reference (`line 42`, `L42`) | +15 | Precise location |
| Error/exception text | +15 | Debugging context |
| Action verb in first 5 words | +15 | Clear intent |

**Score**: 0–30 = vague, 70+ = high-quality.

---

## Installation

**Requirements**: Python 3.9+

### For the Server

```bash
git clone https://github.com/Headstorm/auto-sdlc-baseline-tooling.git
cd auto-sdlc-baseline-tooling
pip install -e ".[server]"
```

Then run `auto-sdlc serve` (see Quick Start above) or use Docker.

### For CLI Only (No Server)

```bash
pip install -e .
```

### For Development

```bash
pip install -e ".[server]"
pip install pytest
python -m pytest tests/ -v  # 109 tests
```

---

## CLI Reference

If you prefer command-line workflows (or aren't running a server), these commands are available:

### `auto-sdlc serve`

Start a local development server:

```bash
auto-sdlc serve --port 8000
# Open http://localhost:8000
```

### `auto-sdlc logs`

Analyze local Claude Code logs:

```bash
auto-sdlc logs --user-id you@company.com --html --export-url http://server:8000/reports
```

**Options:**
- `--projects-dir PATH` — Override default `~/.claude/projects/`
- `--output PATH` — Save JSON report to custom path
- `--html` — Also render HTML report
- `--export-url URL` — POST to server (for Scenario A)
- `--export-dir PATH` — Save to local directory (for Scenario B)
- `--since YYYY-MM-DD` — Filter to date range
- `--qualitative` — Run LLM analysis (requires claude CLI)

### `auto-sdlc ingest`

Batch-process all users at once:

```bash
auto-sdlc ingest --logs-root /shared/logs \
                 --output-dir ./reports \
                 --html
```

**Options:**
- `--users-file PATH` — CSV with `user_id,logs_path` mapping
- `--since YYYY-MM-DD` — Filter to date range
- `--qualitative` — Run LLM analysis on all users

### `auto-sdlc team`

Aggregate pre-existing JSON reports:

```bash
auto-sdlc team --reports-dir /path/to/reports --html
```

---

## How It Works

Claude Code writes JSONL files to `~/.claude/projects/`:

```
~/.claude/projects/
├── project-a/
│   └── <session-id>.jsonl
└── project-b/
    └── <session-id>.jsonl
```

Auto-SDLC parses these files through an analysis pipeline:

```
JSONL → Parser → Analyzer → Scorer → Metrics → Maturity → Report → HTML/JSON
```

Results can be saved locally, posted to a server, or aggregated from multiple users.

---

## Project Structure

```
src/auto_sdlc/
├── cli.py                  # CLI entry points
├── server.py               # FastAPI application (web UI + API)
├── logs/
│   ├── parser.py           # JSONL reader
│   ├── analyzer.py         # Token + metadata extraction
│   ├── scorer.py           # Prompt quality scoring (0-100)
│   ├── metrics.py          # Behavioral metrics
│   ├── maturity.py         # 5-dimension scoring
│   ├── qualitative.py      # LLM analysis
│   ├── report.py           # Report assembly
│   ├── render_html.py      # HTML rendering
│   ├── export.py           # Export to dir/HTTP
│   ├── team.py             # Team aggregation
│   └── ingest.py           # Bulk ingestion
├── init_wizard/
│   └── wizard.py           # Config wizard (stub)
└── audit/
    └── scanner.py          # Audit tool (stub)
```

---

## Testing

```bash
python -m pytest tests/ -v
```

109 tests covering all modules. Full CI/CD ready.

---

## What's Implemented

✅ **Phase 1**: Core analysis pipeline (parser, scorer, metrics, maturity, report generation, HTML rendering)
✅ **Phase 2**: Web application (server with file upload, individual dashboards, team aggregation)
✅ **Phase 3**: Railway deployment (Procfile, env var support, CLI-first landing page)
✅ **Bulk ingest** (`auto-sdlc ingest` command for one-time team analysis)
✅ **Dashboard dimension dropdowns** — Expandable metrics for each dimension (prompting, tooling, frequency, depth, efficiency) in both individual and team dashboards

---

## Coming Soon

- **`auto-sdlc init`** — Interactive wizard to generate CLAUDE.md, AGENTS.md, .rules config
- **`auto-sdlc audit`** — Scan installed Claude Code capabilities against baseline
- **SQLite persistence** — Store reports in database for history/trending instead of files
- **Workflow extraction** — Detect multi-session patterns, abandoned tasks, rework cycles
- **Discovery mapping** — Map maturity criteria to Auto-SDLC discovery questions
- **Auto-sync hook** — Claude Code Stop hook that auto-POSTs logs after every session (zero ongoing effort after setup)
- **Trending dashboard** — Show maturity changes over time per developer and team
- **Gemini/other LLM support** — Use alternative LLMs for qualitative analysis

---

## License

MIT
