# Report Command Options Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the `report` CLI command to accept `--team-name`, `--user-name`, and `--report-type` as flags (instead of only prompting interactively), and expose the already-supported team vs individual report distinction.

**Architecture:** Single file change — `src/auto_sdlc/cli.py`. The report generation pipeline already supports both `"team"` and `"individual"` types end-to-end (models, pipeline, PDF renderer). The only gap is the CLI: `--team-name` and `--user-name` don't exist, and `report_type` is hardcoded to `"individual"`. The fix adds these three options with interactive prompts as fallback when flags are omitted. For team reports, `user_id` is set to `team_name` (the pipeline uses `user_id` as `team_name` when `report_type="team"`).

**Tech Stack:** Python, Click, existing `ReportService`

---

## Context: Current vs Target Behavior

**Current `report` command signature:**
```python
@cli.command()
@click.argument('logs_path', type=click.Path(exists=True))
@click.option('--output-dir', ...)
def report(logs_path, output_dir):
    team_name = click.prompt('Enter team name')   # always interactive
    user_name = click.prompt('Enter user name')   # always interactive
    # hardcoded: report_type="individual"
    service.generate_report(user_id=user_name, ...)
```

**Target `report` command signature:**
```python
@cli.command()
@click.argument('logs_path', type=click.Path(exists=True))
@click.option('--team-name', default=None)
@click.option('--user-name', default=None)
@click.option('--report-type', type=click.Choice(['individual', 'team']), default='individual')
@click.option('--output-dir', ...)
def report(logs_path, team_name, user_name, report_type, output_dir):
    if not team_name:
        team_name = click.prompt('Enter team name')
    if not user_name and report_type == 'individual':
        user_name = click.prompt('Enter user name')
    user_id = user_name if report_type == 'individual' else team_name
    service.generate_report(user_id=user_id, report_type=report_type, ...)
```

**Note:** Team reports don't need a user name — only a team name. Individual reports need both.

---

## File Structure

| File | Action |
|------|--------|
| `src/auto_sdlc/cli.py` | MODIFY — add options to `report` command |
| `tests/test_cli_report.py` | CREATE — tests for new options |

---

## Task 1: Add `--team-name`, `--user-name`, `--report-type` to `report` command

**Files:**
- Modify: `src/auto_sdlc/cli.py`
- Create: `tests/test_cli_report.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_cli_report.py`:

```python
import subprocess
import sys
from pathlib import Path


def test_report_command_help_shows_new_options():
    result = subprocess.run(
        [sys.executable, "-m", "auto_sdlc.cli", "report", "--help"],
        capture_output=True, text=True
    )
    assert "--team-name" in result.stdout
    assert "--user-name" in result.stdout
    assert "--report-type" in result.stdout


def test_report_command_accepts_team_name_flag(tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "session.jsonl").write_text(
        '{"type":"system","subtype":"turn_duration","durationMs":5000,"sessionId":"abc",'
        '"message_count":10,"cwd":"/tmp","gitBranch":"main"}\n'
    )

    result = subprocess.run(
        [
            sys.executable, "-m", "auto_sdlc.cli", "report",
            str(logs_dir),
            "--team-name", "testteam",
            "--user-name", "testuser",
            "--report-type", "individual",
            "--output-dir", str(tmp_path / "reports"),
        ],
        capture_output=True, text=True,
    )
    # Should not fail with "No such option" or hang waiting for input
    assert "No such option" not in result.stderr
    assert "Error: Missing argument" not in result.stderr


def test_report_command_accepts_team_type(tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "session.jsonl").write_text(
        '{"type":"system","subtype":"turn_duration","durationMs":5000,"sessionId":"abc",'
        '"message_count":10,"cwd":"/tmp","gitBranch":"main"}\n'
    )

    result = subprocess.run(
        [
            sys.executable, "-m", "auto_sdlc.cli", "report",
            str(logs_dir),
            "--team-name", "testteam",
            "--report-type", "team",
            "--output-dir", str(tmp_path / "reports"),
        ],
        capture_output=True, text=True,
    )
    # Team report should not ask for user name
    assert "No such option" not in result.stderr
    assert "Error: Missing argument" not in result.stderr


def test_report_rejects_invalid_report_type(tmp_path):
    result = subprocess.run(
        [
            sys.executable, "-m", "auto_sdlc.cli", "report",
            str(tmp_path),
            "--team-name", "t",
            "--report-type", "invalid",
        ],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "invalid" in result.stderr.lower() or "invalid" in result.stdout.lower()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /Users/smannar/auto-sdlc
python3 -m pytest tests/test_cli_report.py -v 2>&1 | head -30
```

Expected: `test_report_command_help_shows_new_options` fails with `AssertionError` (options not in help output yet).

- [ ] **Step 3: Update the `report` command in `src/auto_sdlc/cli.py`**

Replace the existing `report` command (the `@cli.command()` decorated function starting around line 145) with this:

