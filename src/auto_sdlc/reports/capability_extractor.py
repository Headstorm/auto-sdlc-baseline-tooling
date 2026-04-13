"""
Capability Evidence Extractor

Scans a Claude Code project and installed capabilities (skills, agents, MCPs, plugins)
to assess adoption of AI tooling across different organizational dimensions.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class CapabilityEvidence:
    """
    Represents evidence of a capability deployed in the system.

    Attributes:
        dimension: The organizational dimension this capability maps to
        capability_type: Type of capability - "skill", "agent", "mcp", "plugin"
        capabilities: List of capability dictionaries with name, version, sophistication_level
        deployment_status: Current status - "installed", "configured", "active"
        sophistication: Overall sophistication level - "basic", "intermediate", "advanced"
    """

    dimension: str
    capability_type: str
    capabilities: List[Dict] = field(default_factory=list)
    deployment_status: str = "installed"
    sophistication: str = "basic"


class CapabilityEvidenceExtractor:
    """
    Extracts capability evidence from Claude Code configuration and project setup.

    Maps detected capabilities to the 12 organizational dimensions:
    - AI Tool Adoption
    - Prompt & Context Engineering
    - Agent Configuration
    - CI/CD Integration
    - Ticketing & Planning
    - Cross-System Connectivity
    - Quality Controls
    - Security & Compliance
    - Measurement & KPIs
    - Ways of Working
    - Accountability & Ownership
    - Scalability & Knowledge Transfer
    """

    def __init__(self, home_dir: Optional[Path] = None):
        """
        Initialize the extractor.

        Args:
            home_dir: Override home directory (default: Path.home())
        """
        self.home_dir = home_dir or Path.home()
        self.claude_dir = self.home_dir / ".claude"
        self.skills_cache: List[Dict] = []
        self.agents_cache: List[Dict] = []
        self.mcp_cache: List[Dict] = []
        self.plugins_cache: List[Dict] = []

    def extract_from_project(self, project_path: Path) -> List[CapabilityEvidence]:
        """
        Extract all capabilities from a project and installed system.

        Args:
            project_path: Path to the project directory

        Returns:
            List of CapabilityEvidence objects mapped to dimensions
        """
        project_path = Path(project_path)

        # Scan all capability sources
        self.skills_cache = self._scan_skills()
        self.agents_cache = self._scan_agents(project_path)
        self.mcp_cache = self._scan_mcp_integrations()
        self.plugins_cache = self._scan_plugins()

        # Map capabilities to dimensions
        evidence = self._map_to_dimensions()

        return evidence

    def _scan_skills(self) -> List[Dict]:
        """
        Scan for installed skills/slash commands in Claude Code.

        Looks for:
        - Built-in skills (execute-plan, brainstorm, etc.)
        - Custom skills in plugin directories
        - Check for /review, /commit, /plan, and other custom skills

        Returns:
            List of skill dictionaries with name, version, sophistication_level
        """
        skills = []

        # Scan superpowers plugin for built-in commands
        superpowers_dir = (
            self.claude_dir / "plugins" / "cache" / "claude-plugins-official" / "superpowers"
        )
        if superpowers_dir.exists():
            # Find latest version
            version_dirs = sorted([d for d in superpowers_dir.iterdir() if d.is_dir()])
            if version_dirs:
                latest_version = version_dirs[-1]
                commands_dir = latest_version / "commands"
                if commands_dir.exists():
                    for cmd_file in commands_dir.glob("*.md"):
                        skill_name = cmd_file.stem
                        skills.append(
                            {
                                "name": skill_name,
                                "version": latest_version.name,
                                "source": "superpowers-plugin",
                                "sophistication_level": self._assess_skill_sophistication(
                                    skill_name
                                ),
                            }
                        )

        # Scan little-loops plugin for ll: commands
        ll_commands_dir = self.claude_dir / "plugins" / "cache" / "little-loops" / "commands"
        if ll_commands_dir.exists():
            for cmd_file in ll_commands_dir.glob("*.md"):
                skill_name = f"ll:{cmd_file.stem}"
                skills.append(
                    {
                        "name": skill_name,
                        "version": "1.0",
                        "source": "little-loops-plugin",
                        "sophistication_level": self._assess_skill_sophistication(skill_name),
                    }
                )

        # Check for custom skills in ~/.claude/commands/
        custom_commands_dir = self.claude_dir / "commands"
        if custom_commands_dir.exists():
            for item in custom_commands_dir.rglob("SKILL.md"):
                skill_name = item.parent.name
                skills.append(
                    {
                        "name": skill_name,
                        "version": "custom",
                        "source": "custom",
                        "sophistication_level": self._assess_skill_sophistication(skill_name),
                    }
                )

        # Check for /review, /commit, /plan in settings
        settings_file = self.claude_dir / "settings.json"
        if settings_file.exists():
            try:
                settings = json.loads(settings_file.read_text())
                # Note: skills aren't directly in settings, but we mark them as detected
                # if the user has configured the system to support them
                for skill_name in ["review", "commit", "plan"]:
                    # These are commonly available skills
                    pass
            except (json.JSONDecodeError, KeyError):
                pass

        return skills

    def _scan_agents(self, project_path: Path) -> List[Dict]:
        """
        Scan for defined agents in AGENTS.md and ~/.claude/agents/ directory.

        Args:
            project_path: Path to the project directory

        Returns:
            List of agent dictionaries with name, version, sophistication_level
        """
        agents = []

        # Check for AGENTS.md in project root
        agents_md = project_path / "AGENTS.md"
        if agents_md.exists():
            try:
                content = agents_md.read_text()
                # Simple parsing: look for agent definitions (## Agent Name pattern)
                lines = content.split("\n")
                for line in lines:
                    if line.startswith("## ") or line.startswith("### "):
                        agent_name = line.lstrip("#").strip()
                        if agent_name and not agent_name.startswith("Agent"):
                            agents.append(
                                {
                                    "name": agent_name,
                                    "version": "1.0",
                                    "source": "AGENTS.md",
                                    "sophistication_level": "intermediate",
                                }
                            )
            except Exception:
                pass

        # Check ~/.claude/agents/ directory
        agents_dir = self.claude_dir / "agents"
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.json"):
                agent_name = agent_file.stem
                try:
                    agent_data = json.loads(agent_file.read_text())
                    agents.append(
                        {
                            "name": agent_name,
                            "version": agent_data.get("version", "1.0"),
                            "source": "agents-directory",
                            "sophistication_level": self._assess_agent_sophistication(
                                agent_data
                            ),
                        }
                    )
                except Exception:
                    pass

        return agents

    def _scan_mcp_integrations(self) -> List[Dict]:
        """
        Scan for installed MCP servers from mcp.json or plugin .mcp.json files.

        Looks for:
        - ~/.claude/mcp.json (if it exists)
        - .mcp.json files in plugin directories
        - Configured MCP servers in settings

        Returns:
            List of MCP integration dictionaries with name, version, sophistication_level
        """
        mcp_integrations = []

        # Check for ~/.claude/mcp.json
        mcp_config = self.claude_dir / "mcp.json"
        if mcp_config.exists():
            try:
                mcp_data = json.loads(mcp_config.read_text())
                servers = mcp_data.get("mcpServers", {})
                for server_name, server_config in servers.items():
                    mcp_integrations.append(
                        {
                            "name": server_name,
                            "version": server_config.get("version", "1.0"),
                            "type": server_config.get("type", "unknown"),
                            "source": "mcp.json",
                            "sophistication_level": "intermediate",
                        }
                    )
            except Exception:
                pass

        # Scan plugin directories for .mcp.json files
        plugins_dir = self.claude_dir / "plugins"
        if plugins_dir.exists():
            for mcp_file in plugins_dir.rglob(".mcp.json"):
                try:
                    mcp_data = json.loads(mcp_file.read_text())
                    # Extract server names from .mcp.json
                    if isinstance(mcp_data, dict):
                        server_name = mcp_data.get("name") or mcp_file.parent.name
                        mcp_integrations.append(
                            {
                                "name": server_name,
                                "version": mcp_data.get("version", "1.0"),
                                "type": mcp_data.get("type", "unknown"),
                                "source": "plugin",
                                "sophistication_level": self._assess_mcp_sophistication(
                                    mcp_data
                                ),
                            }
                        )
                except Exception:
                    pass

        # Deduplicate by name
        seen = set()
        unique_mcps = []
        for mcp in mcp_integrations:
            if mcp["name"] not in seen:
                seen.add(mcp["name"])
                unique_mcps.append(mcp)

        return unique_mcps

    def _scan_plugins(self) -> List[Dict]:
        """
        Scan for installed plugins in ~/.claude/plugins/installed_plugins.json.

        Returns:
            List of plugin dictionaries with name, version, sophistication_level
        """
        plugins = []

        installed_plugins_file = self.claude_dir / "plugins" / "installed_plugins.json"
        if installed_plugins_file.exists():
            try:
                plugins_data = json.loads(installed_plugins_file.read_text())
                installed = plugins_data.get("plugins", {})

                for plugin_id, plugin_versions in installed.items():
                    if isinstance(plugin_versions, list):
                        for plugin_info in plugin_versions:
                            version = plugin_info.get("version", "1.0")
                            plugins.append(
                                {
                                    "name": plugin_id,
                                    "version": version,
                                    "scope": plugin_info.get("scope", "project"),
                                    "source": "installed-plugins",
                                    "sophistication_level": self._assess_plugin_sophistication(
                                        plugin_id
                                    ),
                                }
                            )
            except Exception:
                pass

        return plugins

    def _assess_skill_sophistication(self, skill_name: str) -> str:
        """
        Assess sophistication of a skill based on its capabilities.

        Args:
            skill_name: Name of the skill

        Returns:
            "basic", "intermediate", or "advanced"
        """
        # Multi-step workflow skills are intermediate/advanced
        advanced_skills = {
            "execute-plan",
            "systematic-debugging",
            "subagent-driven-development",
            "dispatching-parallel-agents",
        }
        intermediate_skills = {
            "write-plan",
            "brainstorm",
            "verification-before-completion",
            "receiving-code-review",
            "requesting-code-review",
        }

        if skill_name in advanced_skills:
            return "advanced"
        elif skill_name in intermediate_skills:
            return "intermediate"
        else:
            return "basic"

    def _assess_agent_sophistication(self, agent_data: Dict) -> str:
        """
        Assess sophistication of an agent based on its configuration.

        Args:
            agent_data: Agent configuration dictionary

        Returns:
            "basic", "intermediate", or "advanced"
        """
        # Check for multi-step workflows, tool count, etc.
        tools = agent_data.get("tools", [])
        workflows = agent_data.get("workflows", [])

        # Advanced: many tools + workflows
        if len(tools) > 5 and len(workflows) > 0:
            return "advanced"
        # Intermediate: moderate tool count or workflow present
        elif len(tools) > 2 or len(workflows) > 0:
            return "intermediate"
        else:
            return "basic"

    def _assess_mcp_sophistication(self, mcp_data: Dict) -> str:
        """
        Assess sophistication of an MCP integration based on its configuration.

        Args:
            mcp_data: MCP configuration dictionary

        Returns:
            "basic", "intermediate", or "advanced"
        """
        # Advanced MCPs: multi-system integrations (JIRA + Slack + Confluence)
        mcp_name = mcp_data.get("name", "").lower()

        complex_systems = ["jira", "slack", "confluence", "github", "gitlab", "linear"]
        matching_systems = sum(1 for sys in complex_systems if sys in mcp_name)

        if matching_systems >= 2:
            return "advanced"
        elif "server" in mcp_name or len(mcp_data.get("capabilities", [])) > 3:
            return "intermediate"
        else:
            return "basic"

    def _assess_plugin_sophistication(self, plugin_id: str) -> str:
        """
        Assess sophistication of a plugin based on its purpose.

        Args:
            plugin_id: Plugin identifier

        Returns:
            "basic", "intermediate", or "advanced"
        """
        advanced_plugins = {"superpowers", "little-loops"}
        intermediate_plugins = {"feature-dev", "code-review"}

        plugin_base = plugin_id.split("@")[0] if "@" in plugin_id else plugin_id

        if plugin_base in advanced_plugins:
            return "advanced"
        elif plugin_base in intermediate_plugins:
            return "intermediate"
        else:
            return "basic"

    def _map_to_dimensions(self) -> List[CapabilityEvidence]:
        """
        Map detected capabilities to organizational dimensions.

        Returns:
            List of CapabilityEvidence objects, one per dimension
        """
        evidence_map = {
            "AI Tool Adoption": self._gather_tool_adoption(),
            "Prompt & Context Engineering": self._gather_prompt_engineering(),
            "Agent Configuration": self._gather_agent_configuration(),
            "CI/CD Integration": self._gather_cicd_integration(),
            "Ticketing & Planning": self._gather_ticketing_planning(),
            "Cross-System Connectivity": self._gather_cross_system(),
            "Quality Controls": self._gather_quality_controls(),
            "Security & Compliance": self._gather_security_compliance(),
            "Measurement & KPIs": self._gather_measurement_kpis(),
            "Ways of Working": self._gather_ways_of_working(),
            "Accountability & Ownership": self._gather_accountability(),
            "Scalability & Knowledge Transfer": self._gather_scalability(),
        }

        evidence_list = []
        for dimension, evidence_data in evidence_map.items():
            if evidence_data["capabilities"]:
                evidence_list.append(
                    CapabilityEvidence(
                        dimension=dimension,
                        capability_type=evidence_data.get("type", "mixed"),
                        capabilities=evidence_data["capabilities"],
                        deployment_status=evidence_data.get("status", "installed"),
                        sophistication=evidence_data.get("sophistication", "basic"),
                    )
                )

        return evidence_list

    def _gather_tool_adoption(self) -> Dict:
        """Gather evidence for AI Tool Adoption dimension."""
        capabilities = []
        max_sophistication = "basic"

        # Count different plugin versions
        if self.plugins_cache:
            capabilities.append(
                {"category": "plugins", "count": len(self.plugins_cache), "items": self.plugins_cache}
            )
            max_sophistication = max(
                max_sophistication,
                max((p.get("sophistication_level", "basic") for p in self.plugins_cache), default="basic"),
                key=lambda x: ["basic", "intermediate", "advanced"].index(x),
            )

        # Count skills
        if self.skills_cache:
            capabilities.append(
                {"category": "skills", "count": len(self.skills_cache), "items": self.skills_cache}
            )
            max_sophistication = max(
                max_sophistication,
                max((s.get("sophistication_level", "basic") for s in self.skills_cache), default="basic"),
                key=lambda x: ["basic", "intermediate", "advanced"].index(x),
            )

        return {
            "type": "plugin",
            "capabilities": capabilities,
            "status": "installed" if capabilities else "not_detected",
            "sophistication": max_sophistication,
        }

    def _gather_prompt_engineering(self) -> Dict:
        """Gather evidence for Prompt & Context Engineering dimension."""
        capabilities = []

        # Look for custom context loaders or prompt enhancement tools
        for skill in self.skills_cache:
            if any(x in skill["name"].lower() for x in ["context", "prompt", "engineering"]):
                capabilities.append(skill)

        for plugin in self.plugins_cache:
            if "little-loops" in plugin.get("name", "").lower():
                capabilities.append({"type": "plugin", "name": plugin["name"], "purpose": "context-engineering"})

        return {
            "type": "skill",
            "capabilities": capabilities,
            "status": "installed" if capabilities else "not_detected",
            "sophistication": "intermediate" if capabilities else "basic",
        }

    def _gather_agent_configuration(self) -> Dict:
        """Gather evidence for Agent Configuration dimension."""
        capabilities = []
        max_sophistication = "basic"

        if self.agents_cache:
            capabilities = self.agents_cache
            max_sophistication = max(
                (a.get("sophistication_level", "basic") for a in self.agents_cache),
                default="basic",
                key=lambda x: ["basic", "intermediate", "advanced"].index(x),
            )

        return {
            "type": "agent",
            "capabilities": capabilities,
            "status": "configured" if capabilities else "not_detected",
            "sophistication": max_sophistication,
        }

    def _gather_cicd_integration(self) -> Dict:
        """Gather evidence for CI/CD Integration dimension."""
        capabilities = []

        # Check for /review skill
        for skill in self.skills_cache:
            if "review" in skill["name"].lower():
                capabilities.append(skill)

        # Check for CI/CD MCPs (GitHub, GitLab, etc.)
        for mcp in self.mcp_cache:
            if any(x in mcp["name"].lower() for x in ["github", "gitlab", "jenkins", "circle"]):
                capabilities.append(mcp)

        return {
            "type": "skill",
            "capabilities": capabilities,
            "status": "active" if capabilities else "not_detected",
            "sophistication": "intermediate" if capabilities else "basic",
        }

    def _gather_ticketing_planning(self) -> Dict:
        """Gather evidence for Ticketing & Planning dimension."""
        capabilities = []

        # Check for /plan skill
        for skill in self.skills_cache:
            if "plan" in skill["name"].lower():
                capabilities.append(skill)

        # Check for ticketing MCPs
        for mcp in self.mcp_cache:
            if any(x in mcp["name"].lower() for x in ["jira", "linear", "github"]):
                capabilities.append(mcp)

        return {
            "type": "mcp",
            "capabilities": capabilities,
            "status": "configured" if capabilities else "not_detected",
            "sophistication": "intermediate" if capabilities else "basic",
        }

    def _gather_cross_system(self) -> Dict:
        """Gather evidence for Cross-System Connectivity dimension."""
        capabilities = []
        count = 0

        # Count active MCP integrations
        system_types = set()
        for mcp in self.mcp_cache:
            name_lower = mcp["name"].lower()
            if any(x in name_lower for x in ["jira", "slack", "confluence", "github", "gitlab", "linear"]):
                capabilities.append(mcp)
                system_types.add(name_lower)
                count += 1

        sophistication = "basic"
        if count >= 3:
            sophistication = "advanced"
        elif count >= 1:
            sophistication = "intermediate"

        return {
            "type": "mcp",
            "capabilities": capabilities,
            "status": "active" if capabilities else "not_detected",
            "sophistication": sophistication,
        }

    def _gather_quality_controls(self) -> Dict:
        """Gather evidence for Quality Controls dimension."""
        capabilities = []

        # Check for /review skill
        for skill in self.skills_cache:
            if "review" in skill["name"].lower():
                capabilities.append(skill)

        # Check for test generation or quality-related MCPs
        for mcp in self.mcp_cache:
            if any(x in mcp["name"].lower() for x in ["test", "quality", "sonar", "github"]):
                capabilities.append(mcp)

        return {
            "type": "skill",
            "capabilities": capabilities,
            "status": "active" if capabilities else "not_detected",
            "sophistication": "intermediate" if capabilities else "basic",
        }

    def _gather_security_compliance(self) -> Dict:
        """Gather evidence for Security & Compliance dimension."""
        capabilities = []

        # Check for audit logging or security-related MCPs
        for mcp in self.mcp_cache:
            if any(x in mcp["name"].lower() for x in ["audit", "security", "compliance", "vault"]):
                capabilities.append(mcp)

        # Check for settings that indicate security awareness
        settings_file = self.claude_dir / "settings.json"
        if settings_file.exists():
            try:
                settings = json.loads(settings_file.read_text())
                if settings.get("permissions"):
                    capabilities.append(
                        {
                            "name": "permission-controls",
                            "version": "1.0",
                            "type": "setting",
                            "source": "settings",
                        }
                    )
            except Exception:
                pass

        return {
            "type": "mcp",
            "capabilities": capabilities,
            "status": "configured" if capabilities else "not_detected",
            "sophistication": "intermediate" if capabilities else "basic",
        }

    def _gather_measurement_kpis(self) -> Dict:
        """Gather evidence for Measurement & KPIs dimension."""
        capabilities = []

        # Check for analytics or observability MCPs
        for mcp in self.mcp_cache:
            if any(x in mcp["name"].lower() for x in ["analytics", "observability", "datadog", "newrelic"]):
                capabilities.append(mcp)

        return {
            "type": "mcp",
            "capabilities": capabilities,
            "status": "configured" if capabilities else "not_detected",
            "sophistication": "intermediate" if capabilities else "basic",
        }

    def _gather_ways_of_working(self) -> Dict:
        """Gather evidence for Ways of Working dimension."""
        capabilities = []

        # Check for workflow or template tools
        for skill in self.skills_cache:
            if any(x in skill["name"].lower() for x in ["workflow", "template", "process"]):
                capabilities.append(skill)

        for plugin in self.plugins_cache:
            if "little-loops" in plugin.get("name", "").lower():
                capabilities.append(
                    {
                        "type": "plugin",
                        "name": plugin["name"],
                        "purpose": "workflow-standardization",
                    }
                )

        return {
            "type": "skill",
            "capabilities": capabilities,
            "status": "configured" if capabilities else "not_detected",
            "sophistication": "intermediate" if capabilities else "basic",
        }

    def _gather_accountability(self) -> Dict:
        """Gather evidence for Accountability & Ownership dimension."""
        capabilities = []

        # Check for audit/logging integrations
        for mcp in self.mcp_cache:
            if any(x in mcp["name"].lower() for x in ["audit", "logging", "slack"]):
                capabilities.append(mcp)

        return {
            "type": "mcp",
            "capabilities": capabilities,
            "status": "configured" if capabilities else "not_detected",
            "sophistication": "intermediate" if capabilities else "basic",
        }

    def _gather_scalability(self) -> Dict:
        """Gather evidence for Scalability & Knowledge Transfer dimension."""
        capabilities = []

        # Check for documentation generators or knowledge base integrations
        for mcp in self.mcp_cache:
            if any(x in mcp["name"].lower() for x in ["confluence", "docs", "wiki", "notion"]):
                capabilities.append(mcp)

        for skill in self.skills_cache:
            if any(x in skill["name"].lower() for x in ["document", "knowledge", "wiki"]):
                capabilities.append(skill)

        return {
            "type": "mcp",
            "capabilities": capabilities,
            "status": "configured" if capabilities else "not_detected",
            "sophistication": "intermediate" if capabilities else "basic",
        }
