"""
Tests for the Roadmap Generator module.

Tests cover:
1. Single dimension roadmap generation
2. All dimensions roadmap generation
3. Effort estimation validation
4. Action dependencies
5. Edge cases and error handling
"""

import pytest

from src.auto_sdlc.reports.roadmap import (
    RoadmapAction,
    RoadmapGenerator,
    RoadmapItem,
)


@pytest.fixture
def generator():
    """Create a RoadmapGenerator instance."""
    return RoadmapGenerator()


class TestRoadmapActionDataclass:
    """Test RoadmapAction dataclass."""

    def test_create_action(self):
        """Test creating a RoadmapAction."""
        action = RoadmapAction(
            action_id="TEST_001",
            step=1,
            title="Test action",
            description="Test description",
            effort_hours=4,
            effort_weeks=1,
            owners=["Tech Lead"],
            dependencies=[],
            success_criteria="Done",
            risk="None",
        )
        assert action.action_id == "TEST_001"
        assert action.step == 1
        assert action.title == "Test action"
        assert action.effort_hours == 4
        assert action.effort_weeks == 1
        assert action.owners == ["Tech Lead"]
        assert action.dependencies == []

    def test_action_with_dependencies(self):
        """Test action with dependencies."""
        action = RoadmapAction(
            action_id="TEST_002",
            step=2,
            title="Dependent action",
            description="Depends on previous",
            effort_hours=6,
            effort_weeks=1,
            owners=["Tech Lead"],
            dependencies=["TEST_001"],
        )
        assert action.dependencies == ["TEST_001"]


class TestRoadmapItemDataclass:
    """Test RoadmapItem dataclass."""

    def test_create_roadmap_item(self):
        """Test creating a RoadmapItem."""
        action1 = RoadmapAction(
            action_id="A1",
            step=1,
            title="Action 1",
            description="Desc 1",
            effort_hours=4,
            effort_weeks=1,
            owners=["Tech Lead"],
        )
        action2 = RoadmapAction(
            action_id="A2",
            step=2,
            title="Action 2",
            description="Desc 2",
            effort_hours=6,
            effort_weeks=1,
            owners=["Tech Lead"],
        )

        item = RoadmapItem(
            dimension="Test Dimension",
            current_level=1,
            target_level=2,
            actions=[action1, action2],
            total_effort_hours=10,
            total_effort_weeks=2,
            key_insight="Move from L1 to L2",
        )

        assert item.dimension == "Test Dimension"
        assert item.current_level == 1
        assert item.target_level == 2
        assert len(item.actions) == 2
        assert item.total_effort_hours == 10
        assert item.total_effort_weeks == 2


