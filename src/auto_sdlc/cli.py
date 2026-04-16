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


def _get_db() -> Database:
    """Get database connection, creating it if needed."""
    db = Database(str(Path.home() / ".auto-sdlc" / "auto_sdlc.db"))
    db.init()
    return db


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

    # Strip whitespace from flag values provided on the command line
    if team_name is not None:
        team_name = team_name.strip()
    if user_name is not None:
        user_name = user_name.strip()

    # Prompt for team_name if not provided or blank
    if not team_name:
        click.echo()
        team_name = click.prompt('Enter team name', type=str).strip()
    if not team_name:
        click.echo("Error: Team name cannot be empty", err=True)
        sys.exit(1)

    # Prompt for user_name if not provided or blank
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

    # Strip whitespace from flag values provided on the command line
    if team_name is not None:
        team_name = team_name.strip()
    if user_name is not None:
        user_name = user_name.strip()

    click.echo()
    if not team_name:
        team_name = click.prompt('Enter team name', type=str).strip()
    if not team_name:
        click.echo("Error: Team name cannot be empty", err=True)
        sys.exit(1)

    if report_type == 'individual' and not user_name:
        user_name = click.prompt('Enter user name', type=str).strip()
    if report_type == 'individual' and not user_name:
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
            zip_bytes = logs_path_obj.read_bytes()
            try:
                temp_path, logs_dir = extract_logs_zip(zip_bytes)
                temp_root = temp_path
                project_path = str(create_project_structure(logs_dir, temp_path))
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


@cli.command(name="list-uploads")
@click.option('--team-name', default=None, help='Filter by team name')
@click.option('--user-name', default=None, help='Filter by user name')
def list_uploads(team_name, user_name):
    """List all uploaded log sets stored in the database."""
    db = _get_db()
    try:
        if team_name:
            uploads = db.get_uploads_by_team(team_name)
        else:
            uploads = db.get_all_uploads()

        if user_name:
            uploads = [u for u in uploads if u["user_name"] == user_name]

        if not uploads:
            click.echo("No uploads found.")
            return

        click.echo(f"\n{'ID':<6} {'Team':<20} {'User':<20} {'Sessions':<10} {'Tokens':<12} {'Status':<10} {'Uploaded'}")
        click.echo("-" * 95)
        for u in uploads:
            click.echo(
                f"{u['id']:<6} {u['team_name']:<20} {u['user_name']:<20} "
                f"{u['session_count']:<10} {u['total_tokens']:<12,} {u['status']:<10} "
                f"{u['uploaded_at'][:19].replace('T', ' ')}"
            )
        click.echo(f"\nTotal: {len(uploads)} upload(s)")
    finally:
        db.close()


@cli.command(name="list-reports")
@click.option('--team-name', default=None, help='Filter by team name')
@click.option('--user-name', default=None, help='Filter by user name')
def list_reports(team_name, user_name):
    """List all generated reports stored in the database."""
    db = _get_db()
    try:
        if team_name:
            reports = db.get_reports_by_team(team_name)
        elif user_name:
            reports = db.get_reports_by_user(user_name)
        else:
            reports = db.get_all_reports()

        if team_name and user_name:
            reports = [r for r in reports if r["user_name"] == user_name]

        if not reports:
            click.echo("No reports found.")
            return

        click.echo(f"\n{'ID':<6} {'Team':<20} {'User':<20} {'Maturity':<10} {'Generated':<22} {'PDF'}")
        click.echo("-" * 110)
        for r in reports:
            maturity = f"{r['overall_maturity_level']:.1f}" if r['overall_maturity_level'] else "N/A"
            click.echo(
                f"{r['id']:<6} {r['team_name']:<20} {r['user_name']:<20} "
                f"{maturity:<10} {r['generated_at'][:19].replace('T', ' '):<22} "
                f"{r['pdf_path']}"
            )
        click.echo(f"\nTotal: {len(reports)} report(s)")
    finally:
        db.close()


if __name__ == '__main__':
    cli()
