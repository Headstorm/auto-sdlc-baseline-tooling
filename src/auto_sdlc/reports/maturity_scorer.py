"""
Maturity Scorer Module

Converts Evidence (triangulated from logs/configs/capabilities) and AssessmentResponses
(team answers to 50 questions) into L1-L4 maturity scores per dimension with confidence levels.

Scoring Logic:
- Evidence Score (0-1): (log_signals * 0.4) + (config_quality * 0.3) + (capability_sophistication * 0.3)
- Assessment Score (0-1): Convert responses to 0-1, weight by relevance, average, adjust for confidence
- Combined Score (0-1): (evidence_score * 0.6) + (assessment_score * 0.4)
- Maturity Level: 0.0-0.25 → L1, 0.25-0.5 → L2, 0.5-0.75 → L3, 0.75-1.0 → L4
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from auto_sdlc.reports.evidence import Evidence
from auto_sdlc.reports.assessment import AssessmentResponse, AssessmentQuestionsEngine


@dataclass
class DimensionScore:
    """
    Maturity score for a single dimension.

    Attributes:
        dimension: Name of the dimension (one of 12)
        maturity_level: L1-L4 (1, 2, 3, or 4)
        confidence: Confidence level ("high", "medium", or "low")
        confidence_score: Numerical confidence 0.0-1.0
        evidence_summary: How evidence informed the score
        assessment_summary: How assessment responses informed the score
        rationale: One-paragraph narrative explaining why this level
    """

    dimension: str
    maturity_level: int
    confidence: str
    confidence_score: float
    evidence_summary: str
    assessment_summary: str
    rationale: str


class MaturityScorer:
    """
    Scores maturity levels for each dimension based on evidence and assessment responses.

    Uses a weighted combination of evidence (60%) and assessment responses (40%) to
    produce L1-L4 scores with confidence levels for each of the 12 dimensions.
    """

    # 12 dimensions from CLAUDE.md
    DIMENSIONS = [
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

    # Map dimensions to question categories for response lookup
    DIMENSION_TO_CATEGORIES = {
        "AI Tool Adoption": ["AI Tool Adoption"],
        "Prompt & Context Engineering": ["Prompt & Context Engineering"],
        "Agent Configuration": ["Agent Configuration"],
        "CI/CD Integration": ["CI/CD Integration"],
        "Ticketing & Planning": ["Ticketing & Planning"],
        "Cross-System Connectivity": ["Cross-System Connectivity"],
        "Quality Controls": ["Quality Controls"],
        "Security & Compliance": ["Security & Compliance"],
        "Measurement & KPIs": ["Measurement & KPIs"],
        "Ways of Working": ["Ways of Working"],
        "Accountability & Ownership": ["Accountability & Ownership"],
        "Scalability & Knowledge Transfer": ["Scalability & Knowledge Transfer"],
    }

    def __init__(self):
        """Initialize the scorer with access to assessment questions."""
        self.questions_engine = AssessmentQuestionsEngine()

    def score_dimension(
        self, evidence: Evidence, responses: List[AssessmentResponse]
    ) -> DimensionScore:
        """
        Score a single dimension based on evidence and assessment responses.

        Args:
            evidence: Evidence object for the dimension
            responses: List of AssessmentResponse objects for this dimension

        Returns:
            DimensionScore with maturity level (L1-L4) and confidence
        """
        dimension = evidence.dimension

        # Calculate evidence score
        evidence_score = self._calculate_evidence_score(evidence)

        # Calculate assessment score
        assessment_score = self._calculate_assessment_score(
            dimension, responses, evidence
        )

        # Combine scores (60% evidence, 40% assessment)
        combined_score = (evidence_score * 0.6) + (assessment_score * 0.4)

        # Map to maturity level
        maturity_level = self._map_to_maturity_level(combined_score)

        # Determine confidence
        confidence_level, confidence_num = self._assess_confidence(
            evidence, assessment_score, responses
        )

        # Generate summaries and rationale
        evidence_summary = self._generate_evidence_summary(evidence)
        assessment_summary = self._generate_assessment_summary(dimension, responses)
        rationale = self._generate_rationale(
            dimension,
            maturity_level,
            evidence_score,
            assessment_score,
            combined_score,
            evidence,
        )

        return DimensionScore(
            dimension=dimension,
            maturity_level=maturity_level,
            confidence=confidence_level,
            confidence_score=confidence_num,
            evidence_summary=evidence_summary,
            assessment_summary=assessment_summary,
            rationale=rationale,
        )

    def score_all_dimensions(
        self, evidences: List[Evidence], responses: List[AssessmentResponse]
    ) -> Dict[str, DimensionScore]:
        """
        Score all 12 dimensions at once.

        Args:
            evidences: List of Evidence objects (one per dimension)
            responses: List of AssessmentResponse objects (all responses)

        Returns:
            Dictionary mapping dimension name to DimensionScore
        """
        scores = {}

        # Group responses by dimension/category
        responses_by_category = self._group_responses_by_category(responses)

        for evidence in evidences:
            dimension = evidence.dimension

            # Get relevant responses for this dimension
            categories = self.DIMENSION_TO_CATEGORIES.get(dimension, [])
            dimension_responses = []
            for category in categories:
                dimension_responses.extend(responses_by_category.get(category, []))

            # Score the dimension
            score = self.score_dimension(evidence, dimension_responses)
            scores[dimension] = score

        return scores

    def _calculate_evidence_score(self, evidence: Evidence) -> float:
        """
        Calculate evidence score from all three sources.

        Formula:
            evidence_score = (log_signals * 0.4) + (config_quality * 0.3) + (capability_sophistication * 0.3)

        Args:
            evidence: Evidence object

        Returns:
            Score 0.0-1.0
        """
        # Log signals score (0.0-1.0)
        log_score = 0.0
        if evidence.log_evidence is not None:
            if evidence.log_evidence.signals:
                # Average all signal values (they should be 0-1)
                signals = list(evidence.log_evidence.signals.values())
                log_score = sum(signals) / len(signals) if signals else 0.0
            else:
                # If no signals, use confidence mapping
                if evidence.log_evidence.confidence == "high":
                    log_score = 0.8
                elif evidence.log_evidence.confidence == "medium":
                    log_score = 0.5
                else:
                    log_score = 0.2

        # Config quality score (0.0-1.0)
        config_score = 0.0
        if evidence.config_evidence:
            qualities = []
            for ce in evidence.config_evidence:
                for quality in ce.quality_indicators.values():
                    if quality == "documented":
                        qualities.append(1.0)
                    elif quality == "partial":
                        qualities.append(0.5)
                    else:
                        qualities.append(0.0)
            if qualities:
                config_score = max(qualities)

        # Capability sophistication score (0.0-1.0)
        capability_score = 0.0
        if evidence.capability_evidence:
            sophistications = []
            for ce in evidence.capability_evidence:
                deployment = ce.deployment_status
                sophistication = ce.sophistication

                # Active + advanced = 1.0
                if deployment == "active" and sophistication == "advanced":
                    sophistications.append(1.0)
                # Active or advanced = 0.75
                elif deployment == "active" or sophistication == "advanced":
                    sophistications.append(0.75)
                # Basic/intermediate = 0.5
                elif sophistication in ["basic", "intermediate"]:
                    sophistications.append(0.5)
                # Installed = 0.25
                elif deployment == "installed":
                    sophistications.append(0.25)
                else:
                    sophistications.append(0.0)

            if sophistications:
                capability_score = max(sophistications)

        # Weighted combination
        evidence_score = (
            log_score * 0.4 + config_score * 0.3 + capability_score * 0.3
        )
        return round(evidence_score, 3)

    def _calculate_assessment_score(
        self,
        dimension: str,
        responses: List[AssessmentResponse],
        evidence: Evidence,
    ) -> float:
        """
        Calculate assessment score from team responses.

        Converts responses to 0-1 scale, weights by relevance, averages, and adjusts for confidence.

        Args:
            dimension: Dimension name
            responses: List of AssessmentResponse objects for this dimension
            evidence: Evidence for context (not used directly but passed for future enhancement)

        Returns:
            Score 0.0-1.0
        """
        if not responses:
            return 0.0

        # Convert responses to scores
        response_scores = []
        for response in responses:
            # Convert answer to score
            answer_lower = response.answer.lower()

            # Check for negative indicators first
            if any(
                word in answer_lower
                for word in ["no,", "no ", "not ", "don't", "missing", "none", "doesn't"]
            ):
                answer_score = 0.0
            # Check for positive indicators
            elif any(
                word in answer_lower
                for word in ["yes", "yes,", "documented", "active", "strong", "implemented"]
            ):
                answer_score = 1.0
            # Check for partial/conditional indicators
            elif any(
                word in answer_lower
                for word in ["partial", "some", "partially", "basic", "manual", "sometimes"]
            ):
                answer_score = 0.5
            else:
                # Neutral or unclear - default to 0.5
                answer_score = 0.5

            # Adjust for confidence
            confidence_multiplier = 1.0
            if response.confidence == "certain":
                confidence_multiplier = 1.0
            elif response.confidence == "likely":
                confidence_multiplier = 0.8
            elif response.confidence == "unsure":
                confidence_multiplier = 0.5

            adjusted_score = answer_score * confidence_multiplier
            response_scores.append(adjusted_score)

        # Average all response scores
        assessment_score = sum(response_scores) / len(response_scores)
        return round(assessment_score, 3)

    def _map_to_maturity_level(self, combined_score: float) -> int:
        """
        Map combined score to maturity level L1-L4.

        Mapping:
        - 0.0-0.25 → L1 (Assisted)
        - 0.25-0.5 → L2 (Integrated)
        - 0.5-0.75 → L3 (Agentic)
        - 0.75-1.0 → L4 (Autonomous)

        Args:
            combined_score: Score 0.0-1.0

        Returns:
            Maturity level 1-4
        """
        if combined_score < 0.25:
            return 1
        elif combined_score < 0.5:
            return 2
        elif combined_score < 0.75:
            return 3
        else:
            return 4

    def _assess_confidence(
        self,
        evidence: Evidence,
        assessment_score: float,
        responses: List[AssessmentResponse],
    ) -> Tuple[str, float]:
        """
        Assess confidence in the final score.

        Combines evidence confidence, assessment score strength, and response data quality.

        High confidence: strong evidence (0.7+) + aligned assessment + sufficient responses
        Medium confidence: one source strong or limited data
        Low confidence: weak evidence, weak assessment, or minimal data

        Args:
            evidence: Evidence object with confidence
            assessment_score: Assessment score 0-1
            responses: Assessment responses for this dimension

        Returns:
            Tuple of (confidence_level, confidence_score)
        """
        # Base: evidence confidence is primary (40%)
        evidence_confidence = evidence.confidence_score

        # Assessment certainty (40%): high if responses are "certain" confidence
        response_certainties = [
            1.0 if r.confidence == "certain" else (0.8 if r.confidence == "likely" else 0.5)
            for r in responses
        ]
        assessment_certainty = (
            sum(response_certainties) / len(response_certainties)
            if response_certainties
            else 0.0
        )

        # Data availability (20%): 4+ responses = full confidence
        num_responses = len(responses)
        data_availability = min(1.0, num_responses / 4.0)

        # Combine with strict weights
        confidence_score = round(
            (
                evidence_confidence * 0.4
                + assessment_certainty * 0.4
                + data_availability * 0.2
            ),
            2,
        )

        # Determine level with stricter thresholds
        if confidence_score >= 0.75:
            confidence_level = "high"
        elif confidence_score >= 0.45:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        return confidence_level, confidence_score

    def _generate_evidence_summary(self, evidence: Evidence) -> str:
        """
        Generate summary of how evidence informed the score.

        Args:
            evidence: Evidence object

        Returns:
            Summary string
        """
        parts = []

        # Log signals
        if evidence.log_evidence and evidence.log_evidence.signals:
            signals_str = ", ".join(
                f"{k}={v:.1%}" for k, v in list(evidence.log_evidence.signals.items())[:2]
            )
            parts.append(f"Logs: {signals_str}")

        # Config
        if evidence.config_evidence:
            qualities = set()
            for ce in evidence.config_evidence:
                for quality in ce.quality_indicators.values():
                    if quality != "missing":
                        qualities.add(quality)
            if "documented" in qualities:
                parts.append("Config: documented")
            elif "partial" in qualities:
                parts.append("Config: partially documented")
            else:
                parts.append("Config: not documented")

        # Capabilities
        if evidence.capability_evidence:
            caps = [ce.capability_type for ce in evidence.capability_evidence]
            sophistications = [ce.sophistication for ce in evidence.capability_evidence]
            max_soph = max(
                sophistications,
                key=lambda x: ["basic", "intermediate", "advanced"].index(x),
            )
            parts.append(f"Capabilities: {len(caps)} deployed ({max_soph})")

        summary = " | ".join(parts) if parts else "No evidence available"
        return summary

    def _generate_assessment_summary(
        self, dimension: str, responses: List[AssessmentResponse]
    ) -> str:
        """
        Generate summary of how assessment responses informed the score.

        Args:
            dimension: Dimension name
            responses: Assessment responses for this dimension

        Returns:
            Summary string
        """
        if not responses:
            return "No assessment responses provided"

        # Count response types
        yes_count = sum(
            1
            for r in responses
            if any(
                word in r.answer.lower()
                for word in ["yes", "documented", "active", "strong"]
            )
        )
        partial_count = sum(
            1
            for r in responses
            if any(
                word in r.answer.lower()
                for word in ["partial", "some", "basic"]
            )
        )
        no_count = len(responses) - yes_count - partial_count

        # Build summary
        parts = []
        if yes_count > 0:
            parts.append(f"{yes_count} positive")
        if partial_count > 0:
            parts.append(f"{partial_count} partial")
        if no_count > 0:
            parts.append(f"{no_count} negative")

        return f"{len(responses)} responses: {', '.join(parts)}"

    def _generate_rationale(
        self,
        dimension: str,
        maturity_level: int,
        evidence_score: float,
        assessment_score: float,
        combined_score: float,
        evidence: Evidence,
    ) -> str:
        """
        Generate one-paragraph narrative rationale for the score.

        Args:
            dimension: Dimension name
            maturity_level: L1-L4
            evidence_score: Evidence score 0-1
            assessment_score: Assessment score 0-1
            combined_score: Combined score 0-1
            evidence: Evidence object

        Returns:
            Rationale string
        """
        level_names = {1: "L1 (Assisted)", 2: "L2 (Integrated)", 3: "L3 (Agentic)", 4: "L4 (Autonomous)"}
        level_descriptions = {
            1: "Evidence-driven activities require external guidance and oversight.",
            2: "Documented practices and tooling are integrated into workflows.",
            3: "Agentic capabilities enable semi-autonomous execution.",
            4: "Fully autonomous, sustainable practices across the team.",
        }

        # Determine alignment between evidence and assessment
        alignment = "align"
        if abs(evidence_score - assessment_score) > 0.3:
            if evidence_score > assessment_score:
                alignment = "exceed team perceptions"
            else:
                alignment = "lag team perceptions"

        next_level = maturity_level + 1 if maturity_level < 4 else 4
        next_steps = {
            1: "Focus on establishing documented practices and basic tooling.",
            2: "Expand tool adoption and automation in CI/CD pipelines.",
            3: "Build agentic workflows and improve cross-system connectivity.",
            4: "Maintain sustainable practices and continuously improve execution.",
        }

        rationale = (
            f"{dimension} is at {level_names[maturity_level]} ({level_descriptions[maturity_level]}) "
            f"based on evidence (score: {evidence_score:.2f}) and team assessment (score: {assessment_score:.2f}) which {alignment}. "
            f"Next step: {next_steps[maturity_level]}"
        )

        return rationale

    def _group_responses_by_category(
        self, responses: List[AssessmentResponse]
    ) -> Dict[str, List[AssessmentResponse]]:
        """
        Group responses by their question category.

        Args:
            responses: List of AssessmentResponse objects

        Returns:
            Dict mapping category name to list of responses
        """
        questions = self.questions_engine.load_questions()
        question_map = {q.id: q for q in questions}

        grouped = {}
        for response in responses:
            question = question_map.get(response.question_id)
            if question:
                category = question.category
                if category not in grouped:
                    grouped[category] = []
                grouped[category].append(response)

        return grouped
