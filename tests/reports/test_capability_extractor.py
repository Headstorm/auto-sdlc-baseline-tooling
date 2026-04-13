"""
Tests for the Capability Evidence Extractor module.

Tests cover:
1. MCP integration detection
2. Skill inventory and count
3. Agent detection from AGENTS.md
4. Sophistication assessment
"""

import json
from pathlib import Path

import pytest

from src.auto_sdlc.reports.capability_extractor import (
    CapabilityEvidence,
    CapabilityEvidenceExtractor,
)


@pytest.fixture
def temp_home(tmp_path):
    """Create a temporary home directory with .claude structure."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    (claude_dir / "plugins").mkdir()
    (claude_dir / "commands").mkdir()
    (claude_dir / "agents").mkdir()
    return tmp_path


@pytest.fixture
def extractor(temp_home):
    """Create an extractor instance with temp home."""
    return CapabilityEvidenceExtractor(home_dir=temp_home)


class TestMCPIntegrationDetection:
    """Test MCP integration detection."""

    def test_scan_mcp_integrations_empty(self, extractor):
        """Test MCP scanning when no MCPs are configured."""
        mcps = extractor._scan_mcp_integrations()
        assert isinstance(mcps, list)
        assert len(mcps) == 0

    def test_scan_mcp_integrations_from_mcp_json(self, extractor, temp_home):
        """Test detecting MCPs from mcp.json."""
        mcp_config = {
            "mcpServers": {
                "github": {
                    "version": "1.0.0",
                    "type": "server",
                },
                "jira": {
                    "version": "2.1.0",
                    "type": "server",
                },
            }
        }

        mcp_file = temp_home / ".claude" / "mcp.json"
        mcp_file.write_text(json.dumps(mcp_config))

        mcps = extractor._scan_mcp_integrations()
        assert len(mcps) == 2
        names = {mcp["name"] for mcp in mcps}
        assert "github" in names
        assert "jira" in names

    def test_scan_mcp_integrations_from_plugin_mcp_json(self, extractor, temp_home):
        """Test detecting MCPs from plugin .mcp.json files."""
        # Create plugin MCP config
        plugin_dir = temp_home / ".claude" / "plugins" / "my-plugin"
        plugin_dir.mkdir(parents=True)

        mcp_config = {
            "name": "slack-integration",
            "version": "1.5.0",
            "type": "server",
        }

        mcp_file = plugin_dir / ".mcp.json"
        mcp_file.write_text(json.dumps(mcp_config))

        mcps = extractor._scan_mcp_integrations()
        assert len(mcps) >= 1
        slack_mcp = next((m for m in mcps if "slack" in m["name"].lower()), None)
        assert slack_mcp is not None
        assert slack_mcp["version"] == "1.5.0"

    def test_mcp_sophistication_assessment(self, extractor):
        """Test sophistication assessment for MCPs."""
        # Basic MCP
        basic_mcp = {"name": "github", "capabilities": []}
        assert extractor._assess_mcp_sophistication(basic_mcp) == "basic"

        # Intermediate MCP
        intermediate_mcp = {"name": "jira-server", "capabilities": ["create", "update", "query"]}
        assert extractor._assess_mcp_sophistication(intermediate_mcp) == "intermediate"

        # Advanced MCP (multi-system)
        advanced_mcp = {"name": "jira-slack-confluence", "capabilities": []}
        assert extractor._assess_mcp_sophistication(advanced_mcp) == "advanced"

    def test_mcp_deduplication(self, extractor, temp_home):
        """Test that MCPs are deduplicated by name."""
        # Create two MCP entries with same name
        mcp_config = {
            "mcpServers": {
                "github": {"version": "1.0.0", "type": "server"},
            }
        }

        mcp_file = temp_home / ".claude" / "mcp.json"
        mcp_file.write_text(json.dumps(mcp_config))

        # Also create a plugin MCP with same name
        plugin_dir = temp_home / ".claude" / "plugins" / "github-plugin"
        plugin_dir.mkdir(parents=True)
        plugin_mcp = {"name": "github", "version": "2.0.0", "type": "server"}
        (plugin_dir / ".mcp.json").write_text(json.dumps(plugin_mcp))

        mcps = extractor._scan_mcp_integrations()
        github_mcps = [m for m in mcps if m["name"] == "github"]
        assert len(github_mcps) == 1


class TestSkillInventory:
    """Test skill detection and inventory."""

    def test_scan_skills_empty(self, extractor):
        """Test skill scanning when no skills are present."""
        skills = extractor._scan_skills()
        # Should find at least superpowers if it's installed
        assert isinstance(skills, list)

    def test_skill_sophistication_assessment(self, extractor):
        """Test skill sophistication assessment."""
        # Advanced skill
        assert extractor._assess_skill_sophistication("execute-plan") == "advanced"
        assert extractor._assess_skill_sophistication("systematic-debugging") == "advanced"

        # Intermediate skill
        assert extractor._assess_skill_sophistication("write-plan") == "intermediate"
        assert extractor._assess_skill_sophistication("brainstorm") == "intermediate"

        # Basic skill
        assert extractor._assess_skill_sophistication("custom-skill") == "basic"

    def test_scan_custom_skills(self, extractor, temp_home):
        """Test scanning custom skills from ~/.claude/commands/."""
        # Create custom skill structure
        custom_skill_dir = temp_home / ".claude" / "commands" / "my-review"
        custom_skill_dir.mkdir(parents=True)
        (custom_skill_dir / "SKILL.md").write_text("# My Review Skill")

        skills = extractor._scan_skills()
        custom_skills = [s for s in skills if s.get("source") == "custom"]
        assert len(custom_skills) > 0
        assert any(s["name"] == "my-review" for s in custom_skills)

    def test_skill_count(self, extractor, temp_home):
        """Test that skill count is accurate."""
        # Create multiple custom skills
        for skill_name in ["skill-a", "skill-b", "skill-c"]:
            skill_dir = temp_home / ".claude" / "commands" / skill_name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(f"# {skill_name}")

        skills = extractor._scan_skills()
        custom_skills = [s for s in skills if s.get("source") == "custom"]
        assert len(custom_skills) >= 3


class TestAgentDetection:
    """Test agent detection from AGENTS.md and agents/ directory."""

    def test_scan_agents_empty(self, extractor):
        """Test agent scanning with no agents."""
        agents = extractor._scan_agents(Path("/tmp"))
        assert isinstance(agents, list)
        assert len(agents) == 0

    def test_agents_from_agents_md(self, extractor, temp_home):
        """Test detecting agents from AGENTS.md file."""
        project_path = temp_home / "my-project"
        project_path.mkdir()

        agents_md = project_path / "AGENTS.md"
        agents_md.write_text(
            """# Agents

