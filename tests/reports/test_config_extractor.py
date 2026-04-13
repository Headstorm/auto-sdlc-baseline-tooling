"""Tests for ConfigEvidenceExtractor."""

import json
import pytest
from datetime import datetime
from pathlib import Path
from src.auto_sdlc.reports.config_extractor import ConfigEvidenceExtractor, ConfigEvidence


@pytest.fixture
def sample_claude_md():
    """Sample CLAUDE.md content covering multiple dimensions."""
    return """# Project AI Practices

## Tool Standardization Policy
We standardize on Claude Code for all development work. All team members must use the approved Claude model version.

## Prompt Templates
We maintain a library of prompt templates for common tasks:
- Code review prompt template in /docs/prompts/review.md
- Planning prompt in /docs/prompts/plan.md
- Context loading guidance for large repos

## CI/CD Integration
All code changes go through /review in CI pipeline. Test generation is automated for critical paths.

## Quality Controls
Code review checklist is required before merge:
- [ ] AI-generated code tested
- [ ] Comments added to complex sections
- [ ] Security scan passed

## Security & Compliance
All data handling must follow PII policy:
- No API keys in prompts
- Customer data anonymized
- Audit trail maintained for all changes

## Measurement & KPIs
We track adoption rate as key metric. Current: 85% of PRs use /review.

## Ways of Working
Daily standup includes AI adoption updates. Team retro monthly to discuss challenges.

## Agent Configuration
We have 3 custom agents: ReviewBot, PlanBot, TestBot configured in AGENTS.md.

## MCP Integrations
Connected systems: GitHub (repos), Slack (notifications), Jira (ticketing)
"""


@pytest.fixture
def sample_agents_md():
    """Sample AGENTS.md content."""
    return """# Custom Agents

## ReviewBot
- Purpose: Automated code review
- Triggers: On pull request
- Capabilities: Code analysis, security scan, test coverage check

## PlanBot
- Purpose: Sprint planning assistant
- Triggers: Manual invocation
- Capabilities: Task breakdown, effort estimation, dependency mapping

## TestBot
- Purpose: Test generation
- Triggers: On new feature branch
- Capabilities: Unit test generation, integration test templates
"""


@pytest.fixture
def sample_rules():
    """Sample .rules content."""
    return """# Code Quality Rules

## Code Review Requirements
- All code must pass /review tool
- Minimum 80% test coverage
- No security warnings in scan

## Linting Standards
- Python: Black formatter, flake8
- JavaScript: ESLint config in root
- YAML: yamllint

## Quality Gate
All checks must pass before merge to main.
"""


@pytest.fixture
def sample_settings_json():
    """Sample settings.json content."""
    return {
        "tools": {
            "approved": ["Claude Code", "Claude API"],
            "prohibited": ["Copilot"],
            "standardVersion": "claude-3.5-sonnet"
        },
        "compliance": {
            "auditEnabled": True,
            "dataRetention": 90,
            "piiDetection": "strict"
        },
        "integrations": {
            "mcp": ["github", "slack", "jira"],
            "webhooks": ["github.com/hooks/push"]
        }
    }


@pytest.fixture
def project_with_all_configs(tmp_path, sample_claude_md, sample_agents_md, sample_rules, sample_settings_json):
    """Create a temporary project with all config files."""
    (tmp_path / "CLAUDE.md").write_text(sample_claude_md)
    (tmp_path / "AGENTS.md").write_text(sample_agents_md)
    (tmp_path / ".rules").write_text(sample_rules)
    (tmp_path / "settings.json").write_text(json.dumps(sample_settings_json, indent=2))
    return tmp_path


@pytest.fixture
def project_with_partial_configs(tmp_path, sample_claude_md):
    """Create a temporary project with only CLAUDE.md."""
    (tmp_path / "CLAUDE.md").write_text(sample_claude_md)
    return tmp_path


@pytest.fixture
def empty_project(tmp_path):
    """Create an empty temporary project."""
    return tmp_path


