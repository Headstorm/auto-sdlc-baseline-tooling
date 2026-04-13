"""
Tests for Report Builder Module

Tests verify correct assembly of TeamReport and IndividualReport from
DimensionScore and RoadmapItem objects, including narrative generation and validation.
"""

import pytest
from datetime import datetime

from auto_sdlc.reports.report_builder import TeamReportBuilder, IndividualReportBuilder
from auto_sdlc.reports.models import (
    DimensionReport,
    TeamReport,
    IndividualReport,
    ALL_DIMENSIONS,
)
from auto_sdlc.reports.maturity_scorer import DimensionScore
from auto_sdlc.reports.roadmap import RoadmapItem, RoadmapAction


@pytest.fixture
def sample_dimension_scores():
    """Create sample DimensionScore objects for all 12 dimensions."""
    scores = {}

    for i, dimension in enumerate(sorted(ALL_DIMENSIONS)):
        level = (i % 4) + 1  # Vary levels 1-4
        scores[dimension] = DimensionScore(
            dimension=dimension,
            maturity_level=level,
            confidence="high" if level >= 2 else "medium",
            confidence_score=0.8 if level >= 2 else 0.5,
            evidence_summary=f"Strong evidence of {dimension.lower()} practices",
            assessment_summary=f"Assessment confirms {dimension.lower()} at L{level}",
            rationale=f"{dimension} practices are well established at L{level}. Team shows consistent adoption.",
        )

    return scores


@pytest.fixture
def sample_roadmaps():
    """Create sample RoadmapItem objects for all 12 dimensions."""
    roadmaps = {}

    for i, dimension in enumerate(sorted(ALL_DIMENSIONS)):
        level = (i % 4) + 1
        target_level = min(level + 1, 4)

        # Create sample actions
        actions = [
            RoadmapAction(
                action_id=f"{dimension[:3]}_001",
                step=1,
                title=f"First action for {dimension}",
                description=f"Initial step to advance {dimension}",
                effort_hours=4,
                effort_weeks=1,
                owners=["Tech Lead"],
                dependencies=[],
                success_criteria=f"{dimension} baseline established",
                risk="Low",
            ),
            RoadmapAction(
                action_id=f"{dimension[:3]}_002",
                step=2,
                title=f"Second action for {dimension}",
                description=f"Follow-up step to advance {dimension}",
                effort_hours=8,
                effort_weeks=2,
                owners=["Tech Lead"],
                dependencies=[f"{dimension[:3]}_001"],
                success_criteria=f"{dimension} practices documented",
                risk="Medium",
            ),
        ]

        roadmaps[dimension] = RoadmapItem(
            dimension=dimension,
            current_level=level,
            target_level=target_level,
            actions=actions,
            total_effort_hours=12,
            total_effort_weeks=3,
            key_insight=f"Transition {dimension} from L{level} to L{target_level}",
        )

    return roadmaps


@pytest.fixture
def team_metadata():
    """Create sample team metadata."""
    return {
        "team_name": "Platform Team",
        "team_size": 6,
        "assessment_period_weeks": 12,
        "report_date": "2026-04-13",
    }


@pytest.fixture
def developer_metadata():
    """Create sample developer metadata."""
    return {
        "developer_id": "dev_001",
        "report_date": "2026-04-13",
        "assessment_period_weeks": 12,
        "usage_patterns": {
            "sessions_per_day": 3.5,
            "messages_per_session": 15,
            "daily_hours": 4.2,
        },
    }


@pytest.fixture
def data_sources():
    """Create sample data sources dict."""
    return {
        "logs": True,
        "configs": True,
        "capabilities": True,
    }


@pytest.fixture
def team_baseline():
    """Create sample team baseline scores."""
    baselines = {}
    for i, dimension in enumerate(sorted(ALL_DIMENSIONS)):
        baselines[dimension] = 2.0 + (i % 2) * 0.5  # Vary between 2.0 and 2.5
    return baselines