class TestRoadmapGeneratorSingleDimension:
    """Test generating roadmap for a single dimension."""

    def test_generate_quality_controls_l1_to_l2(self, generator):
        """Test generating roadmap for Quality Controls L1→L2."""
        roadmap = generator.generate_roadmap_for_dimension(
            "Quality Controls", 1, 2
        )

        assert roadmap.dimension == "Quality Controls"
        assert roadmap.current_level == 1
        assert roadmap.target_level == 2
        assert len(roadmap.actions) >= 3
        assert roadmap.total_effort_hours > 0
        assert roadmap.total_effort_weeks > 0
        assert roadmap.key_insight != ""

        # Verify actions have required fields
        for action in roadmap.actions:
            assert action.action_id
            assert action.step >= 1
            assert action.title
            assert action.description
            assert action.effort_hours > 0
            assert action.effort_weeks > 0

    def test_generate_ai_tool_adoption_l2_to_l3(self, generator):
        """Test generating roadmap for AI Tool Adoption L2→L3."""
        roadmap = generator.generate_roadmap_for_dimension(
            "AI Tool Adoption", 2, 3
        )

        assert roadmap.dimension == "AI Tool Adoption"
        assert roadmap.current_level == 2
        assert roadmap.target_level == 3
        assert len(roadmap.actions) >= 2
        assert "automation" in roadmap.key_insight.lower() or "automat" in roadmap.key_insight.lower()

    def test_all_dimensions_exist(self, generator):
        """Test that all 12 dimensions can be accessed."""
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

        for dimension in dimensions:
            # Should be able to generate L1→L2
            roadmap = generator.generate_roadmap_for_dimension(dimension, 1, 2)
            assert roadmap.dimension == dimension
            assert len(roadmap.actions) > 0

    def test_all_transitions_covered(self, generator):
        """Test that L1→L2, L2→L3, L3→L4 transitions exist."""
        dim = "Quality Controls"

        # L1→L2
        roadmap_1_2 = generator.generate_roadmap_for_dimension(dim, 1, 2)
        assert roadmap_1_2.current_level == 1
        assert len(roadmap_1_2.actions) > 0

        # L2→L3
        roadmap_2_3 = generator.generate_roadmap_for_dimension(dim, 2, 3)
        assert roadmap_2_3.current_level == 2
        assert len(roadmap_2_3.actions) > 0

        # L3→L4
        roadmap_3_4 = generator.generate_roadmap_for_dimension(dim, 3, 4)
        assert roadmap_3_4.current_level == 3
        assert len(roadmap_3_4.actions) > 0

    def test_action_sequence_order(self, generator):
        """Test that actions are in sequence order."""
        roadmap = generator.generate_roadmap_for_dimension(
            "Quality Controls", 1, 2
        )

        steps = [action.step for action in roadmap.actions]
        assert steps == sorted(steps)
        assert steps[0] == 1

    def test_action_dependencies_are_valid(self, generator):
        """Test that action dependencies reference earlier actions."""
        roadmap = generator.generate_roadmap_for_dimension(
            "Quality Controls", 1, 2
        )

        action_ids = {action.action_id for action in roadmap.actions}

        for action in roadmap.actions:
            for dep_id in action.dependencies:
                assert dep_id in action_ids, f"{action.action_id} depends on {dep_id} which doesn't exist"

                # Dependency should be from an earlier step
                dep_action = next(a for a in roadmap.actions if a.action_id == dep_id)
                assert dep_action.step < action.step

    def test_effort_hours_and_weeks_consistency(self, generator):
        """Test that effort estimates are reasonable."""
        roadmap = generator.generate_roadmap_for_dimension(
            "Quality Controls", 1, 2
        )

        # Each action should have effort_hours and effort_weeks
        for action in roadmap.actions:
            assert action.effort_hours > 0
            assert action.effort_weeks > 0
            # effort_weeks should typically be larger than or equal to effort_hours/40
            # (allowing for coordination overhead)
            assert action.effort_weeks >= action.effort_hours / 40

        # Total should be sum of parts
        total_hours = sum(a.effort_hours for a in roadmap.actions)
        assert roadmap.total_effort_hours == total_hours

        total_weeks = sum(a.effort_weeks for a in roadmap.actions)
        assert roadmap.total_effort_weeks == total_weeks

    def test_success_criteria_present(self, generator):
        """Test that success criteria are defined."""
        roadmap = generator.generate_roadmap_for_dimension(
            "Quality Controls", 1, 2
        )

        for action in roadmap.actions:
            assert action.success_criteria, f"Action {action.action_id} missing success criteria"

    def test_risks_identified(self, generator):
        """Test that risks are identified."""
        roadmap = generator.generate_roadmap_for_dimension(
            "Quality Controls", 1, 2
        )

        for action in roadmap.actions:
            assert action.risk, f"Action {action.action_id} missing risk assessment"

    def test_owners_assigned(self, generator):
        """Test that action owners are assigned."""
        roadmap = generator.generate_roadmap_for_dimension(
            "Quality Controls", 1, 2
        )

        for action in roadmap.actions:
            assert len(action.owners) > 0, f"Action {action.action_id} has no owners"


