"""
Report Data Models

Defines the complete structure of Team AI Maturity Reports and Individual Developer Profiles.

Covers all 12 dimensions of the AI Maturity Scorecard:
1. AI Tool Adoption
2. Prompt & Context Engineering
3. Agent Configuration
4. CI/CD Integration
5. Ticketing & Planning
6. Cross-System Connectivity
7. Quality Controls
8. Security & Compliance
9. Measurement & KPIs
10. Ways of Working
11. Accountability & Ownership
12. Scalability & Knowledge Transfer
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


# Constants
ALL_DIMENSIONS = {
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
}

CONFIDENCE_LEVELS = {"high", "medium", "low"}
MATURITY_LEVELS = {1, 2, 3, 4}


@dataclass
class DimensionReport:
    """
    Assessment report for a single dimension of AI maturity.

    Attributes:
        dimension: Dimension name (one of 12)
        maturity_level: Current maturity level (1-4)
        confidence: Confidence in assessment ("high", "medium", or "low")
        current_state: Narrative describing current capability
        evidence_summary: Summary evidence from logs, configs, capabilities
        gaps: Specific gaps identified
        strengths: What's working well
        roadmap: Next steps to reach next level (list of dicts with step details)
    """

    dimension: str
    maturity_level: int
    confidence: str
    current_state: str
    evidence_summary: Dict[str, str] = field(default_factory=dict)
    gaps: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    roadmap: List[Dict] = field(default_factory=list)

    def __post_init__(self):
        """Validate DimensionReport after initialization."""
        self._validate()

    def _validate(self):
        """Validate field values."""
        if self.dimension not in ALL_DIMENSIONS:
            raise ValueError(
                f"Invalid dimension '{self.dimension}'. Must be one of: {sorted(ALL_DIMENSIONS)}"
            )

        if self.maturity_level not in MATURITY_LEVELS:
            raise ValueError(
                f"Maturity level must be 1-4, got {self.maturity_level}"
            )

        if self.confidence not in CONFIDENCE_LEVELS:
            raise ValueError(
                f"Confidence must be one of {CONFIDENCE_LEVELS}, got '{self.confidence}'"
            )

        if not isinstance(self.current_state, str) or not self.current_state.strip():
            raise ValueError("current_state must be a non-empty string")

        if not isinstance(self.evidence_summary, dict):
            raise ValueError("evidence_summary must be a dict")

        if not isinstance(self.gaps, list):
            raise ValueError("gaps must be a list")

        if not isinstance(self.strengths, list):
            raise ValueError("strengths must be a list")

        if not isinstance(self.roadmap, list):
            raise ValueError("roadmap must be a list")


@dataclass
class TeamReport:
    """
    AI Maturity Report for an entire team or company.

    Attributes:
        team_name: Team or company name
        report_date: ISO date string (YYYY-MM-DD)
        data_sources: Which data sources available (logs, configs, capabilities)
        team_size: Number of developers assessed
        assessment_period_weeks: How many weeks of logs were analyzed
        overall_maturity_level: Average maturity across all 12 dimensions (1.0-4.0)
        dimensions: Dict mapping dimension names to DimensionReport objects (must contain all 12)
        executive_summary: 1-2 paragraph overview
        key_insights: Top 3-5 key findings
        recommendations: Strategic recommendations for the team
        confidence_by_dimension: Confidence level for each dimension
        next_steps: Immediate actions to take
    """

    team_name: str
    report_date: str
    data_sources: Dict[str, bool] = field(default_factory=dict)
    team_size: int = 1
    assessment_period_weeks: int = 0
    overall_maturity_level: float = 1.0
    dimensions: Dict[str, "DimensionReport"] = field(default_factory=dict)
    executive_summary: str = ""
    key_insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence_by_dimension: Dict[str, str] = field(default_factory=dict)
    next_steps: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate TeamReport after initialization."""
        self._validate()

    def _validate(self):
        """Validate field values."""
        if not isinstance(self.team_name, str) or not self.team_name.strip():
            raise ValueError("team_name must be a non-empty string")

        # Validate report_date is ISO format
        try:
            datetime.strptime(self.report_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"report_date must be ISO format (YYYY-MM-DD), got '{self.report_date}'"
            )

        if not isinstance(self.data_sources, dict):
            raise ValueError("data_sources must be a dict")

        if self.team_size < 1:
            raise ValueError("team_size must be at least 1")

        if self.assessment_period_weeks < 0:
            raise ValueError("assessment_period_weeks must be >= 0")

        if not (1.0 <= self.overall_maturity_level <= 4.0):
            raise ValueError(
                f"overall_maturity_level must be between 1.0 and 4.0, got {self.overall_maturity_level}"
            )

        # Validate all 12 dimensions are present
        missing_dimensions = ALL_DIMENSIONS - set(self.dimensions.keys())
        if missing_dimensions:
            raise ValueError(
                f"Missing dimensions: {sorted(missing_dimensions)}. All 12 dimensions required."
            )

        # Validate each dimension report
        for dim_name, dim_report in self.dimensions.items():
            if not isinstance(dim_report, DimensionReport):
                raise ValueError(
                    f"dimensions['{dim_name}'] must be a DimensionReport instance"
                )
            if dim_report.dimension != dim_name:
                raise ValueError(
                    f"Dimension mismatch: key '{dim_name}' but report.dimension = '{dim_report.dimension}'"
                )

        if not isinstance(self.executive_summary, str) or not self.executive_summary.strip():
            raise ValueError("executive_summary must be a non-empty string")

        if not isinstance(self.key_insights, list):
            raise ValueError("key_insights must be a list")

        if not isinstance(self.recommendations, list):
            raise ValueError("recommendations must be a list")

        if not isinstance(self.confidence_by_dimension, dict):
            raise ValueError("confidence_by_dimension must be a dict")

        # Validate confidence_by_dimension has all dimensions
        missing_conf = ALL_DIMENSIONS - set(self.confidence_by_dimension.keys())
        if missing_conf:
            raise ValueError(
                f"confidence_by_dimension missing: {sorted(missing_conf)}"
            )

        if not isinstance(self.next_steps, list):
            raise ValueError("next_steps must be a list")


