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
def logs(projects_dir, output):
    """Analyze Claude Code session logs."""
    run_logs_report(projects_dir=projects_dir, output_path=output)


@cli.command(name="init")
def init_cmd():
    """Interactive wizard to generate SDLC config files."""
    run_wizard()


@cli.command()
def audit():
    """Audit installed capabilities against baseline."""
    run_audit()
