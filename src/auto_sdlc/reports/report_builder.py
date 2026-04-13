"""
Report Builder Module

Synthesizes Evidence, DimensionScore, and RoadmapItem objects into complete
TeamReport and IndividualReport objects ready for PDF rendering.

The builder pattern here follows the data flow:
- Phase 2 produces: DimensionScore objects (maturity levels + confidence)
- Phase 2 produces: RoadmapItem objects (actionable steps)
- Phase 3 (this module) synthesizes them into narrative-rich reports
"""

from typing import Dict, List, Optional
from datetime import datetime

from auto_sdlc.reports.models import (
    DimensionReport,
    TeamReport,
    IndividualReport,
    ALL_DIMENSIONS,
)
from auto_sdlc.reports.maturity_scorer import DimensionScore
from auto_sdlc.reports.roadmap import RoadmapItem, RoadmapAction


class TeamReportBuilder:
    """
    Builds complete TeamReport objects from dimension scores and roadmaps.

    Synthesizes all 12 DimensionScore and RoadmapItem objects into a narrative-rich
    TeamReport with executive summary, key insights, and strategic recommendations.
    """

    # Narrative templates for current state by maturity level
    LEVEL_NARRATIVES = {
        1: "Early adoption. Focus on standardization and tool selection.",
        2: "Integrated. Documented practices with emerging tooling.",
        3: "Agentic. Multi-tool ecosystem with automation.",
        4: "Autonomous. Self-improving, proactive practices.",
    }

    def __init__(self):
        """Initialize the TeamReportBuilder."""
        pass

    def build_team_report(
        self,
        dimension_scores: Dict[str, DimensionScore],
        roadmaps: Dict[str, RoadmapItem],
        team_metadata: Dict,
        data_sources: Dict[str, bool],
    ) -> TeamReport:
        """
        Build a complete TeamReport from dimension scores and roadmaps.

        Args:
            dimension_scores: Dict[dimension_name -> DimensionScore] (all 12 dimensions)
            roadmaps: Dict[dimension_name -> RoadmapItem] (all 12 dimensions)
            team_metadata: Dict with keys: team_name, team_size, assessment_period_weeks, report_date
            data_sources: Dict[source_name -> bool] indicating which sources available
                Example: {"logs": True, "configs": True, "capabilities": True}

        Returns:
            TeamReport object ready for PDF rendering

        Raises:
            ValueError: If required dimensions are missing
        """
        # Validate all 12 dimensions are present
        missing = ALL_DIMENSIONS - set(dimension_scores.keys())
        if missing:
            raise ValueError(
                f"Missing dimension scores for: {sorted(missing)}"
            )

        missing_roadmaps = ALL_DIMENSIONS - set(roadmaps.keys())
        if missing_roadmaps:
            raise ValueError(
                f"Missing roadmaps for: {sorted(missing_roadmaps)}"
            )

        # Build dimension reports
        dimensions = self._build_dimension_reports(dimension_scores, roadmaps)

        # Calculate overall maturity
        overall_maturity = self._calculate_overall_maturity(dimension_scores)

        # Build confidence map
        confidence_by_dimension = self._build_confidence_map(dimension_scores)

        # Generate narrative components
        executive_summary = self._generate_executive_summary(
            dimension_scores, overall_maturity, dimensions
        )
        key_insights = self._extract_key_insights(dimension_scores, dimensions)
        recommendations = self._generate_recommendations(
            dimension_scores, dimensions, roadmaps
        )
        next_steps = self._generate_next_steps(roadmaps)

        # Create and return the report
        report = TeamReport(
            team_name=team_metadata.get("team_name", "Team"),
            report_date=team_metadata.get("report_date", datetime.now().strftime("%Y-%m-%d")),
            data_sources=data_sources,
            team_size=team_metadata.get("team_size", 1),
            assessment_period_weeks=team_metadata.get("assessment_period_weeks", 0),
            overall_maturity_level=overall_maturity,
            dimensions=dimensions,
            executive_summary=executive_summary,
            key_insights=key_insights,
            recommendations=recommendations,
            confidence_by_dimension=confidence_by_dimension,
            next_steps=next_steps,
        )

        return report

    def _build_dimension_reports(
        self,
        dimension_scores: Dict[str, DimensionScore],
        roadmaps: Dict[str, RoadmapItem],
    ) -> Dict[str, DimensionReport]:
        """
        Convert DimensionScore + RoadmapItem → DimensionReport for each dimension.

        Args:
            dimension_scores: Dict of DimensionScore objects
            roadmaps: Dict of RoadmapItem objects

        Returns:
            Dict mapping dimension name to DimensionReport
        """
        dimensions = {}

        for dimension in sorted(ALL_DIMENSIONS):
            score = dimension_scores[dimension]
            roadmap = roadmaps[dimension]

            # Generate current state narrative
            current_state = self._generate_current_state_narrative(score)

            # Build evidence summary from the score
            evidence_summary = self._build_evidence_summary(score)

            # Extract gaps and strengths from rationale and score data
            gaps, strengths = self._extract_gaps_and_strengths(score)

            # Convert roadmap actions to dict format
            roadmap_dicts = [
                {
                    "step": action.step,
                    "title": action.title,
                    "description": action.description,
                    "effort_hours": action.effort_hours,
                    "effort_weeks": action.effort_weeks,
                    "owners": action.owners,
                    "success_criteria": action.success_criteria,
                    "risk": action.risk,
                }
                for action in roadmap.actions
            ]

            dimension_report = DimensionReport(
                dimension=dimension,
                maturity_level=score.maturity_level,
                confidence=score.confidence,
                current_state=current_state,
                evidence_summary=evidence_summary,
                gaps=gaps,
                strengths=strengths,
                roadmap=roadmap_dicts,
            )

            dimensions[dimension] = dimension_report

        return dimensions

    def _generate_current_state_narrative(self, score: DimensionScore) -> str:
        """
        Generate a clear narrative of current state based on maturity level and score rationale.

        Args:
            score: DimensionScore object

        Returns:
            Narrative string describing current state
        """
        level_desc = self.LEVEL_NARRATIVES.get(score.maturity_level, "")
        return f"L{score.maturity_level}: {level_desc} {score.rationale}"

    def _build_evidence_summary(self, score: DimensionScore) -> Dict[str, str]:
        """
        Build evidence summary from the DimensionScore.

        Args:
            score: DimensionScore object

        Returns:
            Dict with evidence_summary and assessment_summary
        """
        return {
            "evidence_summary": score.evidence_summary,
            "assessment_summary": score.assessment_summary,
        }

    def _extract_gaps_and_strengths(
        self, score: DimensionScore
    ) -> tuple[List[str], List[str]]:
        """
        Extract gaps and strengths from score rationale and assessment.

        Args:
            score: DimensionScore object

        Returns:
            Tuple of (gaps_list, strengths_list)
        """
        # Extract from rationale - look for common gap/strength indicators
        rationale_lower = score.rationale.lower()

        gaps = []
        strengths = []

        # Simple heuristic-based extraction
        if "lacks" in rationale_lower or "missing" in rationale_lower or "not" in rationale_lower:
            gaps.append(f"Gaps identified in {score.dimension.lower()} practices")

        if "strong" in rationale_lower or "well" in rationale_lower or "consistent" in rationale_lower:
            strengths.append(f"Strong {score.dimension.lower()} practices")

        # Default if nothing extracted
        if not gaps:
            gaps.append(f"Continue developing {score.dimension.lower()}")
        if not strengths:
            strengths.append(f"Foundation in {score.dimension.lower()} established")

        return gaps, strengths

    def _calculate_overall_maturity(
        self, dimension_scores: Dict[str, DimensionScore]
    ) -> float:
        """
        Calculate average maturity across all 12 dimensions.

        Args:
            dimension_scores: Dict of DimensionScore objects

        Returns:
            Average maturity level (1.0-4.0)
        """
        if not dimension_scores:
            return 1.0

        total = sum(score.maturity_level for score in dimension_scores.values())
        average = total / len(dimension_scores)

        # Ensure within bounds
        return min(max(average, 1.0), 4.0)

    def _build_confidence_map(
        self, dimension_scores: Dict[str, DimensionScore]
    ) -> Dict[str, str]:
        """
        Build confidence level map for each dimension.

        Args:
            dimension_scores: Dict of DimensionScore objects

        Returns:
            Dict mapping dimension name to confidence level
        """
        confidence_map = {}

        for dimension in sorted(ALL_DIMENSIONS):
            score = dimension_scores[dimension]
            confidence_map[dimension] = score.confidence

        return confidence_map

    def _generate_executive_summary(
        self,
        dimension_scores: Dict[str, DimensionScore],
        overall_maturity: float,
        dimensions: Dict[str, DimensionReport],
    ) -> str:
        """
        Generate 1-2 paragraph executive summary of team maturity.

        Args:
            dimension_scores: Dict of DimensionScore objects
            overall_maturity: Overall maturity level
            dimensions: Dict of DimensionReport objects

        Returns:
            Executive summary narrative
        """
        # Identify strengths and gaps
        strengths_dims = [
            d for d, score in dimension_scores.items()
            if score.maturity_level >= 3
        ]
        gap_dims = [
            d for d, score in dimension_scores.items()
            if score.maturity_level == 1
        ]

        strengths_str = ", ".join(sorted(strengths_dims)[:3]) if strengths_dims else "none yet"
        gaps_str = ", ".join(sorted(gap_dims)[:3]) if gap_dims else "none"

        # Build summary
        summary = f"Team demonstrates {overall_maturity:.1f}/4.0 overall AI maturity. "
        summary += f"Key strengths: {strengths_str}. "
        summary += f"Primary growth opportunities: {gaps_str}. "
        summary += f"Estimated 3-6 months to advance key dimensions to L3 through focused action on roadmap items."

        return summary

    def _extract_key_insights(
        self,
        dimension_scores: Dict[str, DimensionScore],
        dimensions: Dict[str, DimensionReport],
    ) -> List[str]:
        """
        Extract top 3-5 key findings across all dimensions.

        Args:
            dimension_scores: Dict of DimensionScore objects
            dimensions: Dict of DimensionReport objects

        Returns:
            List of 3-5 key insight strings
        """
        insights = []

        # Insight 1: Overall maturity level
        all_levels = [score.maturity_level for score in dimension_scores.values()]
        avg_level = sum(all_levels) / len(all_levels)
        insights.append(
            f"Team maturity averages L{avg_level:.1f} across all 12 dimensions"
        )

        # Insight 2: Consistency
        high_confidence = [
            d for d, score in dimension_scores.items()
            if score.confidence == "high"
        ]
        if len(high_confidence) >= 8:
            insights.append("Strong assessment confidence across most dimensions")
        else:
            insights.append("Some dimensions need additional assessment data")

        # Insight 3: Gaps vs strengths
        l1_dims = [d for d, score in dimension_scores.items() if score.maturity_level == 1]
        l3_l4_dims = [d for d, score in dimension_scores.items() if score.maturity_level >= 3]
        if l1_dims:
            insights.append(f"Foundational gaps in: {', '.join(sorted(l1_dims)[:2])}")
        if l3_l4_dims:
            insights.append(f"Advanced practices in: {', '.join(sorted(l3_l4_dims)[:2])}")

        # Insight 4: Alignment
        aligned = [
            d for d, dim_report in dimensions.items()
            if len(dim_report.gaps) < 3 and len(dim_report.strengths) > 0
        ]
        if len(aligned) >= 6:
            insights.append("Good alignment between documentation and actual practices")

        return insights[:5]  # Return top 5

    def _generate_recommendations(
        self,
        dimension_scores: Dict[str, DimensionScore],
        dimensions: Dict[str, DimensionReport],
        roadmaps: Dict[str, RoadmapItem],
    ) -> List[str]:
        """
        Generate strategic recommendations prioritized by impact and feasibility.

        Args:
            dimension_scores: Dict of DimensionScore objects
            dimensions: Dict of DimensionReport objects
            roadmaps: Dict of RoadmapItem objects

        Returns:
            List of prioritized recommendation strings
        """
        recommendations = []

        # Find dimensions at L1 (highest impact targets)
        l1_dims = sorted(
            [d for d, score in dimension_scores.items() if score.maturity_level == 1]
        )

        # Find low-effort L1→L2 transitions
        for dim in l1_dims[:3]:  # Top 3 L1 dimensions
            roadmap = roadmaps.get(dim)
            if roadmap and roadmap.total_effort_weeks <= 4:
                recommendations.append(
                    f"Prioritize {dim} to L2 (estimated {roadmap.total_effort_weeks} weeks)"
                )

        # Find quick wins in L2 dimensions
        l2_dims = [d for d, score in dimension_scores.items() if score.maturity_level == 2]
        for dim in sorted(l2_dims)[:2]:  # Top 2 L2 dimensions
            roadmap = roadmaps.get(dim)
            if roadmap:
                quick_actions = [a for a in roadmap.actions if a.effort_hours <= 8]
                if quick_actions:
                    recommendations.append(
                        f"Execute quick-win actions in {dim} (e.g., {quick_actions[0].title})"
                    )

        # Consolidation recommendation
        if len(l1_dims) > 0:
            recommendations.append(
                f"Establish governance board to oversee maturity improvements"
            )

        # Tool adoption recommendation
        if dimension_scores.get("AI Tool Adoption", DimensionScore("AI Tool Adoption", 1, "low", 0.0, "", "", "")).maturity_level < 3:
            recommendations.append(
                "Implement centralized tool management and tracking dashboard"
            )

        return recommendations[:6]  # Top 6 recommendations

    def _generate_next_steps(self, roadmaps: Dict[str, RoadmapItem]) -> List[str]:
        """
        Generate immediate action items (first actions from key roadmaps).

        Args:
            roadmaps: Dict of RoadmapItem objects

        Returns:
            List of immediate next steps
        """
        next_steps = []

        # Collect first actions from all roadmaps with manageable effort
        for roadmap in roadmaps.values():
            if roadmap.actions:
                first_action = roadmap.actions[0]
                if first_action.effort_hours <= 8:  # Quick actions
                    next_steps.append(
                        f"{first_action.title} ({first_action.effort_hours}h)"
                    )

        return next_steps[:5]  # Top 5 immediate steps