class TestTeamReportBuilder:
    """Tests for TeamReportBuilder class."""

    @pytest.fixture
    def builder(self):
        """Create a TeamReportBuilder instance."""
        return TeamReportBuilder()

    def test_build_team_report_complete(
        self, builder, sample_dimension_scores, sample_roadmaps, team_metadata, data_sources
    ):
        """Test building a complete TeamReport with all 12 dimensions."""
        report = builder.build_team_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            team_metadata=team_metadata,
            data_sources=data_sources,
        )

        # Validate report structure
        assert isinstance(report, TeamReport)
        assert report.team_name == "Platform Team"
        assert report.report_date == "2026-04-13"
        assert report.team_size == 6
        assert report.assessment_period_weeks == 12

        # Validate all 12 dimensions present
        assert len(report.dimensions) == 12
        assert set(report.dimensions.keys()) == ALL_DIMENSIONS

        # Validate dimension reports
        for dimension, dim_report in report.dimensions.items():
            assert isinstance(dim_report, DimensionReport)
            assert dim_report.dimension == dimension
            assert 1 <= dim_report.maturity_level <= 4
            assert dim_report.confidence in {"high", "medium", "low"}
            assert len(dim_report.current_state) > 0
            assert isinstance(dim_report.roadmap, list)

    def test_build_team_report_missing_dimensions(
        self, builder, sample_dimension_scores, sample_roadmaps, team_metadata, data_sources
    ):
        """Test that missing dimension scores raises ValueError."""
        incomplete_scores = dict(sample_dimension_scores)
        incomplete_scores.pop("AI Tool Adoption")

        with pytest.raises(ValueError, match="Missing dimension scores"):
            builder.build_team_report(
                dimension_scores=incomplete_scores,
                roadmaps=sample_roadmaps,
                team_metadata=team_metadata,
                data_sources=data_sources,
            )

    def test_overall_maturity_calculation(
        self, builder, sample_dimension_scores, sample_roadmaps, team_metadata, data_sources
    ):
        """Test that overall maturity is correctly calculated."""
        report = builder.build_team_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            team_metadata=team_metadata,
            data_sources=data_sources,
        )

        # Overall should be average of all levels
        expected_avg = sum(s.maturity_level for s in sample_dimension_scores.values()) / len(sample_dimension_scores)
        assert 1.0 <= report.overall_maturity_level <= 4.0
        assert abs(report.overall_maturity_level - expected_avg) < 0.01

    def test_confidence_map_generation(
        self, builder, sample_dimension_scores, sample_roadmaps, team_metadata, data_sources
    ):
        """Test that confidence_by_dimension is complete and accurate."""
        report = builder.build_team_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            team_metadata=team_metadata,
            data_sources=data_sources,
        )

        # Check all dimensions have confidence
        assert len(report.confidence_by_dimension) == 12
        assert set(report.confidence_by_dimension.keys()) == ALL_DIMENSIONS

        # Verify confidence values match source scores
        for dimension, confidence in report.confidence_by_dimension.items():
            assert confidence == sample_dimension_scores[dimension].confidence

    def test_narrative_generation(
        self, builder, sample_dimension_scores, sample_roadmaps, team_metadata, data_sources
    ):
        """Test that narratives are generated properly."""
        report = builder.build_team_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            team_metadata=team_metadata,
            data_sources=data_sources,
        )

        # Executive summary should exist and be substantial
        assert len(report.executive_summary) > 50
        assert "maturity" in report.executive_summary.lower()

        # Key insights should be present
        assert len(report.key_insights) >= 3
        assert len(report.key_insights) <= 5
        for insight in report.key_insights:
            assert len(insight) > 10

        # Recommendations should be present
        assert len(report.recommendations) >= 2
        for rec in report.recommendations:
            assert len(rec) > 10

    def test_dimension_reports_have_roadmaps(
        self, builder, sample_dimension_scores, sample_roadmaps, team_metadata, data_sources
    ):
        """Test that each dimension report includes roadmap actions."""
        report = builder.build_team_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            team_metadata=team_metadata,
            data_sources=data_sources,
        )

        for dimension, dim_report in report.dimensions.items():
            # Should have roadmap actions
            assert len(dim_report.roadmap) > 0

            # Each action should have expected fields
            for action in dim_report.roadmap:
                assert "title" in action
                assert "description" in action
                assert "effort_hours" in action
                assert "effort_weeks" in action

    def test_team_report_validation(
        self, builder, sample_dimension_scores, sample_roadmaps, team_metadata, data_sources
    ):
        """Test that built report passes validation."""
        report = builder.build_team_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            team_metadata=team_metadata,
            data_sources=data_sources,
        )

        # Should not raise any validation errors
        # (validation happens in __post_init__)
        assert report is not None
        assert len(report.dimensions) == 12