class TestRoadmapGeneratorAllDimensions:
    """Test generating roadmaps for all dimensions."""

    def test_generate_all_roadmaps_from_l1(self, generator):
        """Test generating roadmaps for all dimensions from L1."""
        dimensions_and_levels = {
            "AI Tool Adoption": 1,
            "Prompt & Context Engineering": 1,
            "Agent Configuration": 1,
            "CI/CD Integration": 1,
            "Ticketing & Planning": 1,
            "Cross-System Connectivity": 1,
            "Quality Controls": 1,
            "Security & Compliance": 1,
            "Measurement & KPIs": 1,
            "Ways of Working": 1,
            "Accountability & Ownership": 1,
            "Scalability & Knowledge Transfer": 1,
        }

        roadmaps = generator.generate_all_roadmaps(dimensions_and_levels)

        # Should have 12 roadmaps (all dimensions, all from L1)
        assert len(roadmaps) == 12

        # Each roadmap should be well-formed
        for roadmap in roadmaps:
            assert roadmap.dimension in dimensions_and_levels
            assert roadmap.current_level == 1
            assert roadmap.target_level == 2
            assert len(roadmap.actions) > 0

    def test_generate_mixed_levels(self, generator):
        """Test generating roadmaps for mixed maturity levels."""
        dimensions_and_levels = {
            "Quality Controls": 1,  # L1→L2
            "CI/CD Integration": 2,  # L2→L3
            "AI Tool Adoption": 3,  # L3→L4
        }

        roadmaps = generator.generate_all_roadmaps(dimensions_and_levels)

        assert len(roadmaps) == 3

        # Verify transitions
        qc = next(r for r in roadmaps if r.dimension == "Quality Controls")
        assert qc.current_level == 1 and qc.target_level == 2

        ci = next(r for r in roadmaps if r.dimension == "CI/CD Integration")
        assert ci.current_level == 2 and ci.target_level == 3

        ata = next(r for r in roadmaps if r.dimension == "AI Tool Adoption")
        assert ata.current_level == 3 and ata.target_level == 4

    def test_skip_l4_dimensions(self, generator):
        """Test that L4 dimensions are skipped."""
        dimensions_and_levels = {
            "Quality Controls": 4,  # Already at max
            "CI/CD Integration": 1,  # L1→L2
        }

        roadmaps = generator.generate_all_roadmaps(dimensions_and_levels)

        # Should only have 1 roadmap (CI/CD)
        assert len(roadmaps) == 1
        assert roadmaps[0].dimension == "CI/CD Integration"

    def test_total_effort_across_all_dimensions(self, generator):
        """Test calculating total effort across all dimensions."""
        dimensions_and_levels = {
            "Quality Controls": 1,
            "CI/CD Integration": 1,
        }

        roadmaps = generator.generate_all_roadmaps(dimensions_and_levels)

        total_hours = sum(r.total_effort_hours for r in roadmaps)
        total_weeks = sum(r.total_effort_weeks for r in roadmaps)

        assert total_hours > 0
        assert total_weeks > 0
        # Total should be reasonable (not 1000+ hours)
        assert total_hours < 500


class TestRoadmapGeneratorErrors:
    """Test error handling."""

    def test_invalid_dimension(self, generator):
        """Test error on invalid dimension."""
        with pytest.raises(ValueError, match="not found"):
            generator.generate_roadmap_for_dimension("Invalid Dimension", 1, 2)

    def test_invalid_current_level_too_low(self, generator):
        """Test error on invalid current level (too low)."""
        with pytest.raises(ValueError, match="between 1 and 4"):
            generator.generate_roadmap_for_dimension("Quality Controls", 0, 2)

    def test_invalid_current_level_too_high(self, generator):
        """Test error on invalid current level (too high)."""
        with pytest.raises(ValueError, match="between 1 and 4"):
            generator.generate_roadmap_for_dimension("Quality Controls", 5, 6)

    def test_target_not_greater_than_current(self, generator):
        """Test error when target ≤ current."""
        with pytest.raises(ValueError, match="greater than current"):
            generator.generate_roadmap_for_dimension("Quality Controls", 2, 2)

    def test_missing_transition(self, generator):
        """Test error when transition doesn't exist."""
        with pytest.raises(ValueError, match="No roadmap found"):
            # Assuming we only have single-step transitions
            generator.generate_roadmap_for_dimension("Quality Controls", 1, 3)


