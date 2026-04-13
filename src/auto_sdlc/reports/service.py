"""
Report Generation Service Layer

Provides a clean interface to the report generation pipeline.
Used by the web server and any programmatic consumers.
"""

import logging
from pathlib import Path
from typing import Tuple, Optional, Union
from datetime import datetime, timezone

from auto_sdlc.reports.pipeline import ReportGenerationPipeline
from auto_sdlc.reports.models import TeamReport, IndividualReport

logger = logging.getLogger(__name__)


class ReportService:
    """
    Service layer for report generation.

    Wraps ReportGenerationPipeline with output directory handling
    and provides a stable interface for web and programmatic consumers.
    """

    def __init__(self):
        """Initialize the service with a pipeline instance."""
        self.pipeline = ReportGenerationPipeline()

    def generate_report(
        self,
        user_id: str,
        project_path: str,
        report_type: str = "team",
        assessment_responses: Optional[str] = None,
        team_baseline: Optional[str] = None,
        output_dir: Optional[str] = None,
        progress_callback=None,
    ) -> Tuple[Union[TeamReport, IndividualReport], Path]:
        """
        Generate a complete report (team or individual).

        Args:
            user_id: User/team identifier for report attribution
            project_path: Path to project directory with logs, CLAUDE.md, etc.
            report_type: "team" or "individual" (default: "team")
            assessment_responses: Optional path to JSON file with assessment answers
            team_baseline: Optional path to JSON file with team average scores
            output_dir: Where to save PDF. Defaults to ~/.auto-sdlc/reports/
            progress_callback: Optional callable(phase: int, label: str, pct: float)

        Returns:
            Tuple of (Report object, Path to generated PDF)

        Raises:
            ValueError: If inputs are invalid or pipeline step fails
            FileNotFoundError: If required files don't exist
        """
        # Resolve output directory
        if output_dir is None:
            output_dir = str(Path.home() / ".auto-sdlc" / "reports")

        return self.pipeline.generate_report(
            user_id=user_id,
            project_path=project_path,
            report_type=report_type,
            assessment_responses=assessment_responses,
            team_baseline=team_baseline,
            output_dir=output_dir,
            progress_callback=progress_callback,
        )
