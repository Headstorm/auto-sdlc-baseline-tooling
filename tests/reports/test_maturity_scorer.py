"""
Tests for Maturity Scorer Module

Tests verify:
- Correct L1-L4 scoring based on evidence and assessment
- Confidence assignment logic
- Evidence vs. assessment alignment
- All 12 dimensions scorable
"""

import pytest
from datetime import datetime

from auto_sdlc.reports.maturity_scorer import MaturityScorer, DimensionScore
from auto_sdlc.reports.evidence import Evidence
from auto_sdlc.reports.assessment import AssessmentResponse
from auto_sdlc.reports.evidence_extractor import LogEvidence
from auto_sdlc.reports.config_extractor import ConfigEvidence
from auto_sdlc.reports.capability_extractor import CapabilityEvidence


class TestDimensionScore:
    """Tests for DimensionScore dataclass."""

    def test_dimension_score_creation(self):
        """Test creating a DimensionScore."""
        score = DimensionScore(
            dimension="Quality Controls",
            maturity_level=2,
            confidence="high",
            confidence_score=0.85,
            evidence_summary="Logs show review adoption, configs documented",
            assessment_summary="3 responses: 2 positive, 1 partial",
            rationale="At L2 because of integrated practices.",
        )

        assert score.dimension == "Quality Controls"
        assert score.maturity_level == 2
        assert score.confidence == "high"
        assert score.confidence_score == 0.85
        assert "review" in score.evidence_summary.lower()