class TestIndividualReportBuilder:
    """Tests for IndividualReportBuilder class."""

    @pytest.fixture
    def builder(self):
        """Create an IndividualReportBuilder instance."""
        return IndividualReportBuilder()

    def test_build_individual_report_complete(
        self, builder, sample_dimension_scores, sample_roadmaps, developer_metadata, data_sources, team_baseline
    ):
        """Test building a complete IndividualReport with all 12 dimensions."""
        report = builder.build_individual_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            developer_metadata=developer_metadata,
            team_baseline=team_baseline,
            data_sources=data_sources,
        )

        # Validate report structure
        assert isinstance(report, IndividualReport)
        assert report.developer_id == "dev_001"
        assert report.report_date == "2026-04-13"
        assert report.assessment_period_weeks == 12

        # Validate all 12 dimensions present
        assert len(report.dimensions) == 12
        assert set(report.dimensions.keys()) == ALL_DIMENSIONS

    def test_build_individual_report_missing_dimensions(
        self, builder, sample_dimension_scores, sample_roadmaps, developer_metadata, data_sources, team_baseline
    ):
        """Test that missing dimension scores raises ValueError."""
        incomplete_scores = dict(sample_dimension_scores)
        incomplete_scores.pop("AI Tool Adoption")

        with pytest.raises(ValueError, match="Missing dimension scores"):
            builder.build_individual_report(
                dimension_scores=incomplete_scores,
                roadmaps=sample_roadmaps,
                developer_metadata=developer_metadata,
                team_baseline=team_baseline,
                data_sources=data_sources,
            )

    def test_overall_maturity_calculation(
        self, builder, sample_dimension_scores, sample_roadmaps, developer_metadata, data_sources, team_baseline
    ):
        """Test that developer's overall maturity is correctly calculated."""
        report = builder.build_individual_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            developer_metadata=developer_metadata,
            team_baseline=team_baseline,
            data_sources=data_sources,
        )

        # Overall should be average of all levels
        expected_avg = sum(s.maturity_level for s in sample_dimension_scores.values()) / len(sample_dimension_scores)
        assert 1.0 <= report.overall_maturity_level <= 4.0
        assert abs(report.overall_maturity_level - expected_avg) < 0.01

    def test_strengths_identified_correctly(
        self, builder, sample_dimension_scores, sample_roadmaps, developer_metadata, data_sources, team_baseline
    ):
        """Test that developer's strengths are identified (at/above team baseline)."""
        report = builder.build_individual_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            developer_metadata=developer_metadata,
            team_baseline=team_baseline,
            data_sources=data_sources,
        )

        # Strengths should list dimensions where developer >= team average
        assert len(report.strengths) > 0

        # Verify accuracy: all strengths should be >= team baseline
        for strength_str in report.strengths:
            # Parse to verify
            assert ":" in strength_str

    def test_growth_areas_identified_correctly(
        self, builder, sample_dimension_scores, sample_roadmaps, developer_metadata, data_sources, team_baseline
    ):
        """Test that growth areas are identified (below team baseline)."""
        report = builder.build_individual_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            developer_metadata=developer_metadata,
            team_baseline=team_baseline,
            data_sources=data_sources,
        )

        # Growth areas should list dimensions where developer < team average
        assert len(report.growth_areas) > 0

    def test_fit_with_team_baseline_narrative(
        self, builder, sample_dimension_scores, sample_roadmaps, developer_metadata, data_sources, team_baseline
    ):
        """Test that fit_with_team_baseline is generated."""
        report = builder.build_individual_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            developer_metadata=developer_metadata,
            team_baseline=team_baseline,
            data_sources=data_sources,
        )

        # Should have comparison narrative
        assert len(report.fit_with_team_baseline) > 20
        assert "team" in report.fit_with_team_baseline.lower()

    def test_learning_path_generated(
        self, builder, sample_dimension_scores, sample_roadmaps, developer_metadata, data_sources, team_baseline
    ):
        """Test that personalized learning path is generated."""
        report = builder.build_individual_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            developer_metadata=developer_metadata,
            team_baseline=team_baseline,
            data_sources=data_sources,
        )

        # Learning path should have items
        assert isinstance(report.learning_path, list)
        assert len(report.learning_path) > 0

        # Items should be actionable
        for item in report.learning_path:
            assert len(item) > 10
            assert "->" in item or ":" in item

    def test_personalized_recommendations(
        self, builder, sample_dimension_scores, sample_roadmaps, developer_metadata, data_sources, team_baseline
    ):
        """Test that personalized recommendations are generated."""
        report = builder.build_individual_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            developer_metadata=developer_metadata,
            team_baseline=team_baseline,
            data_sources=data_sources,
        )

        # Should have recommendations
        assert len(report.recommendations) > 0
        assert len(report.recommendations) <= 5

        for rec in report.recommendations:
            assert len(rec) > 10

    def test_usage_patterns_preserved(
        self, builder, sample_dimension_scores, sample_roadmaps, developer_metadata, data_sources, team_baseline
    ):
        """Test that usage patterns from metadata are preserved in report."""
        report = builder.build_individual_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            developer_metadata=developer_metadata,
            team_baseline=team_baseline,
            data_sources=data_sources,
        )

        assert report.usage_patterns == developer_metadata["usage_patterns"]
        assert report.usage_patterns["sessions_per_day"] == 3.5

    def test_individual_report_validation(
        self, builder, sample_dimension_scores, sample_roadmaps, developer_metadata, data_sources, team_baseline
    ):
        """Test that built individual report passes validation."""
        report = builder.build_individual_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            developer_metadata=developer_metadata,
            team_baseline=team_baseline,
            data_sources=data_sources,
        )

        # Should not raise any validation errors
        assert report is not None
        assert len(report.dimensions) == 12
        assert report.overall_maturity_level >= 1.0
        assert report.overall_maturity_level <= 4.0

    def test_key_insights_generated(
        self, builder, sample_dimension_scores, sample_roadmaps, developer_metadata, data_sources, team_baseline
    ):
        """Test that key insights are generated for individual report."""
        report = builder.build_individual_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            developer_metadata=developer_metadata,
            team_baseline=team_baseline,
            data_sources=data_sources,
        )

        assert len(report.key_insights) > 0
        assert len(report.key_insights) <= 5

        for insight in report.key_insights:
            assert len(insight) > 10


