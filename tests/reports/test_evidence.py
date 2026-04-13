"""
Tests for Evidence Triangulation Module

Tests verify correct combination of three evidence sources and confidence scoring.
"""

import pytest
from datetime import datetime

from auto_sdlc.reports.evidence import Evidence, EvidenceTriangulator
from auto_sdlc.reports.evidence_extractor import LogEvidence
from auto_sdlc.reports.config_extractor import ConfigEvidence
from auto_sdlc.reports.capability_extractor import CapabilityEvidence


class TestEvidenceTriangulator:
    """Tests for EvidenceTriangulator class."""

    @pytest.fixture
    def triangulator(self):
        """Create triangulator instance."""
        return EvidenceTriangulator()

    def test_triangulate_single_dimension_high_confidence(self, triangulator):
        """Test triangulation with all three sources present and aligned."""
        # Create high confidence log evidence
        log_ev = LogEvidence(
            dimension="Quality Controls",
            signals={"review_usage_pct": 0.85, "test_pattern_prevalence": 0.72},
            raw_metrics={},
            confidence="high",
        )

        # Create documented config evidence
        config_ev = [
            ConfigEvidence(
                dimension="Quality Controls",
                files_present={"CLAUDE.md": True},
                signals={"CLAUDE.md": "review checklist documented"},
                freshness={"CLAUDE.md": datetime.now()},
                quality_indicators={"CLAUDE.md": "documented"},
            )
        ]

        # Create active capability evidence
        cap_ev = [
            CapabilityEvidence(
                dimension="Quality Controls",
                capability_type="skill",
                capabilities=[{"name": "/review", "sophistication_level": "advanced"}],
                deployment_status="active",
                sophistication="advanced",
            )
        ]

        # Triangulate
        evidence = triangulator.triangulate(log_ev, config_ev, cap_ev, "Quality Controls")

        # Verify high confidence
        assert evidence.confidence == "high"
        assert evidence.confidence_score >= 0.7
        assert evidence.dimension == "Quality Controls"
        assert evidence.log_evidence == log_ev
        assert evidence.config_evidence == config_ev
        assert evidence.capability_evidence == cap_ev
        assert "review" in evidence.triangulation_summary.lower()
        assert len(evidence.triangulation_summary) > 0

    def test_triangulate_single_dimension_medium_confidence(self, triangulator):
        """Test triangulation with two sources present and well-aligned."""
        # Log (high) and config (documented) present, no capabilities
        # (1.0 * 0.4) + (1.0 * 0.3) + (0.0 * 0.3) = 0.7 = high confidence
        log_ev = LogEvidence(
            dimension="Ticketing & Planning",
            signals={"jira_references": 0.45},
            raw_metrics={},
            confidence="high",
        )

        config_ev = [
            ConfigEvidence(
                dimension="Ticketing & Planning",
                files_present={"CLAUDE.md": True},
                signals={"CLAUDE.md": "JIRA integration mentioned"},
                freshness={"CLAUDE.md": datetime.now()},
                quality_indicators={"CLAUDE.md": "documented"},
            )
        ]

        cap_ev = []

        evidence = triangulator.triangulate(log_ev, config_ev, cap_ev, "Ticketing & Planning")

        # Verify medium-to-high confidence (two strong sources)
        assert evidence.confidence in ["medium", "high"]
        assert evidence.confidence_score >= 0.4
        assert evidence.log_evidence is not None
        assert len(evidence.config_evidence) > 0
        assert len(evidence.capability_evidence) == 0

    def test_triangulate_single_dimension_low_confidence(self, triangulator):
        """Test triangulation with minimal evidence."""
        # Only log with low confidence
        log_ev = LogEvidence(
            dimension="Measurement & KPIs",
            signals={},
            raw_metrics={},
            confidence="low",
        )

        config_ev = []
        cap_ev = []

        evidence = triangulator.triangulate(log_ev, config_ev, cap_ev, "Measurement & KPIs")

        # Verify low confidence
        assert evidence.confidence == "low"
        assert evidence.confidence_score < 0.4
        assert evidence.log_evidence is not None
        assert len(evidence.config_evidence) == 0
        assert len(evidence.capability_evidence) == 0

    def test_triangulate_missing_log_evidence(self, triangulator):
        """Test triangulation with missing log evidence."""
        log_ev = None
        config_ev = [
            ConfigEvidence(
                dimension="AI Tool Adoption",
                files_present={"CLAUDE.md": True},
                signals={"CLAUDE.md": "Claude model adoption documented"},
                freshness={"CLAUDE.md": datetime.now()},
                quality_indicators={"CLAUDE.md": "documented"},
            )
        ]
        cap_ev = [
            CapabilityEvidence(
                dimension="AI Tool Adoption",
                capability_type="plugin",
                capabilities=[{"name": "superpowers", "version": "1.0"}],
                deployment_status="active",
                sophistication="advanced",
            )
        ]

        evidence = triangulator.triangulate(log_ev, config_ev, cap_ev, "AI Tool Adoption")

        # Should still achieve medium-high confidence with config + capability
        assert evidence.confidence in ["medium", "high"]
        assert evidence.log_evidence is None
        assert len(evidence.config_evidence) > 0
        assert len(evidence.capability_evidence) > 0

    def test_confidence_scoring_logic(self, triangulator):
        """Test that confidence scoring follows the formula correctly."""
        # Test all high signals
        log_ev_high = LogEvidence(
            dimension="Test",
            signals={},
            raw_metrics={},
            confidence="high",
        )
        config_ev_high = [
            ConfigEvidence(
                dimension="Test",
                quality_indicators={"CLAUDE.md": "documented"},
                files_present={},
                signals={},
                freshness={},
            )
        ]
        cap_ev_high = [
            CapabilityEvidence(
                dimension="Test",
                capability_type="skill",
                capabilities=[],
                deployment_status="active",
                sophistication="advanced",
            )
        ]

        confidence_level, score = triangulator._assess_confidence(
            log_ev_high, config_ev_high, cap_ev_high
        )
        # (1.0 * 0.4) + (1.0 * 0.3) + (1.0 * 0.3) = 1.0
        assert score == 1.0
        assert confidence_level == "high"

        # Test all low signals
        log_ev_low = LogEvidence(
            dimension="Test",
            signals={},
            raw_metrics={},
            confidence="low",
        )
        config_ev_low = [
            ConfigEvidence(
                dimension="Test",
                quality_indicators={"CLAUDE.md": "missing"},
                files_present={},
                signals={},
                freshness={},
            )
        ]
        cap_ev_low = [
            CapabilityEvidence(
                dimension="Test",
                capability_type="skill",
                capabilities=[],
                deployment_status="installed",
                sophistication="basic",
            )
        ]

        confidence_level, score = triangulator._assess_confidence(
            log_ev_low, config_ev_low, cap_ev_low
        )
        # (0.0 * 0.4) + (0.0 * 0.3) + (0.25 * 0.3) = 0.075
        assert score < 0.4
        assert confidence_level == "low"

    def test_summary_generation_with_all_sources(self, triangulator):
        """Test that summaries correctly describe evidence from all sources."""
        log_ev = LogEvidence(
            dimension="Quality Controls",
            signals={"review_usage_pct": 0.85, "test_pattern_prevalence": 0.72},
            raw_metrics={},
            confidence="high",
        )

        config_ev = [
            ConfigEvidence(
                dimension="Quality Controls",
                quality_indicators={"CLAUDE.md": "documented", "AGENTS.md": "missing"},
                files_present={"CLAUDE.md": True, "AGENTS.md": True},
                signals={"CLAUDE.md": "test standards defined"},
                freshness={},
            )
        ]

        cap_ev = [
            CapabilityEvidence(
                dimension="Quality Controls",
                capability_type="skill",
                capabilities=[{"name": "/review"}],
                deployment_status="active",
                sophistication="advanced",
            )
        ]

        summary = triangulator._generate_summary(
            "Quality Controls", log_ev, config_ev, cap_ev
        )

        # Verify summary contains references to all sources
        assert "logs show" in summary.lower()
        assert "config" in summary.lower() or "documented" in summary.lower()
        assert "capabilit" in summary.lower()
        assert len(summary) > 50  # Non-trivial summary

    def test_summary_generation_minimal_evidence(self, triangulator):
        """Test summary generation with minimal or missing evidence."""
        log_ev = LogEvidence(
            dimension="Test",
            signals={},
            raw_metrics={},
            confidence="low",
        )

        config_ev = []
        cap_ev = []

        summary = triangulator._generate_summary("Test", log_ev, config_ev, cap_ev)

        # Should mention lack of evidence
        assert "logs show" in summary.lower()
        assert "no capabilities" in summary.lower() or "lack" in summary.lower()
        assert "minimal" in summary.lower()

    def test_triangulate_all_dimensions(self, triangulator):
        """Test triangulation across all 12 dimensions."""
        # Create evidence for all 12 dimensions
        dimensions = [
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

        log_evidence = [
            LogEvidence(
                dimension=dim,
                signals={"signal1": 0.5},
                raw_metrics={},
                confidence="medium" if i % 2 == 0 else "low",
            )
            for i, dim in enumerate(dimensions)
        ]

        config_evidence = [
            ConfigEvidence(
                dimension=dim,
                files_present={"CLAUDE.md": True},
                signals={"CLAUDE.md": "signal"},
                freshness={},
                quality_indicators={"CLAUDE.md": "partial" if i % 3 == 0 else "missing"},
            )
            for i, dim in enumerate(dimensions)
        ]

        cap_evidence = [
            CapabilityEvidence(
                dimension=dim,
                capability_type="skill",
                capabilities=[],
                deployment_status="installed",
                sophistication="basic",
            )
            for i, dim in enumerate(dimensions[:6])  # Only first 6 dimensions
        ]

        # Triangulate all
        evidence_list = triangulator.triangulate_all(
            log_evidence, config_evidence, cap_evidence
        )

        # Verify all 12 dimensions present
        assert len(evidence_list) == 12
        dimensions_found = [e.dimension for e in evidence_list]
        assert set(dimensions_found) == set(dimensions)

        # Verify sorted by confidence
        scores = [e.confidence_score for e in evidence_list]
        assert scores == sorted(scores, reverse=True)

        # Verify each evidence object has correct structure
        for evidence in evidence_list:
            assert evidence.dimension in dimensions
            assert evidence.confidence in ["high", "medium", "low"]
            assert 0.0 <= evidence.confidence_score <= 1.0
            assert len(evidence.triangulation_summary) > 0

    def test_alignment_detection(self, triangulator):
        """Test that alignment between sources is detected correctly."""
        # Case 1: All sources aligned (high confidence)
        log_aligned = LogEvidence(
            dimension="Test",
            signals={"metric": 0.9},
            raw_metrics={},
            confidence="high",
        )
        config_aligned = [
            ConfigEvidence(
                dimension="Test",
                quality_indicators={"CLAUDE.md": "documented"},
                files_present={},
                signals={},
                freshness={},
            )
        ]
        cap_aligned = [
            CapabilityEvidence(
                dimension="Test",
                capability_type="skill",
                capabilities=[],
                deployment_status="active",
                sophistication="advanced",
            )
        ]

        summary_aligned = triangulator._generate_summary(
            "Test", log_aligned, config_aligned, cap_aligned
        )
        assert "well-aligned" in summary_aligned.lower() or "all three" in summary_aligned.lower()

        # Case 2: Misaligned sources (only one strong signal)
        log_weak = LogEvidence(
            dimension="Test",
            signals={},
            raw_metrics={},
            confidence="low",
        )
        config_weak = [
            ConfigEvidence(
                dimension="Test",
                quality_indicators={"CLAUDE.md": "missing"},
                files_present={},
                signals={},
                freshness={},
            )
        ]
        cap_weak = [
            CapabilityEvidence(
                dimension="Test",
                capability_type="skill",
                capabilities=[],
                deployment_status="installed",
                sophistication="basic",
            )
        ]

        summary_weak = triangulator._generate_summary(
            "Test", log_weak, config_weak, cap_weak
        )
        assert "limited alignment" in summary_weak.lower() or "minimal" in summary_weak.lower()

    def test_evidence_dataclass_structure(self):
        """Test that Evidence dataclass has correct structure."""
        log_ev = LogEvidence(
            dimension="Test",
            signals={},
            raw_metrics={},
            confidence="high",
        )

        evidence = Evidence(
            dimension="Test",
            log_evidence=log_ev,
            config_evidence=[],
            capability_evidence=[],
            confidence="high",
            confidence_score=0.85,
            triangulation_summary="Test summary",
        )

        assert evidence.dimension == "Test"
        assert evidence.log_evidence == log_ev
        assert evidence.config_evidence == []
        assert evidence.capability_evidence == []
        assert evidence.confidence == "high"
        assert evidence.confidence_score == 0.85
        assert evidence.triangulation_summary == "Test summary"

    def test_confidence_boundaries(self, triangulator):
        """Test confidence level boundaries at 0.4 and 0.7."""
        # Test at 0.39 (should be low)
        log_ev_low_boundary = LogEvidence(
            dimension="Test",
            signals={},
            raw_metrics={},
            confidence="low",
        )
        config_ev_empty = []
        cap_ev_none = []

        confidence_level, score = triangulator._assess_confidence(
            log_ev_low_boundary, config_ev_empty, cap_ev_none
        )
        # (0.0 * 0.4) + (0.0 * 0.3) + (0.0 * 0.3) = 0.0
        assert score < 0.4
        assert confidence_level == "low"

        # Test at medium boundary
        log_ev_med = LogEvidence(
            dimension="Test",
            signals={},
            raw_metrics={},
            confidence="medium",
        )
        confidence_level, score = triangulator._assess_confidence(
            log_ev_med, config_ev_empty, cap_ev_none
        )
        # (0.5 * 0.4) = 0.2, which is < 0.4
        assert confidence_level == "low"

    def test_multiple_config_evidence_entries(self, triangulator):
        """Test handling multiple config evidence entries for same dimension."""
        log_ev = LogEvidence(
            dimension="Test",
            signals={},
            raw_metrics={},
            confidence="medium",
        )

        # Multiple config entries with different qualities
        config_ev = [
            ConfigEvidence(
                dimension="Test",
                quality_indicators={"CLAUDE.md": "missing"},
                files_present={},
                signals={},
                freshness={},
            ),
            ConfigEvidence(
                dimension="Test",
                quality_indicators={"AGENTS.md": "documented"},
                files_present={},
                signals={},
                freshness={},
            ),
        ]

        cap_ev = []

        confidence_level, score = triangulator._assess_confidence(log_ev, config_ev, cap_ev)

        # Should use best quality (documented = 1.0)
        # (0.5 * 0.4) + (1.0 * 0.3) + (0.0 * 0.3) = 0.2 + 0.3 = 0.5
        assert score >= 0.4  # Should be medium

    def test_multiple_capability_evidence_entries(self, triangulator):
        """Test handling multiple capability evidence entries for same dimension."""
        log_ev = LogEvidence(
            dimension="Test",
            signals={},
            raw_metrics={},
            confidence="high",
        )

        config_ev = []

        # Multiple capability entries with different levels
        cap_ev = [
            CapabilityEvidence(
                dimension="Test",
                capability_type="skill",
                capabilities=[],
                deployment_status="installed",
                sophistication="basic",
            ),
            CapabilityEvidence(
                dimension="Test",
                capability_type="mcp",
                capabilities=[],
                deployment_status="active",
                sophistication="advanced",
            ),
        ]

        confidence_level, score = triangulator._assess_confidence(log_ev, config_ev, cap_ev)

        # Should use best sophistication (active + advanced = 1.0)
        # (1.0 * 0.4) + (0.0 * 0.3) + (1.0 * 0.3) = 0.4 + 0.3 = 0.7
        assert score >= 0.7
        assert confidence_level == "high"