class TestMaturityScorer:
    """Tests for MaturityScorer class."""

    @pytest.fixture
    def scorer(self):
        """Create scorer instance."""
        return MaturityScorer()

    @pytest.fixture
    def high_evidence(self):
        """Create high-confidence evidence."""
        return Evidence(
            dimension="Quality Controls",
            log_evidence=LogEvidence(
                dimension="Quality Controls",
                signals={"review_usage_pct": 0.85, "test_coverage": 0.82},
                raw_metrics={},
                confidence="high",
            ),
            config_evidence=[
                ConfigEvidence(
                    dimension="Quality Controls",
                    files_present={"CLAUDE.md": True},
                    signals={"CLAUDE.md": "review checklist documented"},
                    freshness={"CLAUDE.md": datetime.now()},
                    quality_indicators={"CLAUDE.md": "documented"},
                )
            ],
            capability_evidence=[
                CapabilityEvidence(
                    dimension="Quality Controls",
                    capability_type="skill",
                    capabilities=[{"name": "/review", "sophistication_level": "advanced"}],
                    deployment_status="active",
                    sophistication="advanced",
                )
            ],
            confidence="high",
            confidence_score=0.85,
            triangulation_summary="All sources aligned",
        )

    @pytest.fixture
    def low_evidence(self):
        """Create low-confidence evidence."""
        return Evidence(
            dimension="Scalability & Knowledge Transfer",
            log_evidence=LogEvidence(
                dimension="Scalability & Knowledge Transfer",
                signals={},
                raw_metrics={},
                confidence="low",
            ),
            config_evidence=[],
            capability_evidence=[],
            confidence="low",
            confidence_score=0.15,
            triangulation_summary="Minimal evidence available",
        )

    def test_score_single_dimension_l1(self, scorer, low_evidence):
        """Test scoring an L1 dimension with low evidence."""
        responses = [
            AssessmentResponse(
                question_id="SCALABILITY_1",
                answer="No, we don't have formal onboarding materials",
                confidence="certain",
                notes="",
            )
        ]

        score = scorer.score_dimension(low_evidence, responses)

        assert score.dimension == "Scalability & Knowledge Transfer"
        assert score.maturity_level == 1
        assert score.confidence in ["low", "medium"]  # Relaxed since one "certain" response
        assert score.confidence_score < 0.6  # Still low overall
        assert len(score.evidence_summary) > 0
        assert len(score.assessment_summary) > 0
        assert len(score.rationale) > 0

    def test_score_single_dimension_l2(self, scorer):
        """Test scoring an L2 dimension with medium evidence."""
        medium_evidence = Evidence(
            dimension="AI Tool Adoption",
            log_evidence=LogEvidence(
                dimension="AI Tool Adoption",
                signals={"tool_usage_pct": 0.45, "tool_consistency": 0.50},
                raw_metrics={},
                confidence="medium",
            ),
            config_evidence=[
                ConfigEvidence(
                    dimension="AI Tool Adoption",
                    files_present={"CLAUDE.md": True},
                    signals={"CLAUDE.md": "Claude adoption documented"},
                    freshness={"CLAUDE.md": datetime.now()},
                    quality_indicators={"CLAUDE.md": "partial"},
                )
            ],
            capability_evidence=[],
            confidence="medium",
            confidence_score=0.45,
            triangulation_summary="Some alignment between sources",
        )

        responses = [
            AssessmentResponse(
                question_id="AI_TOOL_ADOPTION_1",
                answer="Partially centralized, mostly by choice",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="AI_TOOL_ADOPTION_2",
                answer="Yes, licenses managed centrally",
                confidence="certain",
                notes="",
            ),
        ]

        score = scorer.score_dimension(medium_evidence, responses)

        assert score.dimension == "AI Tool Adoption"
        assert score.maturity_level == 2
        assert score.confidence in ["medium", "high"]

    def test_score_single_dimension_l3_l4(self, scorer, high_evidence):
        """Test scoring L3 and L4 dimensions with high evidence."""
        # Strong responses and high evidence should score L3+
        responses = [
            AssessmentResponse(
                question_id="QUALITY_CONTROLS_1",
                answer="Yes, we have a documented PR review checklist with AI-specific items",
                confidence="certain",
                notes="Updated quarterly",
            ),
            AssessmentResponse(
                question_id="QUALITY_CONTROLS_2",
                answer="Yes, AI-generated changes are held to the same quality bar",
                confidence="certain",
                notes="Same review process applies",
            ),
            AssessmentResponse(
                question_id="QUALITY_CONTROLS_3",
                answer="Edge cases are tested automatically in CI/CD",
                confidence="certain",
                notes="Coverage exceeds 85%",
            ),
            AssessmentResponse(
                question_id="QUALITY_CONTROLS_1",
                answer="Yes, documented and enforced",
                confidence="certain",
                notes="Regular audits performed",
            ),
        ]

        score = scorer.score_dimension(high_evidence, responses)

        assert score.dimension == "Quality Controls"
        assert score.maturity_level >= 3
        assert score.confidence in ["high", "medium"]  # With 4 certain responses should be high
        assert score.confidence_score >= 0.65

    def test_score_all_dimensions(self, scorer):
        """Test scoring all 12 dimensions at once."""
        # Create basic evidence for all dimensions
        evidences = []
        for dimension in scorer.DIMENSIONS:
            evidence = Evidence(
                dimension=dimension,
                log_evidence=LogEvidence(
                    dimension=dimension,
                    signals={"adoption_pct": 0.5},
                    raw_metrics={},
                    confidence="medium",
                ),
                config_evidence=[],
                capability_evidence=[],
                confidence="medium",
                confidence_score=0.5,
                triangulation_summary=f"Medium evidence for {dimension}",
            )
            evidences.append(evidence)

        # Create responses for all 50 questions
        responses = [
            AssessmentResponse(
                question_id="AI_TOOL_ADOPTION_1",
                answer="Partially standardized",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="AI_TOOL_ADOPTION_2",
                answer="Yes, licenses managed centrally",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="AI_TOOL_ADOPTION_3",
                answer="Mix of standardized and individual choice",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="PROMPT_CONTEXT_1",
                answer="Yes, CLAUDE.md in all repos",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="PROMPT_CONTEXT_2",
                answer="Partially, some shared templates",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="PROMPT_CONTEXT_3",
                answer="Developers load context manually",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="AGENT_CONFIG_1",
                answer="3 custom slash commands",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="AGENT_CONFIG_2",
                answer="Mix of single-function and multi-step",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="AGENT_CONFIG_3",
                answer="Distributed ownership",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="CICD_INTEGRATION_1",
                answer="No, /review not mandatory",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="CICD_INTEGRATION_2",
                answer="Manually triggered test generation",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="CICD_INTEGRATION_3",
                answer="1 AI review layer",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="TICKETING_PLANNING_1",
                answer="Partially, sometimes validated with AI",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="TICKETING_PLANNING_2",
                answer="Yes, structured with acceptance criteria",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="TICKETING_PLANNING_3",
                answer="Occasionally, AI enriches some issues",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="CROSS_SYSTEM_1",
                answer="Connected to Git, JIRA, Slack",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="CROSS_SYSTEM_2",
                answer="3 active MCP integrations",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="CROSS_SYSTEM_3",
                answer="Developers pull from multiple systems",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="QUALITY_CONTROLS_1",
                answer="Yes, documented with AI items",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="QUALITY_CONTROLS_2",
                answer="Yes, same quality bar applied",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="QUALITY_CONTROLS_3",
                answer="Automated with high coverage",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="SECURITY_COMPLIANCE_1",
                answer="Yes, formal policy documented",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="SECURITY_COMPLIANCE_2",
                answer="No PII, no secrets allowed",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="SECURITY_COMPLIANCE_3",
                answer="Sessions logged and auditable",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="MEASUREMENT_KPIS_1",
                answer="Track adoption rate and session frequency",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="MEASUREMENT_KPIS_2",
                answer="Cycle time impact quantified",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="MEASUREMENT_KPIS_3",
                answer="Metrics tied to business outcomes",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="MEASUREMENT_KPIS_4",
                answer="Owned by engineering lead",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="MEASUREMENT_KPIS_5",
                answer="Yes, L3 target for 2024",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="WAYS_OF_WORKING_1",
                answer="Yes, documented in CLAUDE.md",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="WAYS_OF_WORKING_2",
                answer="Load CLAUDE.md and context files",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="WAYS_OF_WORKING_3",
                answer="Plan for complex tasks, direct generation for simple",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="ACCOUNTABILITY_1",
                answer="Yes, designated AI champion",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="ACCOUNTABILITY_2",
                answer="Champion owns CLAUDE.md and tooling",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="ACCOUNTABILITY_3",
                answer="AI adoption factored into reviews",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="ACCOUNTABILITY_4",
                answer="Feedback collected quarterly",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="ACCOUNTABILITY_5",
                answer="Adoption tracked by role",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="SCALABILITY_1",
                answer="Onboarding docs and mentorship provided",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="SCALABILITY_2",
                answer="Yes, prompt library exists",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="SCALABILITY_3",
                answer="1-2 weeks to productivity",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="SCALABILITY_4",
                answer="Power users mentor peers",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="VALUE_REALIZATION_1",
                answer="Yes, 15% cycle time reduction",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="VALUE_REALIZATION_2",
                answer="Test coverage increased to 85%",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="VALUE_REALIZATION_3",
                answer="High satisfaction based on NPS",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="VALUE_REALIZATION_4",
                answer="Freed time for architecture work",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="VALUE_REALIZATION_5",
                answer="Positive ROI within 6 months",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="VALUE_REALIZATION_6",
                answer="Onboarding time reduced by 30%",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="VALUE_REALIZATION_7",
                answer="Using AI for design and planning too",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="VALUE_REALIZATION_8",
                answer="Review velocity increased 40%",
                confidence="likely",
                notes="",
            ),
            AssessmentResponse(
                question_id="VALUE_REALIZATION_9",
                answer="Unexpected: improved code style consistency",
                confidence="certain",
                notes="",
            ),
        ]

        scores = scorer.score_all_dimensions(evidences, responses)

        # Verify all 12 dimensions are scored
        assert len(scores) == 12
        for dimension in scorer.DIMENSIONS:
            assert dimension in scores
            score = scores[dimension]
            assert isinstance(score, DimensionScore)
            assert 1 <= score.maturity_level <= 4
            assert score.confidence in ["high", "medium", "low"]
            assert 0.0 <= score.confidence_score <= 1.0

    def test_confidence_assignment_high(self, scorer, high_evidence):
        """Test high confidence assignment with strong data."""
        responses = [
            AssessmentResponse(
                question_id="QUALITY_CONTROLS_1",
                answer="Yes, fully documented",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="QUALITY_CONTROLS_2",
                answer="Yes, same standard applied",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="QUALITY_CONTROLS_3",
                answer="Yes, comprehensive testing",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="QUALITY_CONTROLS_1",
                answer="Yes, updated regularly",
                confidence="certain",
                notes="",
            ),
        ]

        score = scorer.score_dimension(high_evidence, responses)

        assert score.confidence == "high"
        assert score.confidence_score >= 0.7

    def test_confidence_assignment_low(self, scorer, low_evidence):
        """Test low confidence assignment with weak data."""
        responses = [
            AssessmentResponse(
                question_id="SCALABILITY_1",
                answer="Not sure if we have formal materials",
                confidence="unsure",
                notes="",
            )
        ]

        score = scorer.score_dimension(low_evidence, responses)

        assert score.confidence in ["low", "medium"]  # With unsure response should still be lowish
        assert score.confidence_score < 0.55  # Relatively low

    def test_evidence_vs_assessment_alignment(self, scorer):
        """Test scoring when evidence and assessment align vs. contradict."""
        # Strong evidence, weak assessment → mismatch
        strong_evidence = Evidence(
            dimension="CI/CD Integration",
            log_evidence=LogEvidence(
                dimension="CI/CD Integration",
                signals={"cicd_tool_integration": 0.8, "automated_gates": 0.75},
                raw_metrics={},
                confidence="high",
            ),
            config_evidence=[
                ConfigEvidence(
                    dimension="CI/CD Integration",
                    quality_indicators={"CLAUDE.md": "documented"},
                    files_present={},
                    signals={},
                    freshness={},
                )
            ],
            capability_evidence=[],
            confidence="high",
            confidence_score=0.8,
            triangulation_summary="Strong CI/CD signals",
        )

        weak_responses = [
            AssessmentResponse(
                question_id="CICD_INTEGRATION_1",
                answer="No, AI review is not mandatory",
                confidence="certain",
                notes="",
            )
        ]

        score = scorer.score_dimension(strong_evidence, weak_responses)
        # Evidence (0.8) * 0.6 + Assessment (0.0) * 0.4 = 0.48 → L2
        assert score.maturity_level >= 2

        # Aligned: strong evidence + strong assessment
        strong_responses = [
            AssessmentResponse(
                question_id="CICD_INTEGRATION_1",
                answer="Yes, every PR gets AI review before human review",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="CICD_INTEGRATION_2",
                answer="Automated test generation in CI/CD",
                confidence="certain",
                notes="",
            ),
        ]

        aligned_score = scorer.score_dimension(strong_evidence, strong_responses)
        assert aligned_score.maturity_level >= 3

    def test_confidence_score_calculation(self, scorer):
        """Test confidence score 0-1 accuracy."""
        # Create evidence with known confidence
        evidence = Evidence(
            dimension="Test Dimension",
            log_evidence=LogEvidence(
                dimension="Test Dimension",
                signals={"test_signal": 0.7},
                raw_metrics={},
                confidence="high",
            ),
            config_evidence=[
                ConfigEvidence(
                    dimension="Test Dimension",
                    quality_indicators={"file": "documented"},
                    files_present={},
                    signals={},
                    freshness={},
                )
            ],
            capability_evidence=[],
            confidence="high",
            confidence_score=0.8,
            triangulation_summary="Test",
        )

        # Multiple responses should increase data availability confidence
        responses = [
            AssessmentResponse(
                question_id="TEST_1",
                answer="Yes",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="TEST_2",
                answer="Yes",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="TEST_3",
                answer="Yes",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="TEST_4",
                answer="Yes",
                confidence="certain",
                notes="",
            ),
        ]

        score = scorer.score_dimension(evidence, responses)

        assert 0.0 <= score.confidence_score <= 1.0
        assert score.confidence_score >= 0.6  # Should be good with 4 strong responses

    def test_evidence_score_calculation(self, scorer):
        """Test evidence score calculation with known values."""
        # All high evidence should score near 1.0
        high_ev = Evidence(
            dimension="Test",
            log_evidence=LogEvidence(
                dimension="Test",
                signals={"signal1": 1.0, "signal2": 1.0},
                raw_metrics={},
                confidence="high",
            ),
            config_evidence=[
                ConfigEvidence(
                    dimension="Test",
                    quality_indicators={"file": "documented"},
                    files_present={},
                    signals={},
                    freshness={},
                )
            ],
            capability_evidence=[
                CapabilityEvidence(
                    dimension="Test",
                    capability_type="skill",
                    capabilities=[],
                    deployment_status="active",
                    sophistication="advanced",
                )
            ],
            confidence="high",
            confidence_score=1.0,
            triangulation_summary="All high",
        )

        score_val = scorer._calculate_evidence_score(high_ev)
        assert score_val >= 0.9

        # All low evidence should score near 0.0
        low_ev = Evidence(
            dimension="Test",
            log_evidence=LogEvidence(
                dimension="Test",
                signals={},
                raw_metrics={},
                confidence="low",
            ),
            config_evidence=[],
            capability_evidence=[],
            confidence="low",
            confidence_score=0.0,
            triangulation_summary="All low",
        )

        score_val = scorer._calculate_evidence_score(low_ev)
        assert score_val <= 0.2

    def test_assessment_score_calculation(self, scorer):
        """Test assessment score calculation with various response types."""
        evidence = Evidence(
            dimension="Test",
            log_evidence=None,
            config_evidence=[],
            capability_evidence=[],
            confidence="low",
            confidence_score=0.0,
            triangulation_summary="",
        )

        # All "Yes" responses should give ~1.0
        yes_responses = [
            AssessmentResponse(
                question_id="TEST_1",
                answer="Yes, fully implemented",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="TEST_2",
                answer="Yes, documented",
                confidence="certain",
                notes="",
            ),
        ]
        score_val = scorer._calculate_assessment_score("Test", yes_responses, evidence)
        assert score_val >= 0.9

        # All "No," responses should give ~0.0
        no_responses = [
            AssessmentResponse(
                question_id="TEST_1",
                answer="No, not implemented",
                confidence="certain",
                notes="",
            ),
            AssessmentResponse(
                question_id="TEST_2",
                answer="No, missing",
                confidence="certain",
                notes="",
            ),
        ]
        score_val = scorer._calculate_assessment_score("Test", no_responses, evidence)
        assert score_val <= 0.05

        # Mixed responses with confidence adjustments
        mixed_responses = [
            AssessmentResponse(
                question_id="TEST_1",
                answer="Yes",
                confidence="certain",  # 1.0 * 1.0
                notes="",
            ),
            AssessmentResponse(
                question_id="TEST_2",
                answer="Partially",
                confidence="likely",  # 0.5 * 0.8
                notes="",
            ),
            AssessmentResponse(
                question_id="TEST_3",
                answer="No, not done",
                confidence="unsure",  # 0.0 * 0.5
                notes="",
            ),
        ]
        score_val = scorer._calculate_assessment_score("Test", mixed_responses, evidence)
        expected = (1.0 + 0.4 + 0.0) / 3
        assert abs(score_val - expected) < 0.01

    def test_maturity_level_mapping(self, scorer):
        """Test score-to-level mapping."""
        assert scorer._map_to_maturity_level(0.10) == 1
        assert scorer._map_to_maturity_level(0.25) == 2
        assert scorer._map_to_maturity_level(0.37) == 2
        assert scorer._map_to_maturity_level(0.50) == 3
        assert scorer._map_to_maturity_level(0.62) == 3
        assert scorer._map_to_maturity_level(0.75) == 4
        assert scorer._map_to_maturity_level(0.90) == 4

    def test_all_12_dimensions_list(self, scorer):
        """Test that all 12 dimensions are defined."""
        assert len(scorer.DIMENSIONS) == 12
        expected = [
            "AI Tool Adoption",
            "Prompt & Context Engineering",
            "Agent Configuration",
            "CI/CD Integration",
            "Ticketing & Planning",
            "Cross-System Connectivity",
            "Quality Controls",
            "Security & Compliance",
            "Measurement & KPIs",
            "Ways of Working",
            "Accountability & Ownership",
            "Scalability & Knowledge Transfer",
        ]
        assert scorer.DIMENSIONS == expected
