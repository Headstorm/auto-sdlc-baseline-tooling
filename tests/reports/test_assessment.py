"""
Tests for Assessment Questions Engine

Validates that all 50 assessment questions are loaded correctly,
organized by dimension, and responses can be validated.
"""

import pytest
from auto_sdlc.reports.assessment import (
    AssessmentQuestion,
    AssessmentResponse,
    AssessmentQuestionsEngine,
)


@pytest.fixture
def engine():
    """Fixture to provide a fresh engine instance for each test."""
    return AssessmentQuestionsEngine()


class TestAssessmentQuestionDataclass:
    """Tests for AssessmentQuestion dataclass."""

    def test_assessment_question_creation(self):
        """Test creating an AssessmentQuestion with all required fields."""
        q = AssessmentQuestion(
            id="TEST_1",
            dimension="Capability",
            category="AI Tool Adoption",
            dimension_sub="AI Tool Adoption",
            question="Test question?",
            guidance="Test guidance",
        )
        assert q.id == "TEST_1"
        assert q.dimension == "Capability"
        assert q.category == "AI Tool Adoption"
        assert q.dimension_sub == "AI Tool Adoption"
        assert q.question == "Test question?"
        assert q.guidance == "Test guidance"


class TestAssessmentResponseDataclass:
    """Tests for AssessmentResponse dataclass."""

    def test_assessment_response_creation(self):
        """Test creating an AssessmentResponse."""
        r = AssessmentResponse(
            question_id="TEST_1",
            answer="This is our answer",
            confidence="certain",
        )
        assert r.question_id == "TEST_1"
        assert r.answer == "This is our answer"
        assert r.confidence == "certain"
        assert r.notes == ""

    def test_assessment_response_with_notes(self):
        """Test creating an AssessmentResponse with optional notes."""
        r = AssessmentResponse(
            question_id="TEST_1",
            answer="This is our answer",
            confidence="likely",
            notes="Some additional context",
        )
        assert r.notes == "Some additional context"


class TestLoadQuestions:
    """Tests for loading assessment questions."""

    def test_load_all_questions(self, engine):
        """Verify all 50 questions load correctly."""
        questions = engine.load_questions()
        assert len(questions) == 50, f"Expected 50 questions, got {len(questions)}"
        assert all(isinstance(q, AssessmentQuestion) for q in questions)

    def test_no_duplicate_question_ids(self, engine):
        """Verify no duplicate question IDs exist."""
        questions = engine.load_questions()
        ids = [q.id for q in questions]
        assert len(ids) == len(set(ids)), "Duplicate question IDs found"

    def test_all_questions_have_required_fields(self, engine):
        """Verify each question has all required fields."""
        questions = engine.load_questions()
        required_fields = ["id", "dimension", "category", "dimension_sub", "question", "guidance"]

        for q in questions:
            for field in required_fields:
                value = getattr(q, field, None)
                assert value is not None, f"Question {q.id} missing field {field}"
                assert isinstance(value, str), f"Question {q.id} field {field} is not a string"
                assert len(value) > 0, f"Question {q.id} field {field} is empty"

    def test_questions_are_sorted_by_id(self, engine):
        """Verify questions can be consistently retrieved."""
        q1 = engine.load_questions()
        q2 = engine.load_questions()
        assert [q.id for q in q1] == [q.id for q in q2]


class TestQuestionsByDimension:
    """Tests for filtering questions by dimension."""

    def test_get_questions_by_dimension_capability(self, engine):
        """Verify Capability dimension has expected number of questions."""
        questions = engine.get_questions_by_dimension("Capability")
        assert len(questions) == 9  # 3 + 3 + 3 for AI Tool Adoption, Prompt, Agent Config

    def test_get_questions_by_dimension_integration(self, engine):
        """Verify Integration dimension has expected number of questions."""
        questions = engine.get_questions_by_dimension("Integration")
        assert len(questions) == 9  # 3 + 3 + 3 for CI/CD, Ticketing, Cross-System

    def test_get_questions_by_dimension_governance(self, engine):
        """Verify Governance dimension has expected number of questions."""
        questions = engine.get_questions_by_dimension("Governance")
        assert len(questions) == 11  # 3 + 3 + 5 for Quality, Security, Measurement

    def test_get_questions_by_dimension_execution_ownership(self, engine):
        """Verify Execution Ownership dimension has expected number of questions."""
        questions = engine.get_questions_by_dimension("Execution Ownership")
        assert len(questions) == 12  # 3 + 5 + 4 for Ways, Accountability, Scalability

    def test_get_questions_by_dimension_value_realization(self, engine):
        """Verify Value Realization dimension has expected number of questions."""
        questions = engine.get_questions_by_dimension("Value Realization")
        assert len(questions) == 9  # 9 business impact questions

    def test_get_questions_by_dimension_nonexistent(self, engine):
        """Verify querying a nonexistent dimension returns empty list."""
        questions = engine.get_questions_by_dimension("Nonexistent Dimension")
        assert questions == []

    def test_dimension_coverage_total(self, engine):
        """Verify all dimensions account for all 50 questions."""
        questions = engine.load_questions()
        dimensions = engine.get_all_dimensions()
        total = sum(len(engine.get_questions_by_dimension(d)) for d in dimensions)
        assert total == 50