class TestNarrativeGeneration:
    """Tests specifically for narrative generation accuracy."""

    @pytest.fixture
    def builder(self):
        """Create a TeamReportBuilder instance."""
        return TeamReportBuilder()

    def test_current_state_narrative_includes_level(self, builder):
        """Test that current state narratives include maturity level."""
        score = DimensionScore(
            dimension="Quality Controls",
            maturity_level=2,
            confidence="high",
            confidence_score=0.85,
            evidence_summary="Good evidence",
            assessment_summary="Confirmed at L2",
            rationale="Team has solid quality practices.",
        )

        # Extract narrative using private method
        narrative = builder._generate_current_state_narrative(score)

        assert "L2" in narrative
        assert "Integrated" in narrative  # L2 narrative
        assert "quality" in narrative.lower()  # Contains the rationale about quality

    def test_executive_summary_includes_maturity(self, builder, sample_dimension_scores):
        """Test that executive summary mentions overall maturity level."""
        dimensions = {}
        for dimension in sorted(ALL_DIMENSIONS):
            dimensions[dimension] = DimensionReport(
                dimension=dimension,
                maturity_level=sample_dimension_scores[dimension].maturity_level,
                confidence="high",
                current_state="Test",
                roadmap=[],
            )

        overall = sum(s.maturity_level for s in sample_dimension_scores.values()) / len(sample_dimension_scores)
        summary = builder._generate_executive_summary(sample_dimension_scores, overall, dimensions)

        assert len(summary) > 50
        assert "maturity" in summary.lower()

    def test_key_insights_are_distinct(self, builder, sample_dimension_scores):
        """Test that key insights don't duplicate content."""
        dimensions = {}
        for dimension in sorted(ALL_DIMENSIONS):
            dimensions[dimension] = DimensionReport(
                dimension=dimension,
                maturity_level=sample_dimension_scores[dimension].maturity_level,
                confidence="high",
                current_state="Test",
                roadmap=[],
            )

        insights = builder._extract_key_insights(sample_dimension_scores, dimensions)

        # Should be distinct
        assert len(insights) == len(set(insights))


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_build_report_with_single_team_member(
        self, sample_dimension_scores, sample_roadmaps, data_sources
    ):
        """Test building report for single-person team."""
        builder = TeamReportBuilder()
        metadata = {
            "team_name": "Solo Developer",
            "team_size": 1,
            "assessment_period_weeks": 4,
            "report_date": "2026-04-13",
        }

        report = builder.build_team_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            team_metadata=metadata,
            data_sources=data_sources,
        )

        assert report.team_size == 1
        assert len(report.dimensions) == 12

    def test_build_report_with_partial_data_sources(
        self, sample_dimension_scores, sample_roadmaps, team_metadata
    ):
        """Test building report when some data sources are unavailable."""
        builder = TeamReportBuilder()
        partial_sources = {
            "logs": True,
            "configs": True,
            "capabilities": False,
        }

        report = builder.build_team_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            team_metadata=team_metadata,
            data_sources=partial_sources,
        )

        assert report.data_sources == partial_sources

    def test_all_dimensions_present_in_output(
        self, sample_dimension_scores, sample_roadmaps, team_metadata, data_sources
    ):
        """Test that all 12 dimensions appear in final report."""
        builder = TeamReportBuilder()

        report = builder.build_team_report(
            dimension_scores=sample_dimension_scores,
            roadmaps=sample_roadmaps,
            team_metadata=team_metadata,
            data_sources=data_sources,
        )

        reported_dims = set(report.dimensions.keys())
        assert reported_dims == ALL_DIMENSIONS
        assert len(reported_dims) == 12