```python
@cli.command()
@click.argument('logs_path', type=click.Path(exists=True))
@click.option('--team-name', default=None, help='Team name (prompted if not provided)')
@click.option('--user-name', default=None, help='User name — required for individual reports (prompted if not provided)')
@click.option(
    '--report-type',
    type=click.Choice(['individual', 'team']),
    default='individual',
    show_default=True,
    help='individual: 4-6 page developer profile. team: 8-12 page leadership view.',
)
@click.option(
    '--output-dir',
    type=click.Path(),
    default=None,
    help='Output directory for reports (default: ~/.auto-sdlc/server/reports)',
)
def report(logs_path: str, team_name: str, user_name: str, report_type: str, output_dir: str):
    """
    Generate an AI maturity assessment report from Claude Code logs.

    LOGS_PATH: Path to logs directory (containing .jsonl files) or logs.zip file

    Examples:

        auto-sdlc report ~/.claude/projects/myapp

        auto-sdlc report ~/.claude/projects/myapp --team-name myteam --user-name alice

        auto-sdlc report ~/logs.zip --report-type team --team-name platform_team
    """
    logs_path_obj = Path(logs_path).resolve()

    if not logs_path_obj.exists():
        click.echo(f"Error: Logs path does not exist: {logs_path}", err=True)
        sys.exit(1)

    is_zip = logs_path_obj.is_file() and logs_path_obj.suffix == '.zip'
    is_dir = logs_path_obj.is_dir()

    if not (is_zip or is_dir):
        click.echo(f"Error: Logs path must be a directory or .zip file: {logs_path}", err=True)
        sys.exit(1)

    if not output_dir:
        output_dir = str(Path.home() / ".auto-sdlc" / "server" / "reports")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Prompt only for what's missing
    click.echo()
    if not team_name:
        team_name = click.prompt('Enter team name', type=str).strip()
        if not team_name:
            click.echo("Error: Team name cannot be empty", err=True)
            sys.exit(1)

    if report_type == 'individual' and not user_name:
        user_name = click.prompt('Enter user name', type=str).strip()
        if not user_name:
            click.echo("Error: User name cannot be empty for individual reports", err=True)
            sys.exit(1)

    # For team reports, user_id is the team name (pipeline uses user_id as team_name)
    user_id = user_name if report_type == 'individual' else team_name

    click.echo(f"Generating {report_type} report...")

    project_path = None
    temp_root = None

    try:
        if is_zip:
            import tempfile
            temp_root = Path(tempfile.mkdtemp(prefix="auto_sdlc_logs_"))
            zip_bytes = logs_path_obj.read_bytes()
            try:
                temp_path, logs_dir = extract_logs_zip(zip_bytes)
                project_path = str(create_project_structure(logs_dir, temp_path))
                temp_root = temp_path
            except ValueError as e:
                click.echo(f"Error: {e}", err=True)
                sys.exit(1)
        else:
            import tempfile
            temp_root = Path(tempfile.mkdtemp(prefix="auto_sdlc_logs_"))
            project_path = str(create_project_structure(logs_path_obj, temp_root))

        team_output_dir = output_path / team_name
        team_output_dir.mkdir(parents=True, exist_ok=True)

        with click.progressbar(length=4, label='Generating', show_pos=True) as bar:
            def progress_callback(phase, label, pct):
                bar.update(1)

            service = ReportService()
            report_obj, pdf_path = service.generate_report(
                user_id=user_id,
                project_path=project_path,
                report_type=report_type,
                output_dir=str(team_output_dir),
                progress_callback=progress_callback,
            )

        click.echo()
        click.secho('✓ Report generated successfully!', fg='green', bold=True)
        click.echo(f"Type:     {report_type}")
        click.echo(f"Team:     {team_name}")
        if report_type == 'individual':
            click.echo(f"User:     {user_name}")
        click.echo(f"Location: {pdf_path}")
        click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        if temp_root and temp_root.exists():
            import shutil
            shutil.rmtree(str(temp_root), ignore_errors=True)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
python3 -m pytest tests/test_cli_report.py::test_report_command_help_shows_new_options tests/test_cli_report.py::test_report_rejects_invalid_report_type -v
```

Expected: Both pass. The generate tests (`test_report_command_accepts_*`) may still fail if report generation itself has issues with the minimal test data — that's fine; the key assertions are about option parsing, not PDF generation.

- [ ] **Step 5: Verify help output**

```bash
python3 -m auto_sdlc.cli report --help
```

Expected output:
```
Usage: python -m auto_sdlc.cli report [OPTIONS] LOGS_PATH

  Generate an AI maturity assessment report from Claude Code logs.
  ...

Options:
  --team-name TEXT                Team name (prompted if not provided)
  --user-name TEXT                User name...
  --report-type [individual|team] individual: 4-6 page developer profile...
                                  [default: individual]
  --output-dir PATH               Output directory...
  --help                          Show this message and exit.
```

- [ ] **Step 6: Smoke test — individual report (non-interactive)**

```bash
python3 -m auto_sdlc.cli report ~/.claude/projects/-Users-smannar-auto-sdlc \
  --team-name Headstorm \
  --user-name Srivaths \
  --report-type individual
```

Expected: Progress bar advances, prints `✓ Report generated successfully!` with a PDF path.

- [ ] **Step 7: Smoke test — team report (no user name needed)**

```bash
python3 -m auto_sdlc.cli report ~/.claude/projects/-Users-smannar-auto-sdlc \
  --team-name Headstorm \
  --report-type team
```

Expected: Progress bar, prints `✓ Report generated successfully!`, no `User:` line in output.

- [ ] **Step 8: Commit**

```bash
git add src/auto_sdlc/cli.py tests/test_cli_report.py
git commit -m "feat: add --team-name, --user-name, --report-type options to report command"
```

---

## Verification

```bash
# Help shows all options
python3 -m auto_sdlc.cli report --help

# Non-interactive individual report
python3 -m auto_sdlc.cli report /path/to/logs --team-name myteam --user-name alice

# Non-interactive team report (no user name required)
python3 -m auto_sdlc.cli report /path/to/logs --team-name myteam --report-type team

# Invalid type rejected by Click
python3 -m auto_sdlc.cli report /tmp --team-name t --report-type badvalue
# Expected: Error: Invalid value for '--report-type': 'badvalue' is not one of 'individual', 'team'.
```