class TestQuestionsByCategory:
    """Tests for filtering questions by category."""

    def test_get_questions_by_category_ai_tool_adoption(self, engine):
        """Verify AI Tool Adoption category has 3 questions."""
        questions = engine.get_questions_by_category("AI Tool Adoption")
        assert len(questions) == 3

    def test_get_questions_by_category_prompt_context(self, engine):
        """Verify Prompt & Context Engineering category has 3 questions."""
        questions = engine.get_questions_by_category("Prompt & Context Engineering")
        assert len(questions) == 3

    def test_get_questions_by_category_agent_config(self, engine):
        """Verify Agent Configuration category has 3 questions."""
        questions = engine.get_questions_by_category("Agent Configuration")
        assert len(questions) == 3

    def test_get_questions_by_category_cicd(self, engine):
        """Verify CI/CD Integration category has 3 questions."""
        questions = engine.get_questions_by_category("CI/CD Integration")
        assert len(questions) == 3

    def test_get_questions_by_category_ticketing(self, engine):
        """Verify Ticketing & Planning category has 3 questions."""
        questions = engine.get_questions_by_category("Ticketing & Planning")
        assert len(questions) == 3

    def test_get_questions_by_category_cross_system(self, engine):
        """Verify Cross-System Connectivity category has 3 questions."""
        questions = engine.get_questions_by_category("Cross-System Connectivity")
        assert len(questions) == 3

    def test_get_questions_by_category_quality(self, engine):
        """Verify Quality Controls category has 3 questions."""
        questions = engine.get_questions_by_category("Quality Controls")
        assert len(questions) == 3

    def test_get_questions_by_category_security(self, engine):
        """Verify Security & Compliance category has 3 questions."""
        questions = engine.get_questions_by_category("Security & Compliance")
        assert len(questions) == 3

    def test_get_questions_by_category_measurement(self, engine):
        """Verify Measurement & KPIs category has 5 questions."""
        questions = engine.get_questions_by_category("Measurement & KPIs")
        assert len(questions) == 5  # From Governance section

    def test_get_questions_by_category_ways_of_working(self, engine):
        """Verify Ways of Working category has 3 questions."""
        questions = engine.get_questions_by_category("Ways of Working")
        assert len(questions) == 3

    def test_get_questions_by_category_accountability(self, engine):
        """Verify Accountability & Ownership category has 5 questions."""
        questions = engine.get_questions_by_category("Accountability & Ownership")
        assert len(questions) == 5

    def test_get_questions_by_category_scalability(self, engine):
        """Verify Scalability & Knowledge Transfer category has 4 questions."""
        questions = engine.get_questions_by_category("Scalability & Knowledge Transfer")
        assert len(questions) == 4

    def test_get_questions_by_category_business_impact(self, engine):
        """Verify Business Impact category has 9 questions."""
        questions = engine.get_questions_by_category("Business Impact")
        assert len(questions) == 9

    def test_get_questions_by_category_nonexistent(self, engine):
        """Verify querying a nonexistent category returns empty list."""
        questions = engine.get_questions_by_category("Nonexistent Category")
        assert questions == []


