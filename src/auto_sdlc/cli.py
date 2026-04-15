"""Minimal CLI for auto-sdlc report generation."""
import click
import sys
import shutil
from pathlib import Path
from datetime import datetime, timezone

from auto_sdlc.server.extractors import extract_logs_zip, create_project_structure
from auto_sdlc.reports.service import ReportService
from auto_sdlc.db import Database
from auto_sdlc.logs.parser import find_session_files, parse_session_file
from auto_sdlc.logs.analyzer import extract_token_usage, extract_session_metadata, aggregate_sessions


@click.group()
def cli():
    """Auto-SDLC: AI Maturity Assessment Reports."""
    pass


@cli.command()
@click.argument('logs_path', type=click.Path(exists=True))
@click.option('--team-name', type=str, default=None, help='Team name (prompted if not provided)')
@click.option('--user-name', type=str, default=None, help='User name (prompted if not provided)')
def upload(logs_path: str, team_name: str, user_name: str):
    """
    Upload Claude Code session logs for analysis.

    Copies logs to ~/.auto-sdlc/logs/{team_name}/{user_name}_{timestamp}/ and records metadata in SQLite.

    LOGS_PATH: Path to logs directory or .zip file

    Example:
        auto-sdlc upload ~/.claude/projects/myapp
        auto-sdlc upload ~/logs.zip --team-name myteam --user-name alice
    """
    logs_path_obj = Path(logs_path).resolve()

    # Validate logs path
    if not logs_path_obj.exists():
        click.echo(f"Error: Logs path does not exist: {logs_path}", err=True)
        sys.exit(1)

    # Prompt for team_name if not provided
    if not team_name:
        click.echo()
        team_name = click.prompt('Enter team name', type=str).strip()
        if not team_name:
            click.echo("Error: Team name cannot be empty", err=True)
            sys.exit(1)

    # Prompt for user_name if not provided
    if not user_name:
        user_name = click.prompt('Enter user name', type=str).strip()
        if not user_name:
            click.echo("Error: User name cannot be empty", err=True)
            sys.exit(1)

    try:
        # Create destination directory with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest_dir = Path.home() / ".auto-sdlc" / "logs" / team_name / f"{user_name}_{timestamp}"
        dest_dir.mkdir(parents=True, exist_ok=True)

        click.echo(f"\nUploading logs to {dest_dir}...")

        # Copy logs directory
        if logs_path_obj.is_dir():
            # Copy directory contents
            for item in logs_path_obj.iterdir():
                dest_item = dest_dir / item.name
                if item.is_dir():
                    shutil.copytree(str(item), str(dest_item), dirs_exist_ok=True)
                else:
                    shutil.copy2(str(item), str(dest_item))
        else:
            # Copy single file (zip or other)
            shutil.copy2(str(logs_path_obj), str(dest_dir / logs_path_obj.name))

        # Extract session metadata and token usage
        session_count = 0
        total_tokens = 0

        # Find all session files
        session_files = list(find_session_files(dest_dir))

        for session_file in session_files:
            try:
                events = parse_session_file(str(session_file))
                if events:
                    session_count += 1
                    usage = extract_token_usage(events)
                    total_tokens += usage.get("total_tokens", 0)
            except Exception as e:
                click.echo(f"Warning: Failed to parse {session_file}: {e}", err=True)

        # Record in SQLite database
        db_path = str(Path.home() / ".auto-sdlc" / "auto_sdlc.db")
        db = Database(db_path)
        db.init()

        upload_id = db.insert_upload(
            team_name=team_name,
            user_name=user_name,
            logs_path=str(dest_dir),
            session_count=session_count,
            total_tokens=total_tokens,
        )

        db.close()

        # Print results
        click.echo()
        click.secho('✓ Upload recorded successfully!', fg='green', bold=True)
        click.echo(f"Upload ID: {upload_id}")
        click.echo(f"Sessions found: {session_count}")
        click.echo(f"Total tokens: {total_tokens}")
        click.echo(f"Location: {dest_dir}")
        click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('logs_path', type=click.Path(exists=True))
@click.option(
    '--output-dir',
    type=click.Path(),
    default=None,
    help='Output directory for reports (default: ~/.auto-sdlc/server/reports)'
)
def report(logs_path: str, output_dir: str):
    """
    Generate an AI maturity assessment report from Claude Code logs.

    LOGS_PATH: Path to logs directory (containing .jsonl files) or logs.zip file

    Example:
        auto-sdlc report ~/.claude/projects/myapp
        auto-sdlc report ~/logs.zip
    """
    logs_path_obj = Path(logs_path).resolve()

    # Validate logs path
    if not logs_path_obj.exists():
        click.echo(f"Error: Logs path does not exist: {logs_path}", err=True)
        sys.exit(1)

    # Determine if it's a directory or ZIP file
    is_zip = logs_path_obj.is_file() and logs_path_obj.suffix == '.zip'
    is_dir = logs_path_obj.is_dir()

    if not (is_zip or is_dir):
        click.echo(
            f"Error: Logs path must be a directory or .zip file: {logs_path}",
            err=True
        )
        sys.exit(1)

    # Set default output directory
    if not output_dir:
        output_dir = str(Path.home() / ".auto-sdlc" / "server" / "reports")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get team and user names interactively
    click.echo()
    team_name = click.prompt('Enter team name', type=str).strip()
    if not team_name:
        click.echo("Error: Team name cannot be empty", err=True)
        sys.exit(1)

    user_name = click.prompt('Enter user name', type=str).strip()
    if not user_name:
        click.echo("Error: User name cannot be empty", err=True)
        sys.exit(1)

    click.echo()
    click.echo("Generating report...")

    # Prepare project path based on input type
    project_path = None
    temp_root = None

    try:
        if is_zip:
            # Extract ZIP and create project structure
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
            # Directory: create project structure
            import tempfile
            temp_root = Path(tempfile.mkdtemp(prefix="auto_sdlc_logs_"))
            project_path = str(create_project_structure(logs_path_obj, temp_root))

        # Create team-scoped output directory
        team_output_dir = output_path / team_name
        team_output_dir.mkdir(parents=True, exist_ok=True)

        # Generate report with progress
        with click.progressbar(
            length=4,
            label='Generating',
            show_pos=True,
        ) as bar:
            def progress_callback(phase, label, pct):
                bar.update(1)

            service = ReportService()
            report_obj, pdf_path = service.generate_report(
                user_id=user_name,
                project_path=project_path,
                report_type="individual",
                output_dir=str(team_output_dir),
                progress_callback=progress_callback,
            )

        # Success message
        click.echo()
        click.secho('✓ Report generated successfully!', fg='green', bold=True)
        click.echo(f"Location: {pdf_path}")
        click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        # Clean up temp directory
        if temp_root and temp_root.exists():
            import shutil
            shutil.rmtree(str(temp_root), ignore_errors=True)


if __name__ == '__main__':
    cli()