## Code Review Agent
Handles code review workflows.

## Test Generation Agent
Generates test cases automatically.
"""
        )

        agents = extractor._scan_agents(project_path)
        assert len(agents) == 2
        agent_names = {a["name"] for a in agents}
        assert "Code Review Agent" in agent_names
        assert "Test Generation Agent" in agent_names

    def test_agents_from_agents_directory(self, extractor, temp_home):
        """Test detecting agents from ~/.claude/agents/ directory."""
        # Create agent configs
        agents_dir = temp_home / ".claude" / "agents"
        agents_dir.mkdir(exist_ok=True)

        agent1 = {
            "name": "code-reviewer",
            "version": "1.0.0",
            "tools": ["git", "code-analysis"],
            "workflows": ["review"],
        }
        (agents_dir / "code-reviewer.json").write_text(json.dumps(agent1))

        agent2 = {
            "name": "documentation-agent",
            "version": "2.0.0",
            "tools": ["docs", "markdown"],
        }
        (agents_dir / "documentation-agent.json").write_text(json.dumps(agent2))

        agents = extractor._scan_agents(Path("/tmp"))
        assert len(agents) == 2
        agent_names = {a["name"] for a in agents}
        assert "code-reviewer" in agent_names
        assert "documentation-agent" in agent_names

    def test_agent_sophistication_assessment(self, extractor):
        """Test sophistication assessment for agents."""
        # Basic agent (few tools)
        basic_agent = {"tools": ["tool1"], "workflows": []}
        assert extractor._assess_agent_sophistication(basic_agent) == "basic"

        # Intermediate agent (moderate tools)
        intermediate_agent = {"tools": ["tool1", "tool2", "tool3"], "workflows": []}
        assert extractor._assess_agent_sophistication(intermediate_agent) == "intermediate"

        # Advanced agent (many tools + workflows)
        advanced_agent = {
            "tools": ["tool1", "tool2", "tool3", "tool4", "tool5", "tool6"],
            "workflows": ["workflow1"],
        }
        assert extractor._assess_agent_sophistication(advanced_agent) == "advanced"


class TestCapabilityEvidenceMapping:
    """Test mapping capabilities to dimensions."""

    def test_capability_evidence_dataclass(self):
        """Test CapabilityEvidence dataclass."""
        evidence = CapabilityEvidence(
            dimension="AI Tool Adoption",
            capability_type="plugin",
            capabilities=[{"name": "superpowers"}],
            deployment_status="active",
            sophistication="advanced",
        )

        assert evidence.dimension == "AI Tool Adoption"
        assert evidence.capability_type == "plugin"
        assert len(evidence.capabilities) == 1
        assert evidence.deployment_status == "active"
        assert evidence.sophistication == "advanced"

    def test_extract_from_project_returns_evidence_list(self, extractor):
        """Test that extract_from_project returns CapabilityEvidence objects."""
        evidence_list = extractor.extract_from_project(Path("/tmp"))
        assert isinstance(evidence_list, list)
        for evidence in evidence_list:
            assert isinstance(evidence, CapabilityEvidence)

    def test_ai_tool_adoption_dimension(self, extractor):
        """Test AI Tool Adoption dimension gathering."""
        adoption = extractor._gather_tool_adoption()
        assert "type" in adoption
        assert "capabilities" in adoption
        assert "status" in adoption
        assert "sophistication" in adoption

    def test_agent_configuration_dimension(self, extractor):
        """Test Agent Configuration dimension gathering."""
        config = extractor._gather_agent_configuration()
        assert "type" in config
        assert config["type"] == "agent"
        assert isinstance(config["capabilities"], list)

    def test_cross_system_connectivity_dimension(self, extractor, temp_home):
        """Test Cross-System Connectivity dimension with multiple MCPs."""
        # Create multiple MCP integrations
        mcp_config = {
            "mcpServers": {
                "jira": {"version": "1.0.0"},
                "slack": {"version": "1.0.0"},
                "confluence": {"version": "1.0.0"},
            }
        }

        mcp_file = temp_home / ".claude" / "mcp.json"
        mcp_file.write_text(json.dumps(mcp_config))

        extractor._scan_mcp_integrations()
        extractor.mcp_cache = extractor._scan_mcp_integrations()

        cross_system = extractor._gather_cross_system()
        assert cross_system["sophistication"] == "advanced"
        assert len(cross_system["capabilities"]) >= 3

    def test_ci_cd_integration_dimension(self, extractor):
        """Test CI/CD Integration dimension."""
        cicd = extractor._gather_cicd_integration()
        assert "type" in cicd
        assert "status" in cicd
        assert isinstance(cicd["capabilities"], list)


class TestIntegration:
    """Integration tests for the extractor."""

    def test_full_capability_extraction(self, extractor, temp_home):
        """Test full capability extraction workflow."""
        # Set up a realistic environment
        project_path = temp_home / "my-project"
        project_path.mkdir()

        # Create AGENTS.md
        (project_path / "AGENTS.md").write_text("## Code Reviewer\n## CI Agent")

        # Create MCPs
        mcp_config = {"mcpServers": {"github": {"version": "1.0"}}}
        (temp_home / ".claude" / "mcp.json").write_text(json.dumps(mcp_config))

        # Create custom skill
        skill_dir = temp_home / ".claude" / "commands" / "custom-review"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Custom Review")

        # Extract capabilities
        evidence_list = extractor.extract_from_project(project_path)

        assert len(evidence_list) > 0
        dimensions = {e.dimension for e in evidence_list}

        # Should have evidence for multiple dimensions
        assert len(dimensions) > 1

    def test_plugins_included_in_extraction(self, extractor, temp_home):
        """Test that installed plugins are included in extraction."""
        # Create installed_plugins.json
        plugins_config = {
            "version": 2,
            "plugins": {
                "superpowers@claude-plugins-official": [
                    {
                        "scope": "project",
                        "version": "5.0.7",
                        "installedAt": "2026-03-23T18:55:35.055Z",
                    }
                ]
            },
        }

        plugins_file = temp_home / ".claude" / "plugins" / "installed_plugins.json"
        plugins_file.parent.mkdir(parents=True, exist_ok=True)
        plugins_file.write_text(json.dumps(plugins_config))

        plugins = extractor._scan_plugins()
        assert len(plugins) > 0
        assert any("superpowers" in p.get("name", "") for p in plugins)

    def test_settings_json_security_controls(self, extractor, temp_home):
        """Test detection of security controls from settings.json."""
        settings_config = {
            "permissions": {
                "allow": [
                    "Bash(ls)",
                    "Bash(git:*)",
                    "WebFetch(domain:github.com)",
                ]
            }
        }

        settings_file = temp_home / ".claude" / "settings.json"
        settings_file.write_text(json.dumps(settings_config))

        security = extractor._gather_security_compliance()
        # Should detect permission controls
        assert "status" in security
