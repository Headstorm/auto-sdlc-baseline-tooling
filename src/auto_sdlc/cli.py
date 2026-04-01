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
              help="Directory to store received reports. Defaults to ~/.auto-sdlc/server/reports/")
@click.option("--host", default="0.0.0.0", show_default=True, help="Host to bind to.")
@click.option("--port", default=8000, show_default=True, type=int, help="Port to listen on.")
def serve(reports_dir, host, port):
    """Start the central collection server."""
    try:
        import uvicorn
    except ImportError:
        raise click.ClickException("Server deps not installed. Run: pip install 'auto-sdlc[server]'")
    from pathlib import Path
    from auto_sdlc.server import create_app
    resolved = Path(reports_dir) if reports_dir else Path.home() / ".auto-sdlc" / "server" / "reports"
    resolved.mkdir(parents=True, exist_ok=True)
    click.echo("Auto-SDLC server starting on http://{}:{}".format(host, port))
    click.echo("Storing reports in: {}".format(resolved))
    click.echo("Endpoints:")
    click.echo("  POST /reports      — receive a developer report")
    click.echo("  GET  /reports      — list stored reports")
    click.echo("  GET  /team         — live team JSON report")
    click.echo("  GET  /team/html    — live team HTML dashboard")
    app = create_app(str(resolved))
    uvicorn.run(app, host=host, port=port)


@cli.command(name="init")
def init_cmd():
    """Interactive wizard to generate SDLC config files."""
    run_wizard()


@cli.command()
def audit():
    """Audit installed capabilities against baseline."""
    run_audit()