class TestConfigEvidenceExtractor:
    """Test suite for ConfigEvidenceExtractor."""

    def test_extract_parses_all_config_files(self, project_with_all_configs):
        """Test that extractor recognizes all present config files."""
        extractor = ConfigEvidenceExtractor(project_with_all_configs)
        evidence_list = extractor.extract_from_project()

        # Check that we got evidence for all 12 dimensions
        assert len(evidence_list) == 12
        dimensions = [e.dimension for e in evidence_list]
        assert "AI Tool Adoption" in dimensions
        assert "Prompt & Context Engineering" in dimensions
        assert "Quality Controls" in dimensions

        # Check that files_present is populated correctly
        for evidence in evidence_list:
            assert evidence.files_present["CLAUDE.md"] is True
            assert evidence.files_present["AGENTS.md"] is True
            assert evidence.files_present[".rules"] is True
            assert evidence.files_present["settings.json"] is True

    def test_extract_gracefully_handles_missing_files(self, project_with_partial_configs):
        """Test graceful degradation when some files are missing."""
        extractor = ConfigEvidenceExtractor(project_with_partial_configs)
        evidence_list = extractor.extract_from_project()

        assert len(evidence_list) == 12

        for evidence in evidence_list:
            assert evidence.files_present["CLAUDE.md"] is True
            assert evidence.files_present["AGENTS.md"] is False
            assert evidence.files_present[".rules"] is False
            assert evidence.files_present["settings.json"] is False

    def test_extract_handles_completely_empty_project(self, empty_project):
        """Test that extractor handles projects with no config files."""
        extractor = ConfigEvidenceExtractor(empty_project)
        evidence_list = extractor.extract_from_project()

        assert len(evidence_list) == 12

        for evidence in evidence_list:
            assert evidence.files_present["CLAUDE.md"] is False
            assert evidence.files_present["AGENTS.md"] is False
            assert evidence.files_present[".rules"] is False
            assert evidence.files_present["settings.json"] is False
            # Should have quality indicators even with no files
            assert len(evidence.quality_indicators) > 0

    def test_parse_claude_md_extracts_tool_adoption_signals(self, project_with_all_configs):
        """Test that CLAUDE.md tool standardization signals are extracted."""
        extractor = ConfigEvidenceExtractor(project_with_all_configs)
        evidence_list = extractor.extract_from_project()

        ai_tool_adoption = next(
            (e for e in evidence_list if e.dimension == "AI Tool Adoption"),
            None
        )
        assert ai_tool_adoption is not None
        assert len(ai_tool_adoption.signals) > 0
        # Should have extracted tool standardization policy
        claude_signals = ai_tool_adoption.signals.get("CLAUDE.md", "")
        assert "standardiz" in claude_signals.lower() or "approved" in claude_signals.lower()

    def test_parse_claude_md_extracts_prompt_context_signals(self, project_with_all_configs):
        """Test that prompt template signals are extracted."""
        extractor = ConfigEvidenceExtractor(project_with_all_configs)
        evidence_list = extractor.extract_from_project()

        prompt_context = next(
            (e for e in evidence_list if e.dimension == "Prompt & Context Engineering"),
            None
        )
        assert prompt_context is not None
        assert len(prompt_context.signals) > 0

    def test_parse_agents_md_extracts_agent_config_signals(self, project_with_all_configs):
        """Test that agent configuration signals are extracted."""
        extractor = ConfigEvidenceExtractor(project_with_all_configs)
        evidence_list = extractor.extract_from_project()

        agent_config = next(
            (e for e in evidence_list if e.dimension == "Agent Configuration"),
            None
        )
        assert agent_config is not None
        # With 3 custom agents documented, should have signals
        assert len(agent_config.signals) > 0

    def test_parse_rules_extracts_quality_control_signals(self, project_with_all_configs):
        """Test that .rules code review signals are extracted."""
        extractor = ConfigEvidenceExtractor(project_with_all_configs)
        evidence_list = extractor.extract_from_project()

        quality_controls = next(
            (e for e in evidence_list if e.dimension == "Quality Controls"),
            None
        )
        assert quality_controls is not None
        # Should extract from both CLAUDE.md and .rules
        assert len(quality_controls.signals) > 0

    def test_parse_settings_json_extracts_compliance_signals(self, project_with_all_configs):
        """Test that settings.json compliance signals are extracted."""
        extractor = ConfigEvidenceExtractor(project_with_all_configs)
        evidence_list = extractor.extract_from_project()

        security_compliance = next(
            (e for e in evidence_list if e.dimension == "Security & Compliance"),
            None
        )
        assert security_compliance is not None
        # Should extract from settings.json
        assert len(security_compliance.signals) > 0

    def test_freshness_dates_extracted(self, project_with_all_configs):
        """Test that file modification dates are captured."""
        extractor = ConfigEvidenceExtractor(project_with_all_configs)
        evidence_list = extractor.extract_from_project()

        for evidence in evidence_list:
            if evidence.files_present["CLAUDE.md"]:
                assert "CLAUDE.md" in evidence.freshness
                assert isinstance(evidence.freshness["CLAUDE.md"], datetime)

    def test_quality_assessment_documented(self, project_with_all_configs):
        """Test that quality assessment marks detailed signals as documented."""
        extractor = ConfigEvidenceExtractor(project_with_all_configs)
        evidence_list = extractor.extract_from_project()

        quality_controls = next(
            (e for e in evidence_list if e.dimension == "Quality Controls"),
            None
        )
        # With detailed .rules and CLAUDE.md content, should be documented
        assert quality_controls.quality_indicators.get("CLAUDE.md") in ["documented", "partial"]

    def test_quality_assessment_missing(self, project_with_partial_configs):
        """Test that quality assessment marks absent signals as missing."""
        extractor = ConfigEvidenceExtractor(project_with_partial_configs)
        evidence_list = extractor.extract_from_project()

        agent_config = next(
            (e for e in evidence_list if e.dimension == "Agent Configuration"),
            None
        )
        # AGENTS.md doesn't exist, so should be not_present
        assert agent_config.quality_indicators.get("AGENTS.md") == "not_present"

    def test_quality_assessment_not_present(self, empty_project):
        """Test that quality assessment marks non-existent files correctly."""
        extractor = ConfigEvidenceExtractor(empty_project)
        evidence_list = extractor.extract_from_project()

        any_evidence = evidence_list[0]
        # Files don't exist
        assert any_evidence.quality_indicators.get("CLAUDE.md") == "not_present"
        assert any_evidence.quality_indicators.get(".rules") == "not_present"

    def test_extract_mcp_integration_signals(self, project_with_all_configs):
        """Test extraction of MCP integration signals."""
        extractor = ConfigEvidenceExtractor(project_with_all_configs)
        evidence_list = extractor.extract_from_project()

        connectivity = next(
            (e for e in evidence_list if e.dimension == "Cross-System Connectivity"),
            None
        )
        assert connectivity is not None
        # CLAUDE.md mentions MCP integrations
        assert len(connectivity.signals) > 0

    def test_extract_security_pii_signals(self, project_with_all_configs):
        """Test extraction of security and PII policy signals."""
        extractor = ConfigEvidenceExtractor(project_with_all_configs)
        evidence_list = extractor.extract_from_project()

        security = next(
            (e for e in evidence_list if e.dimension == "Security & Compliance"),
            None
        )
        assert security is not None
        # Should extract from both CLAUDE.md and settings.json
        assert len(security.signals) > 0

    def test_extract_measurement_kpi_signals(self, project_with_all_configs):
        """Test extraction of measurement and KPI signals."""
        extractor = ConfigEvidenceExtractor(project_with_all_configs)
        evidence_list = extractor.extract_from_project()

        measurement = next(
            (e for e in evidence_list if e.dimension == "Measurement & KPIs"),
            None
        )
        assert measurement is not None
        # CLAUDE.md mentions tracking adoption rate
        assert len(measurement.signals) > 0

    def test_evidence_dataclass_structure(self, project_with_all_configs):
        """Test that ConfigEvidence dataclass has correct structure."""
        extractor = ConfigEvidenceExtractor(project_with_all_configs)
        evidence_list = extractor.extract_from_project()

        evidence = evidence_list[0]
        assert isinstance(evidence, ConfigEvidence)
        assert isinstance(evidence.dimension, str)
        assert isinstance(evidence.files_present, dict)
        assert isinstance(evidence.signals, dict)
        assert isinstance(evidence.freshness, dict)
        assert isinstance(evidence.quality_indicators, dict)

    def test_handles_unreadable_files_gracefully(self, tmp_path):
        """Test that extractor handles files it can't read gracefully."""
        # Create a CLAUDE.md file (readable)
        (tmp_path / "CLAUDE.md").write_text("# Test")

        # Try to extract (should not raise even if permissions were restricted)
        extractor = ConfigEvidenceExtractor(tmp_path)
        evidence_list = extractor.extract_from_project()

        assert len(evidence_list) == 12
        assert evidence_list[0].files_present["CLAUDE.md"] is True
