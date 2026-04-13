"""
Config Evidence Extractor for AI Maturity Assessment.

Parses project configuration files (CLAUDE.md, AGENTS.md, .rules, settings.json)
to extract signals for each maturity dimension.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# Mapping of file patterns to dimension signals
DIMENSION_KEYWORDS = {
    "AI Tool Adoption": [
        r"tool.*standard",
        r"standardized.*tool",
        r"tool.*approval",
        r"approved.*tool",
        r"claude.*model",
        r"tool.*policy",
    ],
    "Prompt & Context Engineering": [
        r"prompt.*template",
        r"template.*prompt",
        r"context.*load",
        r"context.*guide",
        r"file.*reference",
        r"context.*architecture",
        r"prompt.*pattern",
    ],
    "Agent Configuration": [
        r"agent.*defin",
        r"custom.*agent",
        r"skill.*config",
        r"tool.*custom",
        r"agent.*integrat",
    ],
    "CI/CD Integration": [
        r"ci/cd",
        r"review.*policy",
        r"test.*generat",
        r"deploy.*policy",
        r"pipeline",
        r"github.*action",
        r"automated.*test",
    ],
    "Ticketing & Planning": [
        r"issue.*struct",
        r"ticket.*format",
        r"planning.*protocol",
        r"epic.*standard",
        r"jira",
        r"issue.*template",
    ],
    "Cross-System Connectivity": [
        r"mcp.*integrat",
        r"connector",
        r"slack.*integrat",
        r"github.*integrat",
        r"jira.*integrat",
        r"api.*gateway",
        r"integration.*list",
    ],
    "Quality Controls": [
        r"code.*review",
        r"quality.*check",
        r"test.*standard",
        r"lint.*rule",
        r"quality.*gate",
        r"review.*checklist",
        r"quality.*bar",
    ],
    "Security & Compliance": [
        r"security",
        r"compliance",
        r"pii.*policy",
        r"data.*handling",
        r"audit.*trail",
        r"pii.*detect",
        r"encryption",
        r"access.*control",
    ],
    "Measurement & KPIs": [
        r"metric",
        r"kpi",
        r"dashboard",
        r"measurement",
        r"tracking",
        r"adoption.*rate",
    ],
    "Ways of Working": [
        r"session.*protocol",
        r"workflow.*document",
        r"working.*agreement",
        r"daily.*ritual",
        r"standup",
        r"retro",
        r"ceremony",
    ],
    "Accountability & Ownership": [
        r"champion",
        r"owner.*ai",
        r"responsibility",
        r"accountability",
        r"leadership",
        r"sponsor",
    ],
    "Scalability & Knowledge Transfer": [
        r"onboarding",
        r"knowledge.*transfer",
        r"playbook",
        r"runbook",
        r"training.*material",
        r"ramp.*time",
        r"prompt.*library",
    ],
}


@dataclass
class ConfigEvidence:
    """Evidence extracted from project configuration files."""

    dimension: str
    files_present: Dict[str, bool] = field(default_factory=dict)
    signals: Dict[str, str] = field(default_factory=dict)
    freshness: Dict[str, datetime] = field(default_factory=dict)
    quality_indicators: Dict[str, str] = field(default_factory=dict)


class ConfigEvidenceExtractor:
    """Extracts evidence signals from project configuration files."""

    def __init__(self, project_path: Path):
        """Initialize extractor with project path."""
        self.project_path = Path(project_path)

    def extract_from_project(self) -> List[ConfigEvidence]:
        """
        Analyze project configs and extract evidence for all dimensions.

        Returns:
            List of ConfigEvidence objects, one per dimension.
        """
        config_contents = {
            "CLAUDE.md": self._parse_claude_md(),
            "AGENTS.md": self._parse_agents_md(),
            ".rules": self._parse_rules(),
            "settings.json": self._parse_settings_json(),
        }

        track_freshness = {}
        for filename in ["CLAUDE.md", "AGENTS.md", ".rules", "settings.json"]:
            fpath = self.project_path / filename
            if fpath.exists():
                track_freshness[filename] = datetime.fromtimestamp(
                    fpath.stat().st_mtime
                )

        # Build evidence per dimension
        evidence_list = []
        for dimension in DIMENSION_KEYWORDS.keys():
            evidence = self._extract_dimension_evidence(
                dimension, config_contents, track_freshness
            )
            evidence_list.append(evidence)

        return evidence_list

    def _extract_dimension_evidence(
        self, dimension: str, config_contents: Dict, track_freshness: Dict
    ) -> ConfigEvidence:
        """Extract evidence for a specific dimension."""
        evidence = ConfigEvidence(dimension=dimension)

        # Track which files are present
        evidence.files_present = {
            "CLAUDE.md": (self.project_path / "CLAUDE.md").exists(),
            "AGENTS.md": (self.project_path / "AGENTS.md").exists(),
            ".rules": (self.project_path / ".rules").exists(),
            "settings.json": (self.project_path / "settings.json").exists(),
        }

        # Track freshness
        evidence.freshness = track_freshness.copy()

        # Extract signals for this dimension
        keywords = DIMENSION_KEYWORDS[dimension]
        signals = {}

        for filename, content in config_contents.items():
            if content:
                matches = self._extract_signals_from_content(content, keywords)
                if matches:
                    signals[filename] = matches

        evidence.signals = signals

        # Assess quality
        evidence.quality_indicators = self._assess_quality(
            signals, dimension, evidence.files_present
        )

        return evidence

    def _extract_signals_from_content(self, content: str, keywords: List[str]) -> str:
        """
        Extract relevant content snippets based on keywords.

        Returns:
            Concatenated snippets of matching content.
        """
        if not content:
            return ""

        lines = content.split("\n")
        matching_snippets = []

        for i, line in enumerate(lines):
            line_lower = line.lower()
            for keyword_pattern in keywords:
                if re.search(keyword_pattern, line_lower):
                    # Capture this line and some context
                    start = max(0, i - 1)
                    end = min(len(lines), i + 3)
                    snippet = "\n".join(lines[start:end])
                    if snippet not in matching_snippets:
                        matching_snippets.append(snippet)
                    break

        return " | ".join(matching_snippets)

    def _assess_quality(
        self, signals: Dict[str, str], dimension: str, files_present: Dict[str, bool]
    ) -> Dict[str, str]:
        """
        Assess quality of evidence for a dimension.

        Returns:
            Dict mapping file names to quality indicators:
            - "documented": Signal found and detailed
            - "partial": Signal found but minimal
            - "missing": No signal found
            - "outdated": File exists but no recent signal
        """
        quality = {}

        for filename, is_present in files_present.items():
            if filename not in signals:
                quality[filename] = "missing" if is_present else "not_present"
            else:
                signal_text = signals[filename]
                if len(signal_text) > 100:
                    quality[filename] = "documented"
                elif len(signal_text) > 20:
                    quality[filename] = "partial"
                else:
                    quality[filename] = "missing"

        return quality

    def _parse_claude_md(self) -> Optional[str]:
        """Extract content from CLAUDE.md."""
        path = self.project_path / "CLAUDE.md"
        if path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except Exception:
                return None
        return None

    def _parse_agents_md(self) -> Optional[str]:
        """Extract content from AGENTS.md."""
        path = self.project_path / "AGENTS.md"
        if path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except Exception:
                return None
        return None

    def _parse_rules(self) -> Optional[str]:
        """Extract content from .rules file."""
        path = self.project_path / ".rules"
        if path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except Exception:
                return None
        return None

    def _parse_settings_json(self) -> Optional[str]:
        """Extract content from settings.json."""
        path = self.project_path / "settings.json"
        if path.exists():
            try:
                content = path.read_text(encoding="utf-8")
                # Return formatted JSON for easier signal extraction
                data = json.loads(content)
                return json.dumps(data, indent=2)
            except Exception:
                return None
        return None
