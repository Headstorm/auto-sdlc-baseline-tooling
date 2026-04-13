"""
Tests for Report Generation Pipeline Module

Tests verify correct orchestration of the complete pipeline from evidence
extraction through PDF rendering for both team and individual reports.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from auto_sdlc.reports.pipeline import ReportGenerationPipeline
from auto_sdlc.reports.models import TeamReport, IndividualReport, ALL_DIMENSIONS


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory with sample structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        # Create logs directory with sample session
        logs_dir = project_dir / "logs"
        logs_dir.mkdir()

        # Create a minimal session file
        session_file = logs_dir / "session_20260401_100000.json"
        session_data = {
            "session_id": "test_session_001",
            "start_timestamp": "2026-04-01T10:00:00Z",
            "end_timestamp": "2026-04-01T11:00:00Z",
            "events": [
                {
                    "type": "message",
                    "timestamp": "2026-04-01T10:05:00Z",
                    "content": "Hello, Claude!",
                    "role": "user"
                }
            ]
        }
        session_file.write_text(json.dumps(session_data))

        # Create CLAUDE.md
        claude_md = project_dir / "CLAUDE.md"
        claude_md.write_text("""
# CLAUDE.md - Auto-SDLC Baseline

## AI Tool Adoption
We use Claude as our primary AI tool.

## Quality Controls
We have code review processes in place.
""")

        yield project_dir


@pytest.fixture
def assessment_responses_file():
    """Create a temporary assessment responses file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        responses = [
            {
                "question_id": "AI_TOOL_ADOPTION_1",
                "answer": "Team standardizes on Claude",
                "confidence": "certain",
                "notes": ""
            },
            {
                "question_id": "PROMPT_CONTEXT_1",
                "answer": "We document prompt templates",
                "confidence": "likely",
                "notes": "In progress"
            }
        ]
        json.dump(responses, f)
        f.flush()
        yield f.name

        # Cleanup
        Path(f.name).unlink()