@dataclass
class IndividualReport:
    """
    AI Maturity Report for an individual developer.

    Attributes:
        developer_id: Anonymized or actual developer identifier
        report_date: ISO date string (YYYY-MM-DD)
        assessment_period_weeks: How many weeks of data were analyzed
        overall_maturity_level: Developer's personal average maturity (1.0-4.0)
        dimensions: Dict mapping dimension names to DimensionReport objects (must contain all 12)
        executive_summary: Developer-focused narrative
        usage_patterns: Dictionary of usage metrics (sessions/day, messages/session, etc.)
        strengths: Developer's particular strengths
        growth_areas: Where the developer should focus development
        fit_with_team_baseline: How developer compares to team average (e.g., "Above team average")
        learning_path: Specific skills to develop
        key_insights: Key findings about this developer
        recommendations: Personalized recommendations
    """

    developer_id: str
    report_date: str
    assessment_period_weeks: int = 0
    overall_maturity_level: float = 1.0
    dimensions: Dict[str, "DimensionReport"] = field(default_factory=dict)
    executive_summary: str = ""
    usage_patterns: Dict[str, float] = field(default_factory=dict)
    strengths: List[str] = field(default_factory=list)
    growth_areas: List[str] = field(default_factory=list)
    fit_with_team_baseline: str = ""
    learning_path: List[str] = field(default_factory=list)
    key_insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate IndividualReport after initialization."""
        self._validate()

    def _validate(self):
        """Validate field values."""
        if not isinstance(self.developer_id, str) or not self.developer_id.strip():
            raise ValueError("developer_id must be a non-empty string")

        # Validate report_date is ISO format
        try:
            datetime.strptime(self.report_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"report_date must be ISO format (YYYY-MM-DD), got '{self.report_date}'"
            )

        if self.assessment_period_weeks < 0:
            raise ValueError("assessment_period_weeks must be >= 0")

        if not (1.0 <= self.overall_maturity_level <= 4.0):
            raise ValueError(
                f"overall_maturity_level must be between 1.0 and 4.0, got {self.overall_maturity_level}"
            )

        # Validate all 12 dimensions are present
        missing_dimensions = ALL_DIMENSIONS - set(self.dimensions.keys())
        if missing_dimensions:
            raise ValueError(
                f"Missing dimensions: {sorted(missing_dimensions)}. All 12 dimensions required."
            )

        # Validate each dimension report
        for dim_name, dim_report in self.dimensions.items():
            if not isinstance(dim_report, DimensionReport):
                raise ValueError(
                    f"dimensions['{dim_name}'] must be a DimensionReport instance"
                )
            if dim_report.dimension != dim_name:
                raise ValueError(
                    f"Dimension mismatch: key '{dim_name}' but report.dimension = '{dim_report.dimension}'"
                )

        if not isinstance(self.executive_summary, str) or not self.executive_summary.strip():
            raise ValueError("executive_summary must be a non-empty string")

        if not isinstance(self.usage_patterns, dict):
            raise ValueError("usage_patterns must be a dict")

        if not isinstance(self.strengths, list):
            raise ValueError("strengths must be a list")

        if not isinstance(self.growth_areas, list):
            raise ValueError("growth_areas must be a list")

        if not isinstance(self.fit_with_team_baseline, str) or not self.fit_with_team_baseline.strip():
            raise ValueError("fit_with_team_baseline must be a non-empty string")

        if not isinstance(self.learning_path, list):
            raise ValueError("learning_path must be a list")

        if not isinstance(self.key_insights, list):
            raise ValueError("key_insights must be a list")

        if not isinstance(self.recommendations, list):
            raise ValueError("recommendations must be a list")
