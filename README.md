# Auto-SDLC: AI Maturity Assessment Tool

Generate professional PDF reports measuring your team's AI maturity across 12 dimensions using Claude Code session logs.

## Overview

Auto-SDLC analyzes your Claude Code usage patterns, prompting strategies, and tool adoption to assess team AI maturity on four dimensions:

1. **Capability** — Tool adoption, prompt engineering, agent configuration
2. **Integration** — CI/CD, ticketing, cross-system connectivity  
3. **Governance** — Quality controls, security, measurement
4. **Execution Ownership** — Practices documentation, accountability, scalability

Each dimension has sub-dimensions scored at levels L1–L4, with reports providing evidence, insights, and a roadmap to the next maturity level.

## Installation

Install from source:
```bash
cd /path/to/auto-sdlc
pip install -e .
```

Or install as a package:
```bash
pip install auto-sdlc
```

## Usage

All commands use the CLI. There is no web dashboard; use `list-*` commands to inspect your data.

### Commands Reference

| Command | Purpose |
|---------|---------|
| `auto-sdlc upload <logs>` | Copy logs to persistent storage and record metadata in SQLite |
| `auto-sdlc report <logs>` | Generate a PDF report from logs (direct mode) |
| `auto-sdlc list-uploads` | List all stored uploads |
| `auto-sdlc list-reports` | List all generated reports |

### Workflow 1: Upload and Generate Immediately

```bash
# Upload logs and generate a report in one step
auto-sdlc report ~/.claude/projects/myapp

# Prompted for: team name, user name
# Output: PDF report saved to ~/.auto-sdlc/server/reports/{team}/{user}_report_*.pdf
```

### Workflow 2: Upload Now, Generate Later

Store logs first, then inspect and generate reports on your schedule:

```bash
# Step 1: Upload logs to persistent storage
auto-sdlc upload ~/.claude/projects/myapp --team-name Headstorm --user-name alice

# Output:
# ✓ Upload recorded successfully!
# Upload ID: 1
# Sessions found: 5
# Total tokens: 12,500
# Location: ~/.auto-sdlc/logs/Headstorm/alice_20260415_182225

# Step 2: List all uploads
auto-sdlc list-uploads

# Output:
# ID  Team      User   Sessions  Tokens    Status   Uploaded
# 1   Headstorm alice  5         12500     pending  2026-04-15 18:22:25

# Step 3: Generate report from upload
auto-sdlc report ~/.auto-sdlc/logs/Headstorm/alice_20260415_182225

# Or filter uploads to find what you need
auto-sdlc list-uploads --team-name Headstorm
auto-sdlc list-uploads --user-name alice
```

### List Uploaded Logs

```bash
# All uploads
auto-sdlc list-uploads

# Filter by team
auto-sdlc list-uploads --team-name Headstorm

# Filter by user
auto-sdlc list-uploads --user-name alice
```

### List Generated Reports

```bash
# All reports
auto-sdlc list-reports

# Filter by team
auto-sdlc list-reports --team-name Headstorm

# Filter by user
auto-sdlc list-reports --user-name alice
```

## Storage

All data is stored locally:

- **Logs:** `~/.auto-sdlc/logs/{team}/{user}_{timestamp}/` — Raw session files
- **Database:** `~/.auto-sdlc/auto_sdlc.db` — SQLite database tracking uploads and reports
- **Reports:** `~/.auto-sdlc/server/reports/{team}/` — Generated PDF files

Inspect the database:
```bash
sqlite3 ~/.auto-sdlc/auto_sdlc.db

# List all uploads
sqlite> SELECT id, team_name, user_name, status, session_count FROM log_uploads;

# List all reports
sqlite> SELECT id, upload_id, team_name, user_name, pdf_path FROM reports;
```

## What to Provide

### Logs Input

A directory containing `.jsonl` session files (one JSON object per line, each representing an event from a Claude Code session):

```bash
~/.claude/projects/myapp/
├── session_abc.jsonl
├── session_def.jsonl
└── ...
```

Or a `.zip` archive containing the above structure.

### Metadata

When uploading or generating:
- **Team name** — E.g., `platform_team`, `Headstorm`
- **User name** — E.g., `john.smith`, `alice`

## Output

Reports are saved as PDF files:
```
~/.auto-sdlc/server/reports/
└── {team_name}/
    ├── {user_name}_report_20260415_182225.pdf
    └── ...
```

Each report contains:
- **Evidence summary** — What the logs show (adoption, prompting, usage patterns)
- **Dimension scores** — L1–L4 level for each of 12 sub-dimensions
- **Strengths** — What's working well
- **Growth areas** — Where improvement is needed
- **Roadmap** — Specific steps to next maturity level with effort estimates

## Troubleshooting

### "No such option: --team"
Use `--team-name` instead (full flag name required).

### "Path does not exist"
Verify the logs directory exists and contains `.jsonl` files.

### "No uploads found"
Run `auto-sdlc upload` first to store logs, then `auto-sdlc list-uploads` to verify they were stored.

## Development

Run tests:
```bash
python3 -m pytest tests/
```

Check code style:
```bash
python3 -m py_compile src/auto_sdlc/*.py
```
