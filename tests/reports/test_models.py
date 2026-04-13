"""
Tests for Report Data Models

Tests verify correct structure, validation, and constraints for Team and Individual Reports.
"""

import pytest
from datetime import datetime

from auto_sdlc.reports.models import (
    DimensionReport,
    TeamReport,
    IndividualReport,
    ALL_DIMENSIONS,
    CONFIDENCE_LEVELS,
    MATURITY_LEVELS,
)


class TestDimensionReport:
    """Tests for DimensionReport dataclass."""

    def test_dimension_report_creation(self):
        """Test creating a valid DimensionReport."""
        report = DimensionReport(
            dimension="AI Tool Adoption",
            maturity_level=2,
            confidence="high",
            current_state="Team has standardized on Claude Code with 90% adoption.",
            evidence_summary={
                "logs": "90% of sessions use Claude Code",
                "configs": "CLAUDE.md documents tool policy",
            },
            gaps=["No tool usage guidelines"],
            strengths=["High adoption", "Consistent usage patterns"],
            roadmap=[
                {
                    "step": 1,
                    "title": "Expand to 95%+ adoption",
                    "effort_weeks": 2,
                    "effort_hours": 8,
                    "owners": ["Tech Lead"],
                }
            ],
        )

        assert report.dimension == "AI Tool Adoption"
        assert report.maturity_level == 2
        assert report.confidence == "high"
        assert "standardized" in report.current_state
        assert len(report.evidence_summary) == 2
        assert len(report.gaps) == 1
        assert len(report.strengths) == 2
        assert len(report.roadmap) == 1

    def test_dimension_report_invalid_dimension(self):
        """Test that invalid dimension name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid dimension"):
            DimensionReport(
                dimension="Invalid Dimension Name",
                maturity_level=2,
                confidence="high",
                current_state="Some state",
            )

    def test_dimension_report_invalid_maturity_level(self):
        """Test that maturity level outside 1-4 raises ValueError."""
        with pytest.raises(ValueError, match="Maturity level must be 1-4"):
            DimensionReport(
                dimension="AI Tool Adoption",
                maturity_level=5,
                confidence="high",
                current_state="Some state",
            )

        with pytest.raises(ValueError, match="Maturity level must be 1-4"):
            DimensionReport(
                dimension="AI Tool Adoption",
                maturity_level=0,
                confidence="high",
                current_state="Some state",
            )

    def test_dimension_report_invalid_confidence(self):
        """Test that invalid confidence level raises ValueError."""
        with pytest.raises(ValueError, match="Confidence must be one of"):
            DimensionReport(
                dimension="AI Tool Adoption",
                maturity_level=2,
                confidence="extremely_high",
                current_state="Some state",
            )

    def test_dimension_report_empty_current_state(self):
        """Test that empty current_state raises ValueError."""
        with pytest.raises(ValueError, match="current_state must be a non-empty string"):
            DimensionReport(
                dimension="AI Tool Adoption",
                maturity_level=2,
                confidence="high",
                current_state="",
            )

    def test_dimension_report_all_confidence_levels(self):
        """Test DimensionReport works with all valid confidence levels."""
        for confidence in ["high", "medium", "low"]:
            report = DimensionReport(
                dimension="AI Tool Adoption",
                maturity_level=2,
                confidence=confidence,
                current_state=f"Testing with {confidence} confidence",
            )
            assert report.confidence == confidence

    def test_dimension_report_all_maturity_levels(self):
        """Test DimensionReport works with all valid maturity levels."""
        for level in [1, 2, 3, 4]:
            report = DimensionReport(
                dimension="AI Tool Adoption",
                maturity_level=level,
                confidence="high",
                current_state=f"Testing with level {level}",
            )
            assert report.maturity_level == level

    def test_dimension_report_defaults(self):
        """Test that optional fields have correct defaults."""
        report = DimensionReport(
            dimension="AI Tool Adoption",
            maturity_level=1,
            confidence="low",
            current_state="Minimal current state",
        )

        assert report.evidence_summary == {}
        assert report.gaps == []
        assert report.strengths == []
        assert report.roadmap == []


class TestTeamReport:
    """Tests for TeamReport dataclass."""

    @pytest.fixture
    def all_dimension_reports(self):
        """Create a DimensionReport for each of the 12 dimensions."""
        dimensions = {}
        for dim in ALL_DIMENSIONS:
            dimensions[dim] = DimensionReport(
                dimension=dim,
                maturity_level=2,
                confidence="high",
                current_state=f"Current state for {dim}",
                evidence_summary={"logs": "Evidence from logs"},
                gaps=[f"Gap in {dim}"],
                strengths=[f"Strength in {dim}"],
                roadmap=[],
            )
        return dimensions

    def test_team_report_creation(self, all_dimension_reports):
        """Test creating a valid TeamReport with all 12 dimensions."""
        report = TeamReport(
            team_name="Platform Team",
            report_date="2026-04-13",
            data_sources={"logs": True, "configs": True, "capabilities": True},
            team_size=6,
            assessment_period_weeks=12,
            overall_maturity_level=2.3,
            dimensions=all_dimension_reports,
            executive_summary="Platform team shows strong AI tool adoption with solid foundational practices.",
            key_insights=[
                "Tool adoption is high and consistent",
                "Assessment practices emerging but inconsistent",
                "No formal compliance auditing yet",
            ],
            recommendations=[
                "Establish code review standards with /review skill",
                "Document AI governance policy",
            ],
            confidence_by_dimension={dim: "high" for dim in ALL_DIMENSIONS},
            next_steps=["Define tool standards", "Implement governance"],
        )

        assert report.team_name == "Platform Team"
        assert report.report_date == "2026-04-13"
        assert report.team_size == 6
        assert report.assessment_period_weeks == 12
        assert report.overall_maturity_level == 2.3
        assert len(report.dimensions) == 12
        assert len(report.key_insights) == 3
        assert len(report.recommendations) == 2

    def test_team_report_invalid_team_name(self, all_dimension_reports):
        """Test that empty team_name raises ValueError."""
        with pytest.raises(ValueError, match="team_name must be a non-empty string"):
            TeamReport(
                team_name="",
                report_date="2026-04-13",
                dimensions=all_dimension_reports,
                executive_summary="Test",
                confidence_by_dimension={dim: "high" for dim in ALL_DIMENSIONS},
            )

    def test_team_report_invalid_date_format(self, all_dimension_reports):
        """Test that invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="report_date must be ISO format"):
            TeamReport(
                team_name="Team",
                report_date="04-13-2026",  # Wrong format
                dimensions=all_dimension_reports,
                executive_summary="Test",
                confidence_by_dimension={dim: "high" for dim in ALL_DIMENSIONS},
            )

        with pytest.raises(ValueError, match="report_date must be ISO format"):
            TeamReport(
                team_name="Team",
                report_date="2026/04/13",  # Wrong format
                dimensions=all_dimension_reports,
                executive_summary="Test",
                confidence_by_dimension={dim: "high" for dim in ALL_DIMENSIONS},
            )

    def test_team_report_invalid_team_size(self, all_dimension_reports):
        """Test that invalid team_size raises ValueError."""
        with pytest.raises(ValueError, match="team_size must be at least 1"):
            TeamReport(
                team_name="Team",
                report_date="2026-04-13",
                team_size=0,
                dimensions=all_dimension_reports,
                executive_summary="Test",
                confidence_by_dimension={dim: "high" for dim in ALL_DIMENSIONS},
            )

    def test_team_report_invalid_assessment_period(self, all_dimension_reports):
        """Test that negative assessment_period_weeks raises ValueError."""
        with pytest.raises(ValueError, match="assessment_period_weeks must be >= 0"):
            TeamReport(
                team_name="Team",
                report_date="2026-04-13",
                assessment_period_weeks=-1,
                dimensions=all_dimension_reports,
                executive_summary="Test",
                confidence_by_dimension={dim: "high" for dim in ALL_DIMENSIONS},
            )

    def test_team_report_invalid_overall_maturity(self, all_dimension_reports):
        """Test that overall_maturity_level outside 1.0-4.0 raises ValueError."""
        with pytest.raises(ValueError, match="overall_maturity_level must be between 1.0 and 4.0"):
            TeamReport(
                team_name="Team",
                report_date="2026-04-13",
                overall_maturity_level=4.5,
                dimensions=all_dimension_reports,
                executive_summary="Test",
                confidence_by_dimension={dim: "high" for dim in ALL_DIMENSIONS},
            )

        with pytest.raises(ValueError, match="overall_maturity_level must be between 1.0 and 4.0"):
            TeamReport(
                team_name="Team",
                report_date="2026-04-13",
                overall_maturity_level=0.5,
                dimensions=all_dimension_reports,
                executive_summary="Test",
                confidence_by_dimension={dim: "high" for dim in ALL_DIMENSIONS},
            )

    def test_team_report_missing_dimensions(self):
        """Test that missing dimensions raises ValueError."""
        # Only provide 11 dimensions
        incomplete_dims = {dim: DimensionReport(
            dimension=dim,
            maturity_level=2,
            confidence="high",
            current_state="State",
        ) for dim in list(ALL_DIMENSIONS)[:11]}

        with pytest.raises(ValueError, match="Missing dimensions"):
            TeamReport(
                team_name="Team",
                report_date="2026-04-13",
                dimensions=incomplete_dims,
                executive_summary="Test",
                confidence_by_dimension={dim: "high" for dim in list(ALL_DIMENSIONS)[:11]},
            )

    def test_team_report_all_12_dimensions_required(self, all_dimension_reports):
        """Test that TeamReport must have exactly all 12 dimensions."""
        assert len(all_dimension_reports) == 12
        assert len(ALL_DIMENSIONS) == 12

        report = TeamReport(
            team_name="Team",
            report_date="2026-04-13",
            dimensions=all_dimension_reports,
            executive_summary="Test",
            confidence_by_dimension={dim: "high" for dim in ALL_DIMENSIONS},
        )

        assert len(report.dimensions) == 12

    def test_team_report_dimension_mismatch(self, all_dimension_reports):
        """Test that dimension key-value mismatch raises ValueError."""
        mismatched_dims = all_dimension_reports.copy()
        # Create a mismatch: key name differs from dimension value
        # Using "Prompt & Context Engineering" as key but with "AI Tool Adoption" dimension value
        original = mismatched_dims.pop("Prompt & Context Engineering")
        mismatched_dims["Prompt & Context Engineering"] = DimensionReport(
            dimension="AI Tool Adoption",  # Mismatch: key says Prompt but value says AI Tool
            maturity_level=2,
            confidence="high",
            current_state="State",
        )

        with pytest.raises(ValueError, match="Dimension mismatch"):
            TeamReport(
                team_name="Team",
                report_date="2026-04-13",
                dimensions=mismatched_dims,
                executive_summary="Test",
                confidence_by_dimension={dim: "high" for dim in ALL_DIMENSIONS},
            )

    def test_team_report_empty_executive_summary(self, all_dimension_reports):
        """Test that empty executive_summary raises ValueError."""
        with pytest.raises(ValueError, match="executive_summary must be a non-empty string"):
            TeamReport(
                team_name="Team",
                report_date="2026-04-13",
                dimensions=all_dimension_reports,
                executive_summary="",
                confidence_by_dimension={dim: "high" for dim in ALL_DIMENSIONS},
            )

    def test_team_report_missing_confidence_by_dimension(self, all_dimension_reports):
        """Test that missing confidence_by_dimension entries raises ValueError."""
        incomplete_conf = {dim: "high" for dim in list(ALL_DIMENSIONS)[:11]}

        with pytest.raises(ValueError, match="confidence_by_dimension missing"):
            TeamReport(
                team_name="Team",
                report_date="2026-04-13",
                dimensions=all_dimension_reports,
                executive_summary="Test",
                confidence_by_dimension=incomplete_conf,
            )

    def test_team_report_valid_date_formats(self, all_dimension_reports):
        """Test that valid ISO dates work correctly."""
        valid_dates = [
            "2026-04-13",
            "2025-01-01",
            "2027-12-31",
        ]

        for date_str in valid_dates:
            report = TeamReport(
                team_name="Team",
                report_date=date_str,
                dimensions=all_dimension_reports,
                executive_summary="Test",
                confidence_by_dimension={dim: "high" for dim in ALL_DIMENSIONS},
            )
            assert report.report_date == date_str


