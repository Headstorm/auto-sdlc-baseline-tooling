"""Maturity scoring system for auto-sdlc."""
from typing import Any, Dict, List, Optional


_LEVEL_LABELS = ["Beginner", "Basic", "Intermediate", "Advanced", "Expert"]

_RUBRIC = {
    "prompting_sophistication": {
        "label": "Prompting Sophistication",
        "thresholds": [0, 15, 30, 50, 70],
    },
    "tooling_adoption": {
        "label": "Tooling Adoption",
        "thresholds": [0, 0.05, 0.15, 0.30, 0.50],
    },
    "usage_frequency": {
        "label": "Usage Frequency",
        "thresholds": [0, 0.1, 0.25, 0.4, 0.6],
    },
    "session_depth": {
        "label": "Session Depth",
        "thresholds": [0, 5, 12, 20, 30],
    },
    "context_efficiency": {
        "label": "Context Efficiency",
        "thresholds": [0, 0.3, 0.6, 0.8, 0.95],
    },
}


def score_dimension(dimension_key: str, value: float) -> int:
    """Score a dimension value against its thresholds.

    Args:
        dimension_key: The dimension key (e.g., 'prompting_sophistication')
        value: The metric value to score

    Returns:
        An integer level from 0-4
    """
    if dimension_key not in _RUBRIC:
        raise ValueError(f"Unknown dimension: {dimension_key}")

    thresholds = _RUBRIC[dimension_key]["thresholds"]

    # Score based on which threshold the value meets or exceeds
    for level in range(4, -1, -1):
        if value >= thresholds[level]:
            return level

    return 0


def build_maturity_report(
    behavioral: Dict[str, float],
    avg_prompt_quality: float,
    token_usage_agg: Dict[str, float],
) -> Dict[str, Any]:
    """Build a comprehensive maturity report.

    Args:
        behavioral: Dict with keys:
            - skill_invocation_ratio: float
            - sessions_per_day: float
            - avg_messages_per_session: float
        avg_prompt_quality: Average prompt quality score (0-100)
        token_usage_agg: Dict with keys:
            - total_tokens: float
            - total_cache_read_tokens: float

    Returns:
        Dict with keys:
            - overall_level: int (0-4)
            - overall_label: str
            - dimensions: Dict[str, Dict] with per-dimension scores
    """
    # Extract behavioral metrics
    skill_invocation_ratio = behavioral.get("skill_invocation_ratio", 0)
    sessions_per_day = behavioral.get("sessions_per_day", 0)
    avg_messages_per_session = behavioral.get("avg_messages_per_session", 0)

    # Calculate context efficiency (cache hit ratio)
    total_tokens = token_usage_agg.get("total_tokens", 0)
    cache_read_tokens = token_usage_agg.get("total_cache_read_tokens", 0)

    if total_tokens > 0:
        context_efficiency = cache_read_tokens / total_tokens
    else:
        context_efficiency = 0

    # Score each dimension
    dimensions = {}

    # prompting_sophistication: based on prompt quality
    prom_score = score_dimension("prompting_sophistication", avg_prompt_quality)
    dimensions["prompting_sophistication"] = {
        "label": _RUBRIC["prompting_sophistication"]["label"],
        "level": prom_score,
        "level_label": _LEVEL_LABELS[prom_score],
    }

    # tooling_adoption: based on skill invocation ratio
    tool_score = score_dimension("tooling_adoption", skill_invocation_ratio)
    dimensions["tooling_adoption"] = {
        "label": _RUBRIC["tooling_adoption"]["label"],
        "level": tool_score,
        "level_label": _LEVEL_LABELS[tool_score],
    }

    # usage_frequency: based on sessions per day
    usage_score = score_dimension("usage_frequency", sessions_per_day)
    dimensions["usage_frequency"] = {
        "label": _RUBRIC["usage_frequency"]["label"],
        "level": usage_score,
        "level_label": _LEVEL_LABELS[usage_score],
    }

    # session_depth: based on average messages per session
    depth_score = score_dimension("session_depth", avg_messages_per_session)
    dimensions["session_depth"] = {
        "label": _RUBRIC["session_depth"]["label"],
        "level": depth_score,
        "level_label": _LEVEL_LABELS[depth_score],
    }

    # context_efficiency: based on cache efficiency
    efficiency_score = score_dimension("context_efficiency", context_efficiency)
    dimensions["context_efficiency"] = {
        "label": _RUBRIC["context_efficiency"]["label"],
        "level": efficiency_score,
        "level_label": _LEVEL_LABELS[efficiency_score],
    }

    # Calculate overall level as the average of dimension scores
    dimension_levels = [dim["level"] for dim in dimensions.values()]
    overall_level = round(sum(dimension_levels) / len(dimension_levels))
    # Clamp to valid range [0, 4]
    overall_level = max(0, min(4, overall_level))

    return {
        "overall_level": overall_level,
        "overall_label": _LEVEL_LABELS[overall_level],
        "dimensions": dimensions,
    }
