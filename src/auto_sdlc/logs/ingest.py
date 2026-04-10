"""Bulk ingestion: discover users from directory or CSV, process all, aggregate team report."""

import json
import click
from pathlib import Path
from datetime import datetime, timezone
from typing import Union, List, Tuple

from auto_sdlc.logs.report import build_report
from auto_sdlc.logs.export import export_report_to_dir
from auto_sdlc.logs.team import build_team_report, build_team_report_from_dir, render_team_html


def discover_users_from_dir(logs_root: Union[Path, str]) -> List[Tuple[str, Path]]:
    """
    Walk logs_root. Each immediate subdirectory = one user.
    Returns list of (user_id, logs_path) tuples.

    Detects two directory layouts:
      Layout A (standard): <user_dir>/projects/.../*.jsonl
        → returns (user_id, <user_dir>/projects/)
      Layout B (flat): <user_dir>/*.jsonl
        → returns (user_id, <user_dir>/)

    user_id is derived from directory name.
    """
    logs_root = Path(logs_root)
    users = []

    for user_dir in sorted(logs_root.iterdir()):
        if not user_dir.is_dir():
            continue

        user_id = user_dir.name

        # Check for Layout A: projects/ subdir exists
        projects_subdir = user_dir / "projects"
        if projects_subdir.exists() and projects_subdir.is_dir():
            users.append((user_id, projects_subdir))
            continue

        # Check for Layout B: JSONL files directly in user dir
        jsonl_files = list(user_dir.glob("*.jsonl"))
        if jsonl_files:
            users.append((user_id, user_dir))
            continue

        # Neither layout detected, skip
        click.echo(f"Warning: no sessions found in {user_dir}", err=True)

    return users


def load_users_from_csv(users_file: Union[Path, str]) -> List[Tuple[str, Path]]:
    """
    Read CSV: user_id,logs_path (one per line, # comments allowed).
    Returns list of (user_id, Path) tuples.
    Raises FileNotFoundError if file not found.
    """
    users_file = Path(users_file)
    if not users_file.exists():
        raise FileNotFoundError(f"Users file not found: {users_file}")

    users = []
    for line in users_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(",")
        if len(parts) != 2:
            click.echo(f"Warning: skipping malformed CSV line: {line}", err=True)
            continue
        user_id, logs_path = parts[0].strip(), parts[1].strip()
        users.append((user_id, Path(logs_path)))

    return users


def run_bulk_ingest(logs_root, output_dir, since=None, html=False,
                   qualitative=False, users_file=None):
    """
    Main orchestration for bulk ingestion:
    1. Discover users (from directory structure or CSV file)
    2. For each user:
       a. Call build_report() to parse logs
       b. Optionally run qualitative analysis (not implemented yet)
       c. Save report JSON via export_report_to_dir()
       d. Optionally render individual HTML
    3. Build team report via build_team_report_from_dir()
    4. Optionally render team HTML
    5. Print summary table to stdout
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Discover users
    if users_file:
        users = load_users_from_csv(users_file)
        click.echo(f"Loaded {len(users)} users from {users_file}")
    else:
        users = discover_users_from_dir(logs_root)
        click.echo(f"Discovered {len(users)} users from {logs_root}")

    if not users:
        click.echo("No users found. Exiting.", err=True)
        return

    # Step 2: Process each user
    click.echo()
    click.echo(f"{'User':<30} {'Sessions':<12} {'Maturity':<20}")
    click.echo("─" * 62)

    for user_id, logs_path in users:
        try:
            # Build report
            report = build_report(
                projects_dir=logs_path,
                user_id=user_id,
                project_filter=None,
                since=since,
            )

            # Export JSON
            export_report_to_dir(report, str(output_dir))

            # Optionally render HTML
            if html:
                from auto_sdlc.logs.render_html import render_individual_html
                html_content = render_individual_html(report)
                user_safe = user_id.replace("@", "_at_").replace("/", "_")
                ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H%M%S")
                html_path = output_dir / f"{user_safe}_{ts}.html"
                html_path.write_text(html_content, encoding="utf-8")

            # Print summary
            sessions = report["summary"]["total_sessions"]
            maturity_label = report["maturity_scores"]["overall_label"]
            click.echo(f"{user_id:<30} {sessions:<12} {maturity_label:<20}")

        except Exception as e:
            click.echo(f"{user_id:<30} ERROR: {str(e)}", err=True)

    # Step 3: Build and render team report
    click.echo()
    click.echo("Generating team report...")

    # Load individual reports for both team aggregation and HTML rendering
    user_reports = []
    for f in sorted(output_dir.glob("*.json")):
        if f.name == "team_report.json":
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            user_id = data.get("user_id", f.stem)
            user_reports.append((user_id, data))
        except (json.JSONDecodeError, OSError):
            continue

    team_report = build_team_report(user_reports)
    team_report["generated_at"] = datetime.now(tz=timezone.utc).isoformat()

    team_report_path = output_dir / "team_report.json"
    team_report_path.write_text(
        json.dumps(team_report, indent=2, default=str),
        encoding="utf-8"
    )
    click.echo(f"Team report saved to {team_report_path}")

    if html:
        # Reuse already-loaded user reports for HTML rendering
        user_reports_for_metrics = [r for _, r in user_reports]
        team_html_content = render_team_html(team_report, user_reports_for_metrics)
        team_html_path = output_dir / "team_report.html"
        team_html_path.write_text(team_html_content, encoding="utf-8")
        click.echo(f"Team HTML saved to {team_html_path}")

    click.echo()
    click.echo(f"✓ Completed. Reports in: {output_dir}")