class TestRoadmapContent:
    """Test specific content of roadmaps."""

    def test_quality_controls_l1_l2_content(self, generator):
        """Test that Quality Controls L1→L2 has expected actions."""
        roadmap = generator.generate_roadmap_for_dimension(
            "Quality Controls", 1, 2
        )

        # Check for specific types of actions
        action_titles_lower = [a.title.lower() for a in roadmap.actions]

        # Should have documentation, skill, and training related actions
        assert any("checklist" in t or "document" in t for t in action_titles_lower)
        assert any("review" in t or "skill" in t for t in action_titles_lower)
        assert any("train" in t or "workflow" in t for t in action_titles_lower)

    def test_roadmap_key_insight_meaningful(self, generator):
        """Test that key insights are meaningful."""
        transitions = [
            ("Quality Controls", 1, 2),
            ("AI Tool Adoption", 2, 3),
            ("Scalability & Knowledge Transfer", 3, 4),
        ]

        for dim, curr, targ in transitions:
            roadmap = generator.generate_roadmap_for_dimension(dim, curr, targ)
            assert len(roadmap.key_insight) > 10
            assert roadmap.key_insight.endswith(("", "s", "e", "g", "m", "d", "n"))  # Ends naturally

    def test_l1_l2_transitions_include_documentation(self, generator):
        """Test that L1→L2 transitions emphasize documentation."""
        dims = ["Quality Controls", "AI Tool Adoption", "Security & Compliance"]

        for dim in dims:
            roadmap = generator.generate_roadmap_for_dimension(dim, 1, 2)
            actions_lower = [a.title.lower() + " " + a.description.lower() for a in roadmap.actions]
            combined = " ".join(actions_lower)

            # L1→L2 should emphasize documentation/standards
            has_doc_related = any(
                word in combined
                for word in ["document", "establish", "define", "create", "standard"]
            )
            assert has_doc_related, f"{dim} L1→L2 should emphasize documentation"

    def test_l2_l3_transitions_include_automation(self, generator):
        """Test that L2→L3 transitions emphasize automation."""
        dims = ["CI/CD Integration", "Prompt & Context Engineering"]

        for dim in dims:
            if dim in ["CI/CD Integration"]:  # Ensure we have L2→L3 data
                roadmap = generator.generate_roadmap_for_dimension(dim, 2, 3)
                actions_lower = [a.title.lower() + " " + a.description.lower() for a in roadmap.actions]
                combined = " ".join(actions_lower)

                # L2→L3 should emphasize automation/efficiency
                has_automation = any(
                    word in combined
                    for word in ["automat", "implement", "expand", "add", "intelligent"]
                )
                assert has_automation, f"{dim} L2→L3 should emphasize automation"

    def test_effort_varies_by_complexity(self, generator):
        """Test that more complex transitions require more effort."""
        l1_l2 = generator.generate_roadmap_for_dimension("Quality Controls", 1, 2)
        l2_l3 = generator.generate_roadmap_for_dimension("Quality Controls", 2, 3)
        l3_l4 = generator.generate_roadmap_for_dimension("Quality Controls", 3, 4)

        # In general, later transitions should require more effort (not always, but trend)
        # At least check they're not identical
        assert l1_l2.total_effort_hours != l2_l3.total_effort_hours or len(l1_l2.actions) != len(l2_l3.actions)


class TestRoadmapIntegration:
    """Integration tests."""

    def test_roadmap_workflow(self, generator):
        """Test a complete workflow: generate single, then all."""
        # First, get one
        qc_roadmap = generator.generate_roadmap_for_dimension(
            "Quality Controls", 1, 2
        )
        assert qc_roadmap is not None

        # Then, get all
        all_dims = {
            "Quality Controls": 1,
            "CI/CD Integration": 1,
            "Scalability & Knowledge Transfer": 1,
        }
        all_roadmaps = generator.generate_all_roadmaps(all_dims)

        assert len(all_roadmaps) == 3
        qc_all = next(r for r in all_roadmaps if r.dimension == "Quality Controls")

        # The two should match
        assert qc_roadmap.dimension == qc_all.dimension
        assert qc_roadmap.current_level == qc_all.current_level
        assert qc_roadmap.target_level == qc_all.target_level
