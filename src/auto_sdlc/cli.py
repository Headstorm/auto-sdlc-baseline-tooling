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
@click.option("--output", default=None, help="Write JSON report to this file path.")
@click.option("--project", default=None,
              help="Filter sessions by project name (matches against working directory).")
@click.option("--since", default=None, metavar="YYYY-MM-DD",
              help="Only include sessions on or after this date.")
@click.option("--summary-only", is_flag=True, default=False,
              help="Print only the summary block, not individual session details.")
def logs(projects_dir, output, project, since, summary_only):
    """Analyze Claude Code session logs."""
    run_logs_report(
        projects_dir=projects_dir,
        output_path=output,
        project_filter=project,
        since=since,
        summary_only=summary_only,
    )


@cli.command(name="init")
def init_cmd():
    """Interactive wizard to generate SDLC config files."""
    run_wizard()


@cli.command()
def audit():
    """Audit installed capabilities against baseline."""
    run_audit()