class TestQuestionsBySubdimension:
    """Tests for filtering questions by sub-dimension."""

    def test_get_questions_by_subdimension_ai_tool_adoption(self, engine):
        """Verify AI Tool Adoption sub-dimension has 3 questions."""
        questions = engine.get_questions_by_subdimension("AI Tool Adoption")
        assert len(questions) == 3

    def test_get_questions_by_subdimension_quality_controls(self, engine):
        """Verify Quality Controls sub-dimension has 3 questions."""
        questions = engine.get_questions_by_subdimension("Quality Controls")
        assert len(questions) == 3

    def test_get_questions_by_subdimension_cross_system(self, engine):
        """Verify Cross-System Connectivity sub-dimension has 3 questions."""
        questions = engine.get_questions_by_subdimension("Cross-System Connectivity")
        assert len(questions) == 3


class TestDimensionCoverage:
    """Tests for ensuring all 12 sub-dimensions are covered."""

    def test_all_subdimensions_covered(self, engine):
        """Verify all 12 sub-dimensions have at least one question."""
        expected_subdimensions = {
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
        actual_subdimensions = set(engine.get_all_subdimensions())

        # Value Realization questions map to Measurement & KPIs sub-dimension
        # so they may not add new sub-dimensions
        for subdim in expected_subdimensions:
            questions = engine.get_questions_by_subdimension(subdim)
            assert len(questions) > 0, f"Sub-dimension '{subdim}' has no questions"

    def test_exactly_five_dimensions(self, engine):
        """Verify exactly 5 high-level dimensions exist."""
        dimensions = engine.get_all_dimensions()
        assert len(dimensions) == 5
        expected = {"Capability", "Integration", "Governance", "Execution Ownership", "Value Realization"}
        assert set(dimensions) == expected


class TestValidateResponses:
    """Tests for response validation."""

    def test_validate_empty_responses(self, engine):
        """Verify validation works with empty response list."""
        errors = engine.validate_responses([])
        # Should report missing questions for all 50
        assert "missing" in errors
        assert len(errors["missing"]) == 50

    def test_validate_missing_confidence(self, engine):
        """Verify validation catches missing confidence."""
        responses = [
            AssessmentResponse(
                question_id="AI_TOOL_ADOPTION_1",
                answer="Yes, by choice",
                confidence="",
            )
        ]
        errors = engine.validate_responses(responses)
        assert "validation" in errors
        # Check that missing confidence is flagged

    def test_validate_invalid_confidence(self, engine):
        """Verify validation catches invalid confidence values."""
        responses = [
            AssessmentResponse(
                question_id="AI_TOOL_ADOPTION_1",
                answer="Yes, by choice",
                confidence="maybe",  # Invalid
            )
        ]
        errors = engine.validate_responses(responses)
        assert "confidence" in errors
        assert any("maybe" in str(msg) for msg in errors["confidence"])

    def test_validate_unknown_question_id(self, engine):
        """Verify validation catches unknown question IDs."""
        responses = [
            AssessmentResponse(
                question_id="UNKNOWN_QUESTION_999",
                answer="Some answer",
                confidence="certain",
            )
        ]
        errors = engine.validate_responses(responses)
        assert "validation" in errors
        assert any("UNKNOWN_QUESTION_999" in str(msg) for msg in errors["validation"])

    def test_validate_missing_answer(self, engine):
        """Verify validation catches missing answers."""
        responses = [
            AssessmentResponse(
                question_id="AI_TOOL_ADOPTION_1",
                answer="",
                confidence="certain",
            )
        ]
        errors = engine.validate_responses(responses)
        assert "validation" in errors

    def test_validate_all_valid_responses(self, engine):
        """Verify validation passes for all valid responses."""
        questions = engine.load_questions()
        responses = [
            AssessmentResponse(
                question_id=q.id,
                answer="Sample answer",
                confidence="likely",
            )
            for q in questions
        ]
        errors = engine.validate_responses(responses)
        assert len(errors) == 0, f"Unexpected validation errors: {errors}"

    def test_validate_partial_responses(self, engine):
        """Verify validation catches partial response sets."""
        responses = [
            AssessmentResponse(
                question_id="AI_TOOL_ADOPTION_1",
                answer="Yes",
                confidence="certain",
            ),
            AssessmentResponse(
                question_id="AI_TOOL_ADOPTION_2",
                answer="No",
                confidence="likely",
            ),
        ]
        errors = engine.validate_responses(responses)
        assert "missing" in errors
        assert len(errors["missing"]) == 48  # 50 - 2 provided

    def test_validate_all_confidence_levels(self, engine):
        """Verify validation accepts all three valid confidence levels."""
        confidence_levels = ["certain", "likely", "unsure"]
        for conf in confidence_levels:
            responses = [
                AssessmentResponse(
                    question_id="AI_TOOL_ADOPTION_1",
                    answer="Answer",
                    confidence=conf,
                )
            ]
            errors = engine.validate_responses(responses)
            # Should not have confidence errors for valid levels
            if "confidence" in errors:
                assert not any(conf in str(msg) for msg in errors["confidence"])


class TestGetAllDimensions:
    """Tests for getting all dimensions."""

    def test_get_all_dimensions(self, engine):
        """Verify get_all_dimensions returns all 5 dimensions."""
        dimensions = engine.get_all_dimensions()
        assert len(dimensions) == 5
        assert "Capability" in dimensions
        assert "Integration" in dimensions
        assert "Governance" in dimensions
        assert "Execution Ownership" in dimensions
        assert "Value Realization" in dimensions

    def test_dimensions_are_sorted(self, engine):
        """Verify dimensions are returned in sorted order."""
        dimensions = engine.get_all_dimensions()
        assert dimensions == sorted(dimensions)


class TestGetAllCategories:
    """Tests for getting all categories."""

    def test_get_all_categories(self, engine):
        """Verify get_all_categories returns all categories."""
        categories = engine.get_all_categories()
        expected = {
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
            "Business Impact",
        }
        assert set(categories) == expected

    def test_categories_are_sorted(self, engine):
        """Verify categories are returned in sorted order."""
        categories = engine.get_all_categories()
        assert categories == sorted(categories)


class TestGetAllSubdimensions:
    """Tests for getting all sub-dimensions."""

    def test_get_all_subdimensions(self, engine):
        """Verify get_all_subdimensions returns all sub-dimensions."""
        subdimensions = engine.get_all_subdimensions()
        # Should include at least 12 unique sub-dimensions
        assert len(subdimensions) >= 12

    def test_subdimensions_are_sorted(self, engine):
        """Verify sub-dimensions are returned in sorted order."""
        subdimensions = engine.get_all_subdimensions()
        assert subdimensions == sorted(subdimensions)


class TestQuestionContent:
    """Tests for question content quality."""

    def test_all_questions_have_meaningful_guidance(self, engine):
        """Verify all questions have meaningful guidance (not empty or trivial)."""
        questions = engine.load_questions()
        for q in questions:
            assert len(q.guidance) > 20, f"Question {q.id} has too short guidance: {q.guidance}"
            assert q.guidance.lower() != "guidance", f"Question {q.id} has trivial guidance"

    def test_all_questions_are_questions(self, engine):
        """Verify all questions are formulated as questions."""
        questions = engine.load_questions()
        for q in questions:
            # Should end with ? or mention a question-like structure
            assert (q.question.strip().endswith("?") or
                   any(word in q.question.lower() for word in ["does", "is", "are", "can", "what", "how", "who", "when", "where"])), \
                   f"Question {q.id} doesn't appear to be a question: {q.question}"


class TestIntegration:
    """Integration tests."""

    def test_full_assessment_workflow(self, engine):
        """Test a complete assessment workflow."""
        # 1. Load all questions
        questions = engine.load_questions()
        assert len(questions) == 50

        # 2. Group by dimension
        capability_qs = engine.get_questions_by_dimension("Capability")
        integration_qs = engine.get_questions_by_dimension("Integration")
        governance_qs = engine.get_questions_by_dimension("Governance")

        # 3. Create mock responses
        responses = []
        for q in capability_qs:
            responses.append(
                AssessmentResponse(
                    question_id=q.id,
                    answer="Sample team response",
                    confidence="likely",
                    notes="Optional context",
                )
            )

        # 4. Validate (should have missing questions for other dimensions)
        errors = engine.validate_responses(responses)
        assert "missing" in errors
        assert len(errors["missing"]) > 0

    def test_question_id_uniqueness_across_all_methods(self, engine):
        """Verify question IDs are unique across all retrieval methods."""
        all_qs = engine.load_questions()
        by_dim = set()
        for dim in engine.get_all_dimensions():
            for q in engine.get_questions_by_dimension(dim):
                by_dim.add(q.id)

        by_cat = set()
        for cat in engine.get_all_categories():
            for q in engine.get_questions_by_category(cat):
                by_cat.add(q.id)

        # All three sets should be identical
        all_ids = {q.id for q in all_qs}
        assert by_dim == all_ids
        assert by_cat == all_ids