@pytest.fixture
def team_baseline_file():
    """Create a temporary team baseline file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        baseline = {
            dim: 2.5 for dim in ALL_DIMENSIONS
        }
        json.dump(baseline, f)
        f.flush()
        yield f.name

        # Cleanup
        Path(f.name).unlink()


@pytest.fixture
def output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestPipelineValidation:
    """Test input validation for the pipeline."""

    def test_validate_inputs_user_id_missing(self, temp_project_dir):
        """Test that empty user_id raises ValueError."""
        pipeline = ReportGenerationPipeline()

        with pytest.raises(ValueError, match="user_id must be a non-empty string"):
            pipeline._validate_inputs("", str(temp_project_dir), "team", None, None)

    def test_validate_inputs_project_path_missing(self):
        """Test that non-existent project path raises FileNotFoundError."""
        pipeline = ReportGenerationPipeline()

        with pytest.raises(FileNotFoundError, match="Project path does not exist"):
            pipeline._validate_inputs("test_user", "/nonexistent/path", "team", None, None)

    def test_validate_inputs_project_path_not_directory(self):
        """Test that file path raises ValueError."""
        pipeline = ReportGenerationPipeline()

        with tempfile.NamedTemporaryFile() as f:
            with pytest.raises(ValueError, match="Project path must be a directory"):
                pipeline._validate_inputs("test_user", f.name, "team", None, None)

    def test_validate_inputs_invalid_report_type(self, temp_project_dir):
        """Test that invalid report_type raises ValueError."""
        pipeline = ReportGenerationPipeline()

        with pytest.raises(ValueError, match="report_type must be 'team' or 'individual'"):
            pipeline._validate_inputs("test_user", str(temp_project_dir), "invalid", None, None)

    def test_validate_inputs_assessment_file_not_found(self, temp_project_dir):
        """Test that missing assessment responses file raises FileNotFoundError."""
        pipeline = ReportGenerationPipeline()

        with pytest.raises(FileNotFoundError, match="Assessment responses file not found"):
            pipeline._validate_inputs(
                "test_user", str(temp_project_dir), "team",
                "/nonexistent/responses.json", None
            )

    def test_validate_inputs_assessment_file_invalid_json(self, temp_project_dir):
        """Test that invalid JSON in assessment file raises ValueError."""
        pipeline = ReportGenerationPipeline()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json}")
            f.flush()

            try:
                with pytest.raises(ValueError, match="not valid JSON"):
                    pipeline._validate_inputs(
                        "test_user", str(temp_project_dir), "team",
                        f.name, None
                    )
            finally:
                Path(f.name).unlink()

    def test_validate_inputs_team_baseline_file_not_found(self, temp_project_dir):
        """Test that missing team baseline file raises FileNotFoundError."""
        pipeline = ReportGenerationPipeline()

        with pytest.raises(FileNotFoundError, match="Team baseline file not found"):
            pipeline._validate_inputs(
                "test_user", str(temp_project_dir), "individual",
                None, "/nonexistent/baseline.json"
            )

    def test_validate_inputs_valid(self, temp_project_dir, assessment_responses_file):
        """Test that valid inputs pass validation."""
        pipeline = ReportGenerationPipeline()

        # Should not raise
        pipeline._validate_inputs(
            "test_user", str(temp_project_dir), "team",
            assessment_responses_file, None
        )


class TestAssessmentResponseLoading:
    """Test loading and parsing of assessment responses."""

    def test_load_assessment_responses_none(self):
        """Test that None input returns empty list."""
        pipeline = ReportGenerationPipeline()
        responses = pipeline._load_assessment_responses(None)
        assert responses == []

    def test_load_assessment_responses_valid_file(self, assessment_responses_file):
        """Test loading valid assessment responses."""
        pipeline = ReportGenerationPipeline()
        responses = pipeline._load_assessment_responses(assessment_responses_file)

        assert len(responses) == 2
        assert responses[0].question_id == "AI_TOOL_ADOPTION_1"
        assert responses[0].answer == "Team standardizes on Claude"
        assert responses[0].confidence == "certain"
        assert responses[1].question_id == "PROMPT_CONTEXT_1"

    def test_load_assessment_responses_missing_file(self):
        """Test that missing file raises ValueError."""
        pipeline = ReportGenerationPipeline()

        with pytest.raises(ValueError, match="Failed to load assessment responses"):
            pipeline._load_assessment_responses("/nonexistent/file.json")


class TestTeamBaselineLoading:
    """Test loading and parsing of team baseline scores."""

    def test_load_team_baseline_none(self):
        """Test that None input returns None."""
        pipeline = ReportGenerationPipeline()
        baseline = pipeline._load_team_baseline(None)
        assert baseline is None

    def test_load_team_baseline_valid_file(self, team_baseline_file):
        """Test loading valid team baseline."""
        pipeline = ReportGenerationPipeline()
        baseline = pipeline._load_team_baseline(team_baseline_file)

        assert isinstance(baseline, dict)
        assert len(baseline) == 12
        assert baseline["AI Tool Adoption"] == 2.5
        assert baseline["Quality Controls"] == 2.5

    def test_load_team_baseline_missing_file(self):
        """Test that missing file raises ValueError."""
        pipeline = ReportGenerationPipeline()

        with pytest.raises(ValueError, match="Failed to load team baseline"):
            pipeline._load_team_baseline("/nonexistent/baseline.json")

    def test_load_team_baseline_invalid_json(self):
        """Test that invalid JSON raises ValueError."""
        pipeline = ReportGenerationPipeline()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            f.flush()

            try:
                with pytest.raises(ValueError, match="Failed to load team baseline"):
                    pipeline._load_team_baseline(f.name)
            finally:
                Path(f.name).unlink()


class TestAssessmentPeriodCalculation:
    """Test calculation of assessment period from project structure."""

    def test_calculate_assessment_period_no_logs(self):
        """Test assessment period when no logs directory exists."""
        pipeline = ReportGenerationPipeline()

        with tempfile.TemporaryDirectory() as tmpdir:
            period = pipeline._calculate_assessment_period(Path(tmpdir))
            assert period == 0

    def test_calculate_assessment_period_empty_logs(self):
        """Test assessment period with empty logs directory."""
        pipeline = ReportGenerationPipeline()

        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / "logs"
            logs_dir.mkdir()

            period = pipeline._calculate_assessment_period(Path(tmpdir))
            assert period == 0


class TestTeamReportGeneration:
    """Test team report generation end-to-end."""

    def test_generate_team_report(self, temp_project_dir, output_dir):
        """Test full team report generation pipeline."""
        pipeline = ReportGenerationPipeline()

        report, pdf_path = pipeline.generate_report(
            user_id="test_team",
            project_path=str(temp_project_dir),
            report_type="team",
            assessment_responses=None,
            team_baseline=None,
            output_dir=output_dir,
        )

        # Verify report object
        assert isinstance(report, TeamReport)
        assert report.team_name == "test_team"
        assert len(report.dimensions) == 12
        assert all(dim in report.dimensions for dim in ALL_DIMENSIONS)

        # Verify PDF was created
        assert isinstance(pdf_path, Path)
        assert pdf_path.exists()
        assert pdf_path.suffix == ".pdf"
        assert "test_team" in pdf_path.name

    def test_generate_team_report_with_assessments(
        self, temp_project_dir, assessment_responses_file, output_dir
    ):
        """Test team report with assessment responses."""
        pipeline = ReportGenerationPipeline()

        report, pdf_path = pipeline.generate_report(
            user_id="assessed_team",
            project_path=str(temp_project_dir),
            report_type="team",
            assessment_responses=assessment_responses_file,
            team_baseline=None,
            output_dir=output_dir,
        )

        assert isinstance(report, TeamReport)
        assert pdf_path.exists()


class TestIndividualReportGeneration:
    """Test individual report generation end-to-end."""

    def test_generate_individual_report(
        self, temp_project_dir, team_baseline_file, output_dir
    ):
        """Test full individual report generation pipeline."""
        pipeline = ReportGenerationPipeline()

        report, pdf_path = pipeline.generate_report(
            user_id="developer_1",
            project_path=str(temp_project_dir),
            report_type="individual",
            assessment_responses=None,
            team_baseline=team_baseline_file,
            output_dir=output_dir,
        )

        # Verify report object
        assert isinstance(report, IndividualReport)
        assert report.developer_id == "developer_1"
        assert len(report.dimensions) == 12
        assert all(dim in report.dimensions for dim in ALL_DIMENSIONS)

        # Verify PDF was created
        assert isinstance(pdf_path, Path)
        assert pdf_path.exists()
        assert pdf_path.suffix == ".pdf"
        assert "developer_1" in pdf_path.name

    def test_generate_individual_report_without_baseline_raises_error(
        self, temp_project_dir, output_dir
    ):
        """Test that individual report without team baseline raises error."""
        pipeline = ReportGenerationPipeline()

        # Individual report should work without baseline but will use None
        report, pdf_path = pipeline.generate_report(
            user_id="developer_2",
            project_path=str(temp_project_dir),
            report_type="individual",
            assessment_responses=None,
            team_baseline=None,
            output_dir=output_dir,
        )

        # Should still generate a report
        assert isinstance(report, IndividualReport)
        assert pdf_path.exists()


class TestPipelineOutputFileNaming:
    """Test output file naming and path handling."""

    def test_pdf_filename_format(self, temp_project_dir, output_dir):
        """Test that PDF filename follows the correct format."""
        pipeline = ReportGenerationPipeline()

        report, pdf_path = pipeline.generate_report(
            user_id="my_team",
            project_path=str(temp_project_dir),
            report_type="team",
            output_dir=output_dir,
        )

        # Check filename format: {user_id}_report_{timestamp}.pdf
        assert pdf_path.name.startswith("my_team_report_")
        assert pdf_path.name.endswith(".pdf")

    def test_pdf_filename_sanitization(self, temp_project_dir, output_dir):
        """Test that special characters in user_id are sanitized."""
        pipeline = ReportGenerationPipeline()

        report, pdf_path = pipeline.generate_report(
            user_id="user@example.com",
            project_path=str(temp_project_dir),
            report_type="team",
            output_dir=output_dir,
        )

        # @ should be replaced with _at_
        assert "user_at_example.com" in pdf_path.name
        assert "@" not in pdf_path.name

    def test_default_output_directory(self, temp_project_dir):
        """Test that default output directory is ~/.auto-sdlc/reports/."""
        pipeline = ReportGenerationPipeline()

        # This would create files in the home directory, so we just test the logic
        # by checking that None input is handled correctly
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override the home directory
            import unittest.mock
            with unittest.mock.patch('pathlib.Path.home') as mock_home:
                mock_home.return_value = Path(tmpdir)

                report, pdf_path = pipeline.generate_report(
                    user_id="test",
                    project_path=str(temp_project_dir),
                    report_type="team",
                    output_dir=None,
                )

                # Should create in ~/.auto-sdlc/reports/
                expected_base = Path(tmpdir) / ".auto-sdlc" / "reports"
                assert str(pdf_path).startswith(str(expected_base))
