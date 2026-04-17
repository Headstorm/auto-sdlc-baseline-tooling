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
| `auto-sdlc report` | Generate a PDF report from the latest upload for a team/user |
| `auto-sdlc list-uploads` | List all stored uploads |
| `auto-sdlc list-reports` | List all generated reports |
| `auto-sdlc open-report` | Open a PDF report in your system viewer |

### Workflow 1: Upload and Generate Individual Report

```bash
# Step 1: Upload logs
auto-sdlc upload ~/.claude/projects/myapp --team-name Headstorm --user-name Alice

# Output:
# ✓ Upload recorded successfully!
# Upload ID: 1
# Sessions found: 5
# Total tokens: 12,500
# Location: ~/.auto-sdlc/logs/Headstorm/Alice_20260417_143022

# Step 2: Generate individual report (uses the latest upload)
auto-sdlc report --team-name Headstorm --user-name Alice

# Output:
# Using upload from: ~/.auto-sdlc/logs/Headstorm/Alice_20260417_143022
# Generating individual report...
# ✓ Report generated successfully!
# Type:     individual
# Team:     Headstorm
# User:     Alice
# Location: ~/.auto-sdlc/server/reports/Headstorm/Alice_report_20260417_143022.pdf
# To open:  open "~/.auto-sdlc/server/reports/Headstorm/Alice_report_20260417_143022.pdf"

# Step 3: Open the report
auto-sdlc open-report --team-name Headstorm --user-name Alice
```

### Workflow 2: Generate Team-Level Report

```bash
# Upload logs (will use latest for entire team)
auto-sdlc upload ~/.claude/projects/myapp --team-name Headstorm --user-name Alice

# Generate team-wide report (no user name needed)
auto-sdlc report --team-name Headstorm --report-type team

# Output:
# Using upload from: ~/.auto-sdlc/logs/Headstorm/Alice_20260417_143022
# Generating team report...
# ✓ Report generated successfully!
# Type:     team
# Team:     Headstorm
# Location: ~/.auto-sdlc/server/reports/Headstorm/team_report_20260417_143022.pdf

# Open the team report
auto-sdlc open-report --team-name Headstorm --report-type team
```

### Workflow 3: Inspect Uploads and Reports

```bash
# List all uploads
auto-sdlc list-uploads

# Filter by team
auto-sdlc list-uploads --team-name Headstorm

# Filter by user
auto-sdlc list-uploads --user-name Alice

# List all reports
auto-sdlc list-reports

# Filter by team
auto-sdlc list-reports --team-name Headstorm

# Filter by user
auto-sdlc list-reports --user-name Alice
```

### Workflow 4: Access Reports

```bash
# Open most recent report for a user
auto-sdlc open-report --team-name Headstorm --user-name Alice

# Open most recent report for a team
auto-sdlc open-report --team-name Headstorm

# Open a specific report by ID (from list-reports)
auto-sdlc open-report --id 1

# Open report by user name only
auto-sdlc open-report --user-name Alice

# Or open manually from the terminal
open "~/.auto-sdlc/server/reports/Headstorm/Alice_report_20260417_143510.pdf"
```

### Interactive Mode

All optional flags can be omitted—you'll be prompted interactively:

```bash
# Report without flags — prompts for team and user
auto-sdlc report

# Upload without flags — prompts for team and user
auto-sdlc upload ~/logs.zip

# List commands can also be run without filters
auto-sdlc list-uploads
auto-sdlc list-reports
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
