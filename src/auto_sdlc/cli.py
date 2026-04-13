import click
from auto_sdlc.logs.report import run_logs_report
from auto_sdlc.init_wizard.wizard import run_wizard
from auto_sdlc.audit.scanner import run_audit


@click.group()
def cli():
    """Auto-SDLC Baseline Tooling."""


@cli.command()
@click.option("--projects-dir", default=None,
              help="Path to Claude Code projects dir. Defaults to ~/.claude/projects/")
@click.option("--output", default=None,
              help="Write JSON report to this file. Defaults to ~/.auto-sdlc/reports/<user>/<timestamp>.json")
@click.option("--project", default=None,
              help="Filter sessions by project name (matches against working directory).")
@click.option("--since", default=None, metavar="YYYY-MM-DD",
              help="Only include sessions on or after this date.")
@click.option("--summary-only", is_flag=True, default=False,
              help="Print summary + maturity scores to stdout instead of saving full report.")
@click.option("--user-id", default=None,
              help="Developer identifier (email or name) for report attribution.")
@click.option("--qualitative", is_flag=True, default=False,
              help="Run LLM qualitative analysis via 'claude -p' (slow, requires claude CLI).")
@click.option("--html", is_flag=True, default=False,
              help="Also render an HTML report alongside the JSON.")
@click.option("--export-dir", default=None,
              help="Copy the JSON report to this directory (for team aggregation).")
@click.option("--export-url", default=None,
              help="POST the JSON report to this URL (for central collection).")
def logs(projects_dir, output, project, since, summary_only, user_id, qualitative, html, export_dir, export_url):
    """Analyze Claude Code session logs."""
    report = run_logs_report(
        projects_dir=projects_dir,
        output_path=output,
        user_id=user_id,
        project_filter=project,
        since=since,
        summary_only=summary_only,
        run_qualitative=qualitative,
    )
    if html and not summary_only:
        from auto_sdlc.logs.render_html import render_individual_html
        from pathlib import Path
        from datetime import datetime, timezone
        from auto_sdlc.logs.report import _infer_user_id
        html_content = render_individual_html(report)
        if output:
            html_path = Path(output).with_suffix(".html")
        else:
            effective_user = (user_id or _infer_user_id()).replace("@", "_at_").replace("/", "_")
            user_dir = Path.home() / ".auto-sdlc" / "reports" / effective_user
            user_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H%M%S")
            html_path = user_dir / "{}.html".format(ts)
        html_path.write_text(html_content, encoding="utf-8")
        click.echo("HTML report saved to {}".format(html_path))

    if export_dir and not summary_only:
        from auto_sdlc.logs.export import export_report_to_dir
        exported_path = export_report_to_dir(report, export_dir)
        click.echo("Report exported to {}".format(exported_path))

    if export_url and not summary_only:
        from auto_sdlc.logs.export import export_report_to_http
        success = export_report_to_http(report, export_url)
        if success:
            click.echo("Report posted to {}".format(export_url))
        else:
            click.echo("Warning: failed to POST report to {}".format(export_url))


@cli.command()
@click.option("--logs-root", default=None,
              help="Root directory containing user subdirs with logs.")
@click.option("--output-dir", default="./auto-sdlc-reports",
              help="Where to write per-user JSON reports + team rollup.")
@click.option("--since", default=None, metavar="YYYY-MM-DD",
              help="Only include sessions on or after this date.")
@click.option("--html", is_flag=True, default=False,
              help="Also render individual + team HTML reports.")
@click.option("--qualitative", is_flag=True, default=False,
              help="Run LLM qualitative analysis (slow, requires claude CLI).")
@click.option("--users-file", default=None,
              help="CSV with user_id,logs_path per line. Overrides directory discovery.")
def ingest(logs_root, output_dir, since, html, qualitative, users_file):
    """Batch-ingest all users' Claude Code logs for team analysis."""
    if not logs_root and not users_file:
        raise click.UsageError("Must provide --logs-root or --users-file")
    from auto_sdlc.logs.ingest import run_bulk_ingest
    run_bulk_ingest(
        logs_root=logs_root,
        output_dir=output_dir,
        since=since,
        html=html,
        qualitative=qualitative,
        users_file=users_file,
    )


@cli.command()
@click.option("--reports-dir", required=True,
              help="Directory containing individual user JSON report files.")
@click.option("--output", default=None,
              help="Write team JSON report to this file.")
@click.option("--html", is_flag=True, default=False,
              help="Also render team HTML report.")
def team(reports_dir, output, html):
    """Aggregate individual user reports into a team maturity report."""
    from auto_sdlc.logs.team import build_team_report_from_dir, render_team_html
    from datetime import datetime, timezone
    from pathlib import Path
    import json

    team_report = build_team_report_from_dir(reports_dir)
    team_report["generated_at"] = datetime.now(tz=timezone.utc).isoformat()

    dest = Path(output) if output else Path(reports_dir) / "team_report.json"
    dest.write_text(json.dumps(team_report, indent=2, default=str), encoding="utf-8")
    click.echo("Team report saved to {}".format(dest))

    if html:
        html_content = render_team_html(team_report)
        html_path = dest.with_suffix(".html")
        html_path.write_text(html_content, encoding="utf-8")
        click.echo("Team HTML report saved to {}".format(html_path))