class TestIndividualReport:
    """Tests for IndividualReport dataclass."""

    @pytest.fixture
    def all_dimension_reports(self):
        """Create a DimensionReport for each of the 12 dimensions."""
        dimensions = {}
        for dim in ALL_DIMENSIONS:
            dimensions[dim] = DimensionReport(
                dimension=dim,
                maturity_level=2,
                confidence="medium",
                current_state=f"Developer's current state for {dim}",
                evidence_summary={"logs": "Evidence from developer logs"},
                gaps=[f"Gap in {dim}"],
                strengths=[f"Strength in {dim}"],
                roadmap=[],
            )
        return dimensions

    def test_individual_report_creation(self, all_dimension_reports):
        """Test creating a valid IndividualReport."""
        report = IndividualReport(
            developer_id="dev_001",
            report_date="2026-04-13",
            assessment_period_weeks=12,
            overall_maturity_level=2.1,
            dimensions=all_dimension_reports,
            executive_summary="Developer shows emerging AI practices with strong tool adoption.",
            usage_patterns={
                "sessions_per_day": 2.5,
                "messages_per_session": 8.3,
                "tools_used": 1,
            },
            strengths=["Strong Claude Code usage", "Good prompt engineering"],
            growth_areas=["Cross-system integration", "Scalability patterns"],
            fit_with_team_baseline="At team average",
            learning_path=["Advanced prompting", "Agent configuration"],
            key_insights=["Developer is adopting tools quickly", "Needs training on governance"],
            recommendations=["Take advanced prompting course", "Pair with experienced mentor"],
        )

        assert report.developer_id == "dev_001"
        assert report.report_date == "2026-04-13"
        assert report.assessment_period_weeks == 12
        assert report.overall_maturity_level == 2.1
        assert len(report.dimensions) == 12
        assert len(report.usage_patterns) == 3
        assert len(report.strengths) == 2
        assert len(report.growth_areas) == 2
        assert len(report.learning_path) == 2

    def test_individual_report_invalid_developer_id(self, all_dimension_reports):
        """Test that empty developer_id raises ValueError."""
        with pytest.raises(ValueError, match="developer_id must be a non-empty string"):
            IndividualReport(
                developer_id="",
                report_date="2026-04-13",
                dimensions=all_dimension_reports,
                executive_summary="Test",
            )

    def test_individual_report_invalid_date_format(self, all_dimension_reports):
        """Test that invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="report_date must be ISO format"):
            IndividualReport(
                developer_id="dev_001",
                report_date="13-04-2026",  # Wrong format
                dimensions=all_dimension_reports,
                executive_summary="Test",
            )

    def test_individual_report_invalid_overall_maturity(self, all_dimension_reports):
        """Test that overall_maturity_level outside 1.0-4.0 raises ValueError."""
        with pytest.raises(ValueError, match="overall_maturity_level must be between 1.0 and 4.0"):
            IndividualReport(
                developer_id="dev_001",
                report_date="2026-04-13",
                overall_maturity_level=4.1,
                dimensions=all_dimension_reports,
                executive_summary="Test",
            )

    def test_individual_report_missing_dimensions(self):
        """Test that missing dimensions raises ValueError."""
        incomplete_dims = {dim: DimensionReport(
            dimension=dim,
            maturity_level=2,
            confidence="high",
            current_state="State",
        ) for dim in list(ALL_DIMENSIONS)[:6]}  # Only half the dimensions

        with pytest.raises(ValueError, match="Missing dimensions"):
            IndividualReport(
                developer_id="dev_001",
                report_date="2026-04-13",
                dimensions=incomplete_dims,
                executive_summary="Test",
            )

    def test_individual_report_empty_executive_summary(self, all_dimension_reports):
        """Test that empty executive_summary raises ValueError."""
        with pytest.raises(ValueError, match="executive_summary must be a non-empty string"):
            IndividualReport(
                developer_id="dev_001",
                report_date="2026-04-13",
                dimensions=all_dimension_reports,
                executive_summary="",
            )

    def test_individual_report_empty_fit_with_team_baseline(self, all_dimension_reports):
        """Test that empty fit_with_team_baseline raises ValueError."""
        with pytest.raises(ValueError, match="fit_with_team_baseline must be a non-empty string"):
            IndividualReport(
                developer_id="dev_001",
                report_date="2026-04-13",
                dimensions=all_dimension_reports,
                executive_summary="Test",
                fit_with_team_baseline="",
            )

    def test_individual_report_defaults(self):
        """Test that optional fields have correct defaults."""
        dimensions = {dim: DimensionReport(
            dimension=dim,
            maturity_level=1,
            confidence="low",
            current_state="State",
        ) for dim in ALL_DIMENSIONS}

        report = IndividualReport(
            developer_id="dev_001",
            report_date="2026-04-13",
            dimensions=dimensions,
            executive_summary="Summary",
            fit_with_team_baseline="At baseline",
        )

        assert report.assessment_period_weeks == 0
        assert report.overall_maturity_level == 1.0
        assert report.usage_patterns == {}
        assert report.strengths == []
        assert report.growth_areas == []
        assert report.learning_path == []
        assert report.key_insights == []
        assert report.recommendations == []

    def test_individual_report_negative_assessment_period(self, all_dimension_reports):
        """Test that negative assessment_period_weeks raises ValueError."""
        with pytest.raises(ValueError, match="assessment_period_weeks must be >= 0"):
            IndividualReport(
                developer_id="dev_001",
                report_date="2026-04-13",
                assessment_period_weeks=-5,
                dimensions=all_dimension_reports,
                executive_summary="Test",
                fit_with_team_baseline="At baseline",
            )


class TestValidationEdgeCases:
    """Additional validation edge case tests."""

    def test_dimension_report_all_valid_dimensions(self):
        """Test that DimensionReport accepts all 12 valid dimensions."""
        for dim_name in ALL_DIMENSIONS:
            report = DimensionReport(
                dimension=dim_name,
                maturity_level=2,
                confidence="high",
                current_state="Test",
            )
            assert report.dimension == dim_name

    def test_team_report_all_maturity_levels(self):
        """Test TeamReport with all valid overall_maturity_level values."""
        dimensions = {dim: DimensionReport(
            dimension=dim,
            maturity_level=2,
            confidence="high",
            current_state="State",
        ) for dim in ALL_DIMENSIONS}

        for level in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
            report = TeamReport(
                team_name="Team",
                report_date="2026-04-13",
                overall_maturity_level=level,
                dimensions=dimensions,
                executive_summary="Test",
                confidence_by_dimension={dim: "high" for dim in ALL_DIMENSIONS},
            )
            assert report.overall_maturity_level == level

    def test_individual_report_all_confidence_levels(self):
        """Test IndividualReport with all valid confidence levels in dimensions."""
        for confidence in ["high", "medium", "low"]:
            dimensions = {dim: DimensionReport(
                dimension=dim,
                maturity_level=2,
                confidence=confidence,
                current_state="State",
            ) for dim in ALL_DIMENSIONS}

            report = IndividualReport(
                developer_id="dev_001",
                report_date="2026-04-13",
                dimensions=dimensions,
                executive_summary="Test",
                fit_with_team_baseline="At baseline",
            )
            assert len(report.dimensions) == 12

    def test_whitespace_in_strings(self):
        """Test that strings with only whitespace are treated as empty."""
        with pytest.raises(ValueError, match="current_state must be a non-empty string"):
            DimensionReport(
                dimension="AI Tool Adoption",
                maturity_level=2,
                confidence="high",
                current_state="   ",  # Only whitespace
            )

        dimensions = {dim: DimensionReport(
            dimension=dim,
            maturity_level=2,
            confidence="high",
            current_state="State",
        ) for dim in ALL_DIMENSIONS}

        with pytest.raises(ValueError, match="team_name must be a non-empty string"):
            TeamReport(
                team_name="   ",  # Only whitespace
                report_date="2026-04-13",
                dimensions=dimensions,
                executive_summary="Test",
                confidence_by_dimension={dim: "high" for dim in ALL_DIMENSIONS},
            )