class IndividualReportBuilder:
    """
    Builds complete IndividualReport objects for individual developers.

    Synthesizes developer-specific DimensionScore and RoadmapItem objects into
    a personalized report with learning path and comparison to team baseline.
    """

    def __init__(self):
        """Initialize the IndividualReportBuilder."""
        pass

    def build_individual_report(
        self,
        dimension_scores: Dict[str, DimensionScore],
        roadmaps: Dict[str, RoadmapItem],
        developer_metadata: Dict,
        team_baseline: Dict[str, float],
        data_sources: Dict[str, bool],
    ) -> IndividualReport:
        """
        Build a complete IndividualReport for a developer.

        Args:
            dimension_scores: Dict[dimension_name -> DimensionScore] (all 12 dimensions)
            roadmaps: Dict[dimension_name -> RoadmapItem] (all 12 dimensions)
            developer_metadata: Dict with keys: developer_id, report_date, assessment_period_weeks,
                usage_patterns (dict with sessions/day, messages/session, etc.)
            team_baseline: Dict[dimension_name -> float] (team average for each dimension)
            data_sources: Dict[source_name -> bool] indicating which sources available

        Returns:
            IndividualReport object ready for PDF rendering

        Raises:
            ValueError: If required dimensions are missing
        """
        # Validate all 12 dimensions are present
        missing = ALL_DIMENSIONS - set(dimension_scores.keys())
        if missing:
            raise ValueError(
                f"Missing dimension scores for: {sorted(missing)}"
            )

        missing_roadmaps = ALL_DIMENSIONS - set(roadmaps.keys())
        if missing_roadmaps:
            raise ValueError(
                f"Missing roadmaps for: {sorted(missing_roadmaps)}"
            )

        # Build dimension reports (similar to team, but developer-specific)
        dimensions = self._build_dimension_reports(dimension_scores, roadmaps)

        # Calculate developer's overall maturity
        overall_maturity = self._calculate_overall_maturity(dimension_scores)

        # Compare to team baseline
        strengths = self._identify_strengths(dimension_scores, team_baseline)
        growth_areas = self._identify_growth_areas(dimension_scores, team_baseline)
        fit_with_baseline = self._compare_to_team_baseline(
            dimension_scores, team_baseline
        )

        # Generate learning path
        learning_path = self._generate_learning_path(
            dimension_scores, team_baseline, roadmaps
        )

        # Generate narratives
        executive_summary = self._generate_executive_summary(
            developer_metadata.get("developer_id", "Developer"),
            overall_maturity,
            fit_with_baseline,
        )
        key_insights = self._extract_key_insights(dimension_scores, team_baseline)
        recommendations = self._generate_personalized_recommendations(
            dimension_scores, team_baseline, roadmaps
        )

        # Create and return the report
        report = IndividualReport(
            developer_id=developer_metadata.get("developer_id", "unknown"),
            report_date=developer_metadata.get("report_date", datetime.now().strftime("%Y-%m-%d")),
            assessment_period_weeks=developer_metadata.get("assessment_period_weeks", 0),
            overall_maturity_level=overall_maturity,
            dimensions=dimensions,
            executive_summary=executive_summary,
            usage_patterns=developer_metadata.get("usage_patterns", {}),
            strengths=strengths,
            growth_areas=growth_areas,
            fit_with_team_baseline=fit_with_baseline,
            learning_path=learning_path,
            key_insights=key_insights,
            recommendations=recommendations,
        )

        return report

    def _build_dimension_reports(
        self,
        dimension_scores: Dict[str, DimensionScore],
        roadmaps: Dict[str, RoadmapItem],
    ) -> Dict[str, DimensionReport]:
        """
        Convert DimensionScore + RoadmapItem → DimensionReport for each dimension.

        Args:
            dimension_scores: Dict of DimensionScore objects
            roadmaps: Dict of RoadmapItem objects

        Returns:
            Dict mapping dimension name to DimensionReport
        """
        dimensions = {}

        for dimension in sorted(ALL_DIMENSIONS):
            score = dimension_scores[dimension]
            roadmap = roadmaps[dimension]

            # Generate current state narrative
            current_state = self._generate_current_state_narrative(score)

            # Build evidence summary
            evidence_summary = {
                "evidence_summary": score.evidence_summary,
                "assessment_summary": score.assessment_summary,
            }

            # Extract gaps and strengths
            gaps, strengths = self._extract_gaps_and_strengths(score)

            # Convert roadmap actions
            roadmap_dicts = [
                {
                    "step": action.step,
                    "title": action.title,
                    "description": action.description,
                    "effort_hours": action.effort_hours,
                    "effort_weeks": action.effort_weeks,
                    "owners": action.owners,
                    "success_criteria": action.success_criteria,
                    "risk": action.risk,
                }
                for action in roadmap.actions
            ]

            dimension_report = DimensionReport(
                dimension=dimension,
                maturity_level=score.maturity_level,
                confidence=score.confidence,
                current_state=current_state,
                evidence_summary=evidence_summary,
                gaps=gaps,
                strengths=strengths,
                roadmap=roadmap_dicts,
            )

            dimensions[dimension] = dimension_report

        return dimensions

    def _generate_current_state_narrative(self, score: DimensionScore) -> str:
        """
        Generate narrative of current state.

        Args:
            score: DimensionScore object

        Returns:
            Narrative string
        """
        level_narratives = {
            1: "Early adoption. Focus on standardization and tool selection.",
            2: "Integrated. Documented practices with emerging tooling.",
            3: "Agentic. Multi-tool ecosystem with automation.",
            4: "Autonomous. Self-improving, proactive practices.",
        }
        level_desc = level_narratives.get(score.maturity_level, "")
        return f"L{score.maturity_level}: {level_desc} {score.rationale}"

    def _extract_gaps_and_strengths(
        self, score: DimensionScore
    ) -> tuple[List[str], List[str]]:
        """
        Extract gaps and strengths from score.

        Args:
            score: DimensionScore object

        Returns:
            Tuple of (gaps_list, strengths_list)
        """
        gaps = []
        strengths = []

        rationale_lower = score.rationale.lower()

        if "lacks" in rationale_lower or "missing" in rationale_lower or "not" in rationale_lower:
            gaps.append(f"Gaps in {score.dimension.lower()}")

        if "strong" in rationale_lower or "well" in rationale_lower or "consistent" in rationale_lower:
            strengths.append(f"Strong {score.dimension.lower()} practices")

        if not gaps:
            gaps.append(f"Continue developing {score.dimension.lower()}")
        if not strengths:
            strengths.append(f"Foundation in {score.dimension.lower()}")

        return gaps, strengths

    def _calculate_overall_maturity(
        self, dimension_scores: Dict[str, DimensionScore]
    ) -> float:
        """
        Calculate developer's average maturity across all 12 dimensions.

        Args:
            dimension_scores: Dict of DimensionScore objects

        Returns:
            Average maturity level (1.0-4.0)
        """
        if not dimension_scores:
            return 1.0

        total = sum(score.maturity_level for score in dimension_scores.values())
        average = total / len(dimension_scores)

        return min(max(average, 1.0), 4.0)

    def _identify_strengths(
        self,
        dimension_scores: Dict[str, DimensionScore],
        team_baseline: Dict[str, float],
    ) -> List[str]:
        """
        Identify dimensions where developer is at or above team baseline.

        Args:
            dimension_scores: Dict of DimensionScore objects
            team_baseline: Dict of team average scores

        Returns:
            List of strength statements
        """
        strengths = []

        for dimension in sorted(ALL_DIMENSIONS):
            dev_level = dimension_scores[dimension].maturity_level
            team_avg = team_baseline.get(dimension, 2.0)

            if dev_level >= team_avg:
                strengths.append(
                    f"{dimension}: L{dev_level} (team avg: L{team_avg:.1f})"
                )

        return strengths

    def _identify_growth_areas(
        self,
        dimension_scores: Dict[str, DimensionScore],
        team_baseline: Dict[str, float],
    ) -> List[str]:
        """
        Identify dimensions where developer is below team baseline.

        Args:
            dimension_scores: Dict of DimensionScore objects
            team_baseline: Dict of team average scores

        Returns:
            List of growth area statements
        """
        growth_areas = []

        for dimension in sorted(ALL_DIMENSIONS):
            dev_level = dimension_scores[dimension].maturity_level
            team_avg = team_baseline.get(dimension, 2.0)

            if dev_level < team_avg:
                growth_areas.append(
                    f"{dimension}: L{dev_level} (team avg: L{team_avg:.1f})"
                )

        return growth_areas

    def _compare_to_team_baseline(
        self,
        dimension_scores: Dict[str, DimensionScore],
        team_baseline: Dict[str, float],
    ) -> str:
        """
        Generate comparison statement: "Above/Below/At team average in X dimensions".

        Args:
            dimension_scores: Dict of DimensionScore objects
            team_baseline: Dict of team average scores

        Returns:
            Comparison narrative
        """
        dev_avg = sum(score.maturity_level for score in dimension_scores.values()) / len(dimension_scores)
        team_avg = sum(team_baseline.values()) / len(team_baseline)

        above = sum(
            1 for d, score in dimension_scores.items()
            if score.maturity_level > team_baseline.get(d, 2.0)
        )
        below = sum(
            1 for d, score in dimension_scores.items()
            if score.maturity_level < team_baseline.get(d, 2.0)
        )

        if dev_avg > team_avg:
            return f"Developer is above team average (L{dev_avg:.1f} vs L{team_avg:.1f}), excelling in {above} dimensions."
        elif dev_avg < team_avg:
            return f"Developer is below team average (L{dev_avg:.1f} vs L{team_avg:.1f}), with growth opportunities in {below} dimensions."
        else:
            return f"Developer is at team average (L{dev_avg:.1f}), with balanced growth across all dimensions."

    def _generate_learning_path(
        self,
        dimension_scores: Dict[str, DimensionScore],
        team_baseline: Dict[str, float],
        roadmaps: Dict[str, RoadmapItem],
    ) -> List[str]:
        """
        Generate prioritized learning path: specific skills to develop.

        Args:
            dimension_scores: Dict of DimensionScore objects
            team_baseline: Dict of team average scores
            roadmaps: Dict of RoadmapItem objects

        Returns:
            List of prioritized skill development items
        """
        learning_path = []

        # Find dimensions below team baseline, ordered by gap size
        gaps = []
        for dimension in ALL_DIMENSIONS:
            dev_level = dimension_scores[dimension].maturity_level
            team_avg = team_baseline.get(dimension, 2.0)
            gap = team_avg - dev_level
            if gap > 0:
                gaps.append((dimension, gap, dev_level))

        # Sort by gap size (descending)
        gaps.sort(key=lambda x: x[1], reverse=True)

        # Create learning path from top gaps
        for dimension, gap_size, current_level in gaps[:5]:
            roadmap = roadmaps.get(dimension)
            if roadmap and roadmap.actions:
                first_action = roadmap.actions[0]
                learning_path.append(
                    f"Develop {dimension} (L{current_level}→L{int(current_level + 1)}: {first_action.title})"
                )

        return learning_path

    def _generate_executive_summary(
        self, developer_id: str, overall_maturity: float, fit_with_baseline: str
    ) -> str:
        """
        Generate developer-focused executive summary.

        Args:
            developer_id: Developer identifier
            overall_maturity: Developer's overall maturity level
            fit_with_baseline: Baseline comparison statement

        Returns:
            Executive summary narrative
        """
        summary = f"{developer_id} demonstrates L{overall_maturity:.1f}/4.0 personal AI maturity. "
        summary += fit_with_baseline + " "
        summary += "Recommended focus: advancing below-average dimensions and consolidating strengths."

        return summary

    def _extract_key_insights(
        self,
        dimension_scores: Dict[str, DimensionScore],
        team_baseline: Dict[str, float],
    ) -> List[str]:
        """
        Extract key findings about this developer.

        Args:
            dimension_scores: Dict of DimensionScore objects
            team_baseline: Dict of team average scores

        Returns:
            List of key insight strings
        """
        insights = []

        # Insight 1: Specialization
        high_dims = [
            d for d, score in dimension_scores.items()
            if score.maturity_level >= 3
        ]
        if high_dims:
            insights.append(f"Advanced skills: {', '.join(sorted(high_dims)[:2])}")

        # Insight 2: Comparison
        dev_avg = sum(score.maturity_level for score in dimension_scores.values()) / len(dimension_scores)
        team_avg = sum(team_baseline.values()) / len(team_baseline)
        if dev_avg > team_avg:
            insights.append("Strong performer relative to team")
        elif dev_avg < team_avg:
            insights.append("Growth opportunity relative to team")

        # Insight 3: Consistency
        levels = [score.maturity_level for score in dimension_scores.values()]
        consistency = max(levels) - min(levels)
        if consistency <= 1:
            insights.append("Consistent skills across all dimensions")
        else:
            insights.append("Varied specialization across dimensions")

        return insights[:5]

    def _generate_personalized_recommendations(
        self,
        dimension_scores: Dict[str, DimensionScore],
        team_baseline: Dict[str, float],
        roadmaps: Dict[str, RoadmapItem],
    ) -> List[str]:
        """
        Generate individual-specific actions.

        Args:
            dimension_scores: Dict of DimensionScore objects
            team_baseline: Dict of team average scores
            roadmaps: Dict of RoadmapItem objects

        Returns:
            List of personalized recommendation strings
        """
        recommendations = []

        # Find top 3 below-baseline dimensions for focused growth
        gaps = []
        for dimension in ALL_DIMENSIONS:
            dev_level = dimension_scores[dimension].maturity_level
            team_avg = team_baseline.get(dimension, 2.0)
            if dev_level < team_avg:
                gaps.append((dimension, team_avg - dev_level))

        gaps.sort(key=lambda x: x[1], reverse=True)

        for dimension, gap in gaps[:3]:
            roadmap = roadmaps.get(dimension)
            if roadmap and roadmap.actions:
                first_action = roadmap.actions[0]
                recommendations.append(
                    f"Focus on {dimension}: {first_action.title}"
                )

        # Find quick wins (L1→L2 in dimensions at L1)
        l1_dims = [d for d, score in dimension_scores.items() if score.maturity_level == 1]
        for dim in sorted(l1_dims)[:1]:
            roadmap = roadmaps.get(dim)
            if roadmap and roadmap.total_effort_hours <= 16:
                recommendations.append(
                    f"Quick win: Advance {dim} from L1 to L2 ({roadmap.total_effort_hours}h estimated)"
                )

        # Consolidation
        high_dims = [
            d for d, score in dimension_scores.items()
            if score.maturity_level >= 3
        ]
        if high_dims:
            recommendations.append(
                f"Consolidate strengths in {high_dims[0]} to prepare for peer mentoring"
            )

        return recommendations[:5]
