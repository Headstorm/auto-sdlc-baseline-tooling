"""
Report Generation Pipeline Module

Orchestrates the entire report generation pipeline end-to-end:
Evidence Extraction → Assessment → Scoring → Roadmaps → Report Building → PDF Rendering

This module provides a unified interface to the reporting system, allowing both CLI
and programmatic invocation of report generation.
"""

import json
from pathlib import Path
from typing import Tuple, Optional, Dict, List, Union
from datetime import datetime, timezone

from auto_sdlc.reports.evidence_extractor import LogEvidenceExtractor
from auto_sdlc.reports.config_extractor import ConfigEvidenceExtractor
from auto_sdlc.reports.capability_extractor import CapabilityEvidenceExtractor
from auto_sdlc.reports.evidence import EvidenceTriangulator, Evidence
from auto_sdlc.reports.assessment import (
    AssessmentQuestionsEngine,
    AssessmentResponse,
)
from auto_sdlc.reports.maturity_scorer import MaturityScorer
from auto_sdlc.reports.roadmap import RoadmapGenerator
from auto_sdlc.reports.report_builder import TeamReportBuilder, IndividualReportBuilder
from auto_sdlc.reports.pdf_renderer import PDFRenderer
from auto_sdlc.reports.models import TeamReport, IndividualReport