@cli.command()
@click.option("--reports-dir", default=None,
              help="Directory to store received reports. Defaults to $REPORTS_DIR env var or ~/.auto-sdlc/server/reports/")
@click.option("--host", default="0.0.0.0", show_default=True, help="Host to bind to.")
@click.option("--port", default=None, type=int, help="Port to listen on. Defaults to $PORT env var or 8000.")
def serve(reports_dir, host, port):
    """Start the central collection server."""
    import os
    try:
        import uvicorn
    except ImportError:
        raise click.ClickException("Server deps not installed. Run: pip install 'auto-sdlc[server]'")
    from pathlib import Path
    from auto_sdlc.server import create_app

    # Resolve port: CLI arg → $PORT env var → default 8000
    resolved_port = port or int(os.environ.get("PORT", 8000))

    # Resolve reports dir: CLI arg → $REPORTS_DIR env var → default ~/.auto-sdlc/server/reports/
    if reports_dir:
        resolved = Path(reports_dir)
    else:
        env_dir = os.environ.get("REPORTS_DIR")
        resolved = Path(env_dir) if env_dir else Path.home() / ".auto-sdlc" / "server" / "reports"
    resolved.mkdir(parents=True, exist_ok=True)
    click.echo("Auto-SDLC server starting on http://{}:{}".format(host, resolved_port))
    click.echo("Storing reports in: {}".format(resolved))
    click.echo("Endpoints:")
    click.echo("  POST /reports      — receive a developer report")
    click.echo("  GET  /reports      — list stored reports")
    click.echo("  GET  /team         — live team JSON report")
    click.echo("  GET  /team/html    — live team HTML dashboard")
    app = create_app(str(resolved))
    uvicorn.run(app, host=host, port=resolved_port)


@cli.command(name="init")
def init_cmd():
    """Interactive wizard to generate SDLC config files."""
    run_wizard()


@cli.command()
def audit():
    """Audit installed capabilities against baseline."""
    run_audit()


@cli.command(name="report")
@click.option(
    "--user-id",
    required=True,
    help="User/team identifier for report attribution.",
)
@click.option(
    "--project-path",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to project directory with logs, CLAUDE.md, etc.",
)
@click.option(
    "--output-dir",
    default=None,
    type=click.Path(file_okay=False, dir_okay=True),
    help="Where to save PDF report. Defaults to ~/.auto-sdlc/reports/",
)
@click.option(
    "--report-type",
    type=click.Choice(["team", "individual"], case_sensitive=False),
    default="team",
    help="Report type: 'team' or 'individual'. Defaults to 'team'.",
)
@click.option(
    "--assessment-responses",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Optional: Path to JSON file with assessment question answers.",
)
@click.option(
    "--team-baseline",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Optional: Path to JSON file with team average scores (for individual reports).",
)
def report(user_id, project_path, output_dir, report_type, assessment_responses, team_baseline):
    """
    Generate an AI Maturity Report from project evidence.

    Orchestrates the complete pipeline:
    Evidence Extraction → Assessment → Scoring → Roadmaps → Report Building → PDF Rendering

    EXAMPLES:

    Generate a team report:
    \b
      auto-sdlc report \\
        --user-id platform_team \\
        --project-path /path/to/project

    Generate an individual report with team baseline:
    \b
      auto-sdlc report \\
        --user-id developer_name \\
        --project-path /path/to/project \\
        --report-type individual \\
        --team-baseline ./team_baseline.json

    Generate team report with assessment answers:
    \b
      auto-sdlc report \\
        --user-id platform_team \\
        --project-path /path/to/project \\
        --output-dir ./reports \\
        --assessment-responses ./responses.json

    ASSESSMENT RESPONSES FILE FORMAT:
    \b
      [
        {
          "question_id": "AI_TOOL_ADOPTION_1",
          "answer": "Team uses Claude primarily",
          "confidence": "certain",
          "notes": "Optional additional context"
        },
        ...
      ]

    TEAM BASELINE FILE FORMAT:
    \b
      {
        "AI Tool Adoption": 2.5,
        "Prompt & Context Engineering": 2.3,
        ...
      }
    """
    try:
        from auto_sdlc.reports.pipeline import ReportGenerationPipeline

        pipeline = ReportGenerationPipeline()
        report_obj, pdf_path = pipeline.generate_report(
            user_id=user_id,
            project_path=project_path,
            report_type=report_type.lower(),
            assessment_responses=assessment_responses,
            team_baseline=team_baseline,
            output_dir=output_dir,
        )

        click.echo(f"✓ Report generated successfully")
        click.echo(f"  Type: {report_type}")
        click.echo(f"  File: {pdf_path}")

    except FileNotFoundError as e:
        raise click.ClickException(f"File not found: {e}")
    except ValueError as e:
        raise click.ClickException(f"Invalid input: {e}")
    except Exception as e:
        raise click.ClickException(f"Report generation failed: {e}")
