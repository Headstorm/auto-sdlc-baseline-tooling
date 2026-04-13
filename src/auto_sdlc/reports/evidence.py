"""
Evidence Triangulation Module

Combines LogEvidence, ConfigEvidence, and CapabilityEvidence into unified assessments
with per-dimension confidence scoring.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from auto_sdlc.reports.evidence_extractor import LogEvidence
from auto_sdlc.reports.config_extractor import ConfigEvidence
from auto_sdlc.reports.capability_extractor import CapabilityEvidence


@dataclass
class Evidence:
    """
    Unified evidence assessment combining all three sources for a single dimension.

    Attributes:
        dimension: Name of the dimension being assessed
        log_evidence: Behavioral signals from logs (optional)
        config_evidence: Configuration signals from files (optional list)
        capability_evidence: Deployed capabilities (optional list)
        confidence: Confidence level ("high", "medium", or "low")
        confidence_score: Numerical score 0.0-1.0
        triangulation_summary: Narrative summary integrating all sources
    """

    dimension: str
    log_evidence: Optional[LogEvidence] = None
    config_evidence: List[ConfigEvidence] = field(default_factory=list)
    capability_evidence: List[CapabilityEvidence] = field(default_factory=list)
    confidence: str = "medium"
    confidence_score: float = 0.5
    triangulation_summary: str = ""


class EvidenceTriangulator:
    """
    Triangulates three evidence sources to create unified dimension assessments.

    Uses confidence scoring logic:
    - High confidence (0.7+): Two or more sources strongly present
    - Medium confidence (0.4-0.7): At least one source present
    - Low confidence (<0.4): Minimal or missing data
    """

    def __init__(self):
        """Initialize the triangulator."""
        pass

    def triangulate(
        self,
        log_ev: Optional[LogEvidence],
        config_ev: List[ConfigEvidence],
        cap_ev: List[CapabilityEvidence],
        dimension: str,
    ) -> Evidence:
        """
        Triangulate all three evidence sources for a single dimension.

        Args:
            log_ev: Log evidence for the dimension
            config_ev: List of config evidence entries
            cap_ev: List of capability evidence entries
            dimension: Name of the dimension

        Returns:
            Unified Evidence object with confidence score and summary
        """
        confidence_level, confidence_score = self._assess_confidence(
            log_ev, config_ev, cap_ev
        )
        summary = self._generate_summary(dimension, log_ev, config_ev, cap_ev)

        return Evidence(
            dimension=dimension,
            log_evidence=log_ev,
            config_evidence=config_ev,
            capability_evidence=cap_ev,
            confidence=confidence_level,
            confidence_score=confidence_score,
            triangulation_summary=summary,
        )

    def _assess_confidence(
        self,
        log_ev: Optional[LogEvidence],
        config_ev: List[ConfigEvidence],
        cap_ev: List[CapabilityEvidence],
    ) -> Tuple[str, float]:
        """
        Calculate confidence level and score based on source presence and strength.

        Logic:
        Confidence = (log_presence * 0.4) + (config_presence * 0.3) + (capability_presence * 0.3)

        where:
          log_presence = 1.0 if high, 0.5 if medium, 0.0 if low/missing
          config_presence = 1.0 if "documented", 0.5 if "partial", 0.0 if "missing"
          capability_presence = 1.0 if active+advanced, 0.5 if basic/intermediate, 0.0 if none

        Args:
            log_ev: Log evidence (may be None)
            config_ev: Config evidence list (may be empty)
            cap_ev: Capability evidence list (may be empty)

        Returns:
            Tuple of (confidence_level, confidence_score)
            - confidence_level: "high", "medium", or "low"
            - confidence_score: float 0.0-1.0
        """
        # Calculate log presence score
        log_presence = 0.0
        if log_ev is not None:
            if log_ev.confidence == "high":
                log_presence = 1.0
            elif log_ev.confidence == "medium":
                log_presence = 0.5
            else:
                log_presence = 0.0

        # Calculate config presence score
        config_presence = 0.0
        if config_ev:
            # Use best quality from all config evidence entries
            qualities = []
            for ce in config_ev:
                for quality in ce.quality_indicators.values():
                    if quality == "documented":
                        qualities.append(1.0)
                    elif quality == "partial":
                        qualities.append(0.5)
                    else:
                        qualities.append(0.0)
            if qualities:
                config_presence = max(qualities)

        # Calculate capability presence score
        cap_presence = 0.0
        if cap_ev:
            # Use best sophistication from all capability evidence entries
            sophistications = []
            for ce in cap_ev:
                deployment_status = ce.deployment_status
                sophistication = ce.sophistication

                # Active + advanced = 1.0
                if deployment_status == "active" and sophistication == "advanced":
                    sophistications.append(1.0)
                # Active or advanced = 0.75
                elif deployment_status == "active" or sophistication == "advanced":
                    sophistications.append(0.75)
                # Basic/intermediate = 0.5
                elif sophistication in ["basic", "intermediate"]:
                    sophistications.append(0.5)
                # Installed = 0.25
                elif deployment_status == "installed":
                    sophistications.append(0.25)
                else:
                    sophistications.append(0.0)

            if sophistications:
                cap_presence = max(sophistications)

        # Weighted confidence score
        confidence_score = (
            log_presence * 0.4 + config_presence * 0.3 + cap_presence * 0.3
        )

        # Determine confidence level
        if confidence_score >= 0.7:
            confidence_level = "high"
        elif confidence_score >= 0.4:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        return confidence_level, round(confidence_score, 2)

    def _generate_summary(
        self,
        dimension: str,
        log_ev: Optional[LogEvidence],
        config_ev: List[ConfigEvidence],
        cap_ev: List[CapabilityEvidence],
    ) -> str:
        """
        Generate narrative summary describing evidence from all sources.

        Format: "Logs show X, configs document Y, capabilities include Z. [Alignment assessment]"

        Args:
            dimension: Name of the dimension
            log_ev: Log evidence (may be None)
            config_ev: Config evidence list
            cap_ev: Capability evidence list

        Returns:
            Narrative summary string
        """
        parts = []

        # Logs summary
        if log_ev is not None:
            signals_str = ", ".join(
                f"{k}: {v}" for k, v in list(log_ev.signals.items())[:2]
            )
            parts.append(f"Logs show {signals_str}")
        else:
            parts.append("No log signals detected")

        # Config summary
        if config_ev:
            qualities = set()
            for ce in config_ev:
                for quality in ce.quality_indicators.values():
                    if quality != "missing":
                        qualities.add(quality)
            if "documented" in qualities:
                parts.append("configs document this dimension")
            elif "partial" in qualities:
                parts.append("configs partially document this dimension")
            else:
                parts.append("configs lack documentation")
        else:
            parts.append("configs lack documentation")

        # Capabilities summary
        if cap_ev:
            cap_types = set()
            sophistications = []
            for ce in cap_ev:
                cap_types.add(ce.capability_type)
                sophistications.append(ce.sophistication)
            type_str = "/".join(sorted(cap_types))
            max_soph = max(
                sophistications,
                key=lambda x: ["basic", "intermediate", "advanced"].index(x),
            )
            parts.append(f"capabilities include {type_str} ({max_soph})")
        else:
            parts.append("no capabilities deployed")

        # Assess alignment
        has_log = log_ev is not None and log_ev.confidence == "high"
        has_config = any(
            "documented" in ce.quality_indicators.values() for ce in config_ev
        )
        has_cap = any(
            ce.deployment_status == "active" and ce.sophistication in ["advanced"]
            for ce in cap_ev
        )

        alignment_parts = [p for p in [has_log, has_config, has_cap] if p]
        if len(alignment_parts) >= 2:
            parts.append("Sources well-aligned.")
        elif len(alignment_parts) == 1:
            parts.append("Limited alignment between sources.")
        else:
            parts.append("Minimal evidence across sources.")

        return " ".join(parts)

    def triangulate_all(
        self,
        log_evidence: List[LogEvidence],
        config_evidence: List[ConfigEvidence],
        cap_evidence: List[CapabilityEvidence],
    ) -> List[Evidence]:
        """
        Triangulate evidence for all 12 dimensions.

        Args:
            log_evidence: List of LogEvidence objects (one per dimension)
            config_evidence: List of ConfigEvidence objects (one per dimension)
            cap_evidence: List of CapabilityEvidence objects (may be subset of dimensions)

        Returns:
            List of Evidence objects sorted by confidence_score (descending)
        """
        # Build lookup maps
        log_map = {le.dimension: le for le in log_evidence}
        config_map = {}
        for ce in config_evidence:
            if ce.dimension not in config_map:
                config_map[ce.dimension] = []
            config_map[ce.dimension].append(ce)

        cap_map = {}
        for cape in cap_evidence:
            if cape.dimension not in cap_map:
                cap_map[cape.dimension] = []
            cap_map[cape.dimension].append(cape)

        # Get all dimensions from log evidence (source of truth for all 12)
        all_dimensions = set(log_map.keys())

        # Triangulate each dimension
        evidence_list = []
        for dimension in all_dimensions:
            log_ev = log_map.get(dimension)
            conf_ev = config_map.get(dimension, [])
            cap_ev = cap_map.get(dimension, [])

            evidence = self.triangulate(log_ev, conf_ev, cap_ev, dimension)
            evidence_list.append(evidence)

        # Sort by confidence score (descending)
        evidence_list.sort(key=lambda e: e.confidence_score, reverse=True)

        return evidence_list