class ReportGenerationPipeline:
    """
    Orchestrates the complete report generation pipeline.

    Flows through these steps:
    1. Evidence Extraction (logs, configs, capabilities)
    2. Evidence Triangulation (combine sources)
    3. Assessment Loading and Processing
    4. Scoring (12 dimensions)
    5. Roadmap Generation
    6. Report Building
    7. PDF Rendering
    """

    def __init__(self):
        """Initialize the pipeline with all necessary components."""
        # Extractors are initialized per-project (project_path is required)
        self.log_extractor = None
        self.config_extractor = None
        self.capability_extractor = None
        # Other components don't need project path
        self.triangulator = EvidenceTriangulator()
        self.assessment_engine = AssessmentQuestionsEngine()
        self.scorer = MaturityScorer()
        self.roadmap_gen = RoadmapGenerator()
        self.team_builder = TeamReportBuilder()
        self.individual_builder = IndividualReportBuilder()
        self.pdf_renderer = PDFRenderer()

    def generate_report(
        self,
        user_id: str,
        project_path: str,
        report_type: str = "team",
        assessment_responses: Optional[str] = None,
        team_baseline: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> Tuple[Union[TeamReport, IndividualReport], Path]:
        """
        Generate a complete report (team or individual) for a project.

        Args:
            user_id: User/team identifier for report attribution
            project_path: Path to project directory with logs, CLAUDE.md, etc.
            report_type: "team" or "individual" (default: "team")
            assessment_responses: Optional path to JSON file with assessment answers
            team_baseline: Optional path to JSON file with team average scores (for individual reports)
            output_dir: Where to save PDF (default: ~/.auto-sdlc/reports/)

        Returns:
            Tuple of (Report object, Path to generated PDF)

        Raises:
            ValueError: If inputs are invalid or pipeline step fails
            FileNotFoundError: If required files don't exist
        """
        # Validate inputs
        self._validate_inputs(
            user_id, project_path, report_type, assessment_responses, team_baseline
        )

        # Resolve output directory
        if output_dir is None:
            output_dir = Path.home() / ".auto-sdlc" / "reports"
        else:
            output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        project_path = Path(project_path)

        # Initialize extractors with project path
        self.log_extractor = LogEvidenceExtractor()
        self.config_extractor = ConfigEvidenceExtractor(project_path)
        self.capability_extractor = CapabilityEvidenceExtractor(project_path)

        # Step 1: Extract evidence from all sources
        print("✓ Extracting evidence from logs...")
        log_evidence = self.log_extractor.extract_from_project(project_path)

        print("✓ Parsing configurations (CLAUDE.md, AGENTS.md, etc.)...")
        config_evidence = self.config_extractor.extract_from_project()

        print("✓ Scanning capabilities (skills, agents, MCPs)...")
        capability_evidence = self.capability_extractor.extract_from_project(project_path)

        # Step 2: Triangulate evidence sources
        print("✓ Triangulating evidence sources...")
        triangulated_evidence = self.triangulator.triangulate_all(
            log_evidence, config_evidence, capability_evidence
        )

        # Track data sources available
        data_sources = {
            "logs": len(log_evidence) > 0,
            "configs": len(config_evidence) > 0,
            "capabilities": len(capability_evidence) > 0,
        }

        # Step 3: Load and process assessment responses
        print("✓ Loading assessment questions...")
        assessment_responses_list = self._load_assessment_responses(
            assessment_responses
        )

        # Step 4: Score all dimensions
        print("✓ Scoring dimensions...")
        dimension_scores = self.scorer.score_all_dimensions(
            triangulated_evidence, assessment_responses_list
        )

        # Step 5: Generate roadmaps for all dimensions
        print("✓ Generating roadmaps...")
        # Extract dimension levels for roadmap generation
        dimension_levels = {
            dim: score.maturity_level for dim, score in dimension_scores.items()
        }
        roadmap_list = self.roadmap_gen.generate_all_roadmaps(dimension_levels)
        # Convert list to dict for easier access
        roadmaps = {rm.dimension: rm for rm in roadmap_list}

        # Step 6: Build report based on type
        print("✓ Building report...")
        if report_type == "team":
            team_metadata = {
                "team_name": user_id,
                "team_size": 1,  # Can be enhanced with actual team size
                "assessment_period_weeks": self._calculate_assessment_period(
                    project_path
                ),
                "report_date": datetime.now().strftime("%Y-%m-%d"),
            }
            report = self.team_builder.build_team_report(
                dimension_scores, roadmaps, team_metadata, data_sources
            )
        elif report_type == "individual":
            # Load team baseline if provided, else use defaults
            team_baseline_scores = self._load_team_baseline(team_baseline)
            if team_baseline_scores is None:
                # Default to 2.0 (mid-range) for all dimensions if no baseline provided
                team_baseline_scores = {dim: 2.0 for dim in dimension_scores.keys()}

            individual_metadata = {
                "developer_id": user_id,
                "assessment_period_weeks": self._calculate_assessment_period(
                    project_path
                ),
                "report_date": datetime.now().strftime("%Y-%m-%d"),
            }
            report = self.individual_builder.build_individual_report(
                dimension_scores,
                roadmaps,
                individual_metadata,
                team_baseline_scores,
                data_sources,
            )
        else:
            raise ValueError(f"Invalid report_type: {report_type}. Must be 'team' or 'individual'.")

        # Step 7: Render to PDF
        print("✓ Rendering PDF...")
        pdf_path = self._render_pdf(report, user_id, output_dir)

        print(f"\nReport saved to: {pdf_path}")
        return report, pdf_path

    def _validate_inputs(
        self,
        user_id: str,
        project_path: str,
        report_type: str,
        assessment_responses: Optional[str],
        team_baseline: Optional[str],
    ) -> None:
        """
        Validate all input parameters.

        Raises:
            ValueError: If any input is invalid
            FileNotFoundError: If required paths don't exist
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id must be a non-empty string")

        project_path_obj = Path(project_path)
        if not project_path_obj.exists():
            raise FileNotFoundError(f"Project path does not exist: {project_path}")

        if not project_path_obj.is_dir():
            raise ValueError(f"Project path must be a directory: {project_path}")

        if report_type not in ("team", "individual"):
            raise ValueError(
                f"report_type must be 'team' or 'individual', got '{report_type}'"
            )

        if assessment_responses is not None:
            resp_path = Path(assessment_responses)
            if not resp_path.exists():
                raise FileNotFoundError(
                    f"Assessment responses file not found: {assessment_responses}"
                )
            # Validate JSON
            try:
                with open(resp_path) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Assessment responses file is not valid JSON: {e}"
                )

        if team_baseline is not None:
            baseline_path = Path(team_baseline)
            if not baseline_path.exists():
                raise FileNotFoundError(
                    f"Team baseline file not found: {team_baseline}"
                )
            # Validate JSON
            try:
                with open(baseline_path) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Team baseline file is not valid JSON: {e}")

    def _load_assessment_responses(
        self, responses_file: Optional[str]
    ) -> List[AssessmentResponse]:
        """
        Load assessment responses from a JSON file.

        File format: List of dicts with keys:
        - question_id: String identifier
        - answer: Response text
        - confidence: "certain", "likely", or "unsure"
        - notes: Optional additional context

        Args:
            responses_file: Path to JSON file with responses (or None for defaults)

        Returns:
            List of AssessmentResponse objects
        """
        if responses_file is None:
            # Return empty list (evidence-only scoring)
            return []

        try:
            with open(responses_file) as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to load assessment responses: {e}")

        responses = []
        for item in data:
            try:
                response = AssessmentResponse(
                    question_id=item.get("question_id", ""),
                    answer=item.get("answer", ""),
                    confidence=item.get("confidence", "unsure"),
                    notes=item.get("notes", ""),
                )
                responses.append(response)
            except Exception as e:
                raise ValueError(f"Invalid assessment response format: {e}")

        return responses

    def _load_team_baseline(self, baseline_file: Optional[str]) -> Optional[Dict]:
        """
        Load team baseline scores from a JSON file.

        File format: Dict mapping dimension names to average scores (1.0-4.0)
        Example:
        {
            "AI Tool Adoption": 2.5,
            "Prompt & Context Engineering": 2.3,
            ...
        }

        Args:
            baseline_file: Path to JSON file with baseline scores (or None)

        Returns:
            Dict mapping dimension names to float scores, or None
        """
        if baseline_file is None:
            return None

        try:
            with open(baseline_file) as f:
                baseline = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to load team baseline: {e}")

        # Validate structure
        if not isinstance(baseline, dict):
            raise ValueError("Team baseline must be a JSON object")

        return baseline

    def _calculate_assessment_period(self, project_path: Path) -> int:
        """
        Calculate assessment period in weeks from project logs.

        Examines session logs to determine the time span covered.

        Args:
            project_path: Path to project directory

        Returns:
            Number of weeks covered by logs (or 0 if unable to determine)
        """
        # Simple heuristic: count session files and estimate 1 per week
        # More sophisticated logic could examine actual timestamps
        logs_dir = project_path / "logs"
        if not logs_dir.exists():
            return 0

        session_files = list(logs_dir.glob("session_*.json"))
        return max(len(session_files) // 7, 0) if session_files else 0

    def _render_pdf(
        self, report: Union[TeamReport, IndividualReport], user_id: str, output_dir: Path
    ) -> Path:
        """
        Render report to PDF and save to output directory.

        Filename format: {user_id}_report_{date}.pdf

        Args:
            report: TeamReport or IndividualReport object
            user_id: User/team identifier for filename
            output_dir: Directory to save PDF

        Returns:
            Path to generated PDF file
        """
        # Create safe filename from user_id
        safe_user_id = user_id.replace("@", "_at_").replace("/", "_")

        # Generate timestamp
        now = datetime.now(tz=timezone.utc)
        timestamp = now.strftime("%Y-%m-%d_%H%M%S")

        # Build filename
        filename = f"{safe_user_id}_report_{timestamp}.pdf"
        pdf_path = output_dir / filename

        # Render PDF based on report type
        if isinstance(report, TeamReport):
            self.pdf_renderer.render_team_report(report, str(pdf_path))
        elif isinstance(report, IndividualReport):
            self.pdf_renderer.render_individual_report(report, str(pdf_path))
        else:
            raise TypeError(f"Unsupported report type: {type(report)}")

        return pdf_path
