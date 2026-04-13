"""
Assessment Questions Engine

Loads and manages the 50 assessment questions from CLAUDE.md,
organized by dimension and category. Provides methods to query
questions by dimension or category, and to validate assessment responses.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AssessmentQuestion:
    """
    Represents a single assessment question.

    Attributes:
        id: Unique identifier (e.g., "AI_TOOL_ADOPTION_1")
        dimension: High-level dimension (Capability, Integration, Governance, Execution, Value)
        category: Section name from CLAUDE.md
        dimension_sub: Specific sub-dimension (e.g., "AI Tool Adoption", "Quality Controls")
        question: The actual question text
        guidance: Guidance on how to assess the answer
    """

    id: str
    dimension: str
    category: str
    dimension_sub: str
    question: str
    guidance: str


@dataclass
class AssessmentResponse:
    """
    Represents a team's response to an assessment question.

    Attributes:
        question_id: References AssessmentQuestion.id
        answer: The team's response text
        confidence: Level of certainty ("certain", "likely", "unsure")
        notes: Optional additional context
    """

    question_id: str
    answer: str
    confidence: str
    notes: str = ""


class AssessmentQuestionsEngine:
    """
    Manages assessment questions and validates responses.

    Loads all 50 assessment questions from CLAUDE.md (Appendix: Assessment Questions by Dimension)
    and provides methods to retrieve questions by dimension, category, or sub-dimension.
    """

    def __init__(self):
        """Initialize the engine and load all assessment questions."""
        self._questions: List[AssessmentQuestion] = []
        self._load_questions()

    def _load_questions(self) -> None:
        """Load all 50 assessment questions from hardcoded data."""
        # SECTION 1: Capability (AI Tools, Context, Agents) - 9 questions
        self._questions.extend([
            # AI Tool Adoption (3 questions)
            AssessmentQuestion(
                id="AI_TOOL_ADOPTION_1",
                dimension="Capability",
                category="AI Tool Adoption",
                dimension_sub="AI Tool Adoption",
                question="Who decides which AI tool to use? By choice or enforcement?",
                guidance="Assess whether tool selection is decentralized (by choice) or centralized (enforcement). Look for clear decision criteria."
            ),
            AssessmentQuestion(
                id="AI_TOOL_ADOPTION_2",
                dimension="Capability",
                category="AI Tool Adoption",
                dimension_sub="AI Tool Adoption",
                question="Are licenses managed centrally? How?",
                guidance="Verify whether the team has a centralized system for license management, approval, and tracking of tool usage."
            ),
            AssessmentQuestion(
                id="AI_TOOL_ADOPTION_3",
                dimension="Capability",
                category="AI Tool Adoption",
                dimension_sub="AI Tool Adoption",
                question="Does the team standardize on 1-2 tools or pick individually?",
                guidance="Measure standardization: check if team converges on fewer tools or if each developer chooses independently."
            ),

            # Prompt & Context Engineering (3 questions)
            AssessmentQuestion(
                id="PROMPT_CONTEXT_1",
                dimension="Capability",
                category="Prompt & Context Engineering",
                dimension_sub="Prompt & Context Engineering",
                question="Does every repo have CLAUDE.md? What does it cover?",
                guidance="Check presence and quality of CLAUDE.md files. Assess whether they cover architecture, conventions, tools, and context loading."
            ),
            AssessmentQuestion(
                id="PROMPT_CONTEXT_2",
                dimension="Capability",
                category="Prompt & Context Engineering",
                dimension_sub="Prompt & Context Engineering",
                question="Are prompt templates shared? How often reused?",
                guidance="Evaluate whether the team maintains shared prompt templates and how frequently developers reuse them vs. starting from scratch."
            ),
            AssessmentQuestion(
                id="PROMPT_CONTEXT_3",
                dimension="Capability",
                category="Prompt & Context Engineering",
                dimension_sub="Prompt & Context Engineering",
                question="How do developers load context at session start?",
                guidance="Assess context loading practices: do they load CLAUDE.md? Load files? Use agent commands? Is there a standard approach?"
            ),

            # Agent Configuration (3 questions)
            AssessmentQuestion(
                id="AGENT_CONFIG_1",
                dimension="Capability",
                category="Agent Configuration",
                dimension_sub="Agent Configuration",
                question="How many custom slash commands exist? (/review, /commit, /plan, etc.?)",
                guidance="Count custom agents/commands. Check if they are documented, maintained, and aligned with team needs."
            ),
            AssessmentQuestion(
                id="AGENT_CONFIG_2",
                dimension="Capability",
                category="Agent Configuration",
                dimension_sub="Agent Configuration",
                question="Are agents multi-step or single-function?",
                guidance="Assess agent sophistication: do they handle complex workflows or single discrete tasks? Look for AGENTS.md documentation."
            ),
            AssessmentQuestion(
                id="AGENT_CONFIG_3",
                dimension="Capability",
                category="Agent Configuration",
                dimension_sub="Agent Configuration",
                question="Who maintains agent code?",
                guidance="Verify ownership: is there a designated maintainer? Is agent code reviewed? Is maintenance documented?"
            ),
        ])

        # SECTION 2: Integration (CI/CD, Tickets, Connectivity) - 9 questions
        self._questions.extend([
            # CI/CD Integration (3 questions)
            AssessmentQuestion(
                id="CICD_INTEGRATION_1",
                dimension="Integration",
                category="CI/CD Integration",
                dimension_sub="CI/CD Integration",
                question="Does every PR get AI review before human review?",
                guidance="Check whether /review or similar is a mandatory gate. Is it enforced or optional?"
            ),
            AssessmentQuestion(
                id="CICD_INTEGRATION_2",
                dimension="Integration",
                category="CI/CD Integration",
                dimension_sub="CI/CD Integration",
                question="Are test suites generated automatically or manually?",
                guidance="Assess whether AI generation of tests is automated in CI/CD or manually triggered. Check adoption rate and coverage."
            ),
            AssessmentQuestion(
                id="CICD_INTEGRATION_3",
                dimension="Integration",
                category="CI/CD Integration",
                dimension_sub="CI/CD Integration",
                question="How many AI review layers exist?",
                guidance="Count sequential AI review steps: linting, type checking, code review, test generation, security scan."
            ),

            # Ticketing & Planning (3 questions)
            AssessmentQuestion(
                id="TICKETING_PLANNING_1",
                dimension="Integration",
                category="Ticketing & Planning",
                dimension_sub="Ticketing & Planning",
                question="Do developers validate ticket quality with AI before starting?",
                guidance="Check if teams use AI to refine issues/tickets before work begins. Is there a documented process?"
            ),
            AssessmentQuestion(
                id="TICKETING_PLANNING_2",
                dimension="Integration",
                category="Ticketing & Planning",
                dimension_sub="Ticketing & Planning",
                question="Are tickets structured with sufficient context for AI and humans?",
                guidance="Assess ticket quality: do they include acceptance criteria, edge cases, relevant links, and structured context?"
            ),
            AssessmentQuestion(
                id="TICKETING_PLANNING_3",
                dimension="Integration",
                category="Ticketing & Planning",
                dimension_sub="Ticketing & Planning",
                question="Does AI enrich issues with acceptance criteria or edge cases?",
                guidance="Check if AI is used to enhance issues with additional validation scenarios or acceptance criteria."
            ),

            # Cross-System Connectivity (3 questions)
            AssessmentQuestion(
                id="CROSS_SYSTEM_1",
                dimension="Integration",
                category="Cross-System Connectivity",
                dimension_sub="Cross-System Connectivity",
                question="Is AI connected to Git, JIRA, Slack, Confluence, docs?",
                guidance="Inventory MCP integrations and AI tool connections. Which systems are integrated? Which are planned?"
            ),
            AssessmentQuestion(
                id="CROSS_SYSTEM_2",
                dimension="Integration",
                category="Cross-System Connectivity",
                dimension_sub="Cross-System Connectivity",
                question="How many MCP integrations are active? Which are planned?",
                guidance="Count active MCP connections (e.g., Git, JIRA, Slack, Confluence, databases). Assess reliability and adoption."
            ),
            AssessmentQuestion(
                id="CROSS_SYSTEM_3",
                dimension="Integration",
                category="Cross-System Connectivity",
                dimension_sub="Cross-System Connectivity",
                question="Do developers pull context from multiple systems per session?",
                guidance="Assess context richness: do developers load info from Git, JIRA, docs, and Slack in typical sessions?"
            ),
        ])

        # SECTION 3: Governance (Quality, Security, Metrics) - 9 questions
        self._questions.extend([
            # Quality Controls (3 questions)
            AssessmentQuestion(
                id="QUALITY_CONTROLS_1",
                dimension="Governance",
                category="Quality Controls",
                dimension_sub="Quality Controls",
                question="Is there a documented PR review checklist with AI-specific items?",
                guidance="Check for formal review standards. Are AI-generated changes held to the same quality bar as human code?"
            ),
            AssessmentQuestion(
                id="QUALITY_CONTROLS_2",
                dimension="Governance",
                category="Quality Controls",
                dimension_sub="Quality Controls",
                question="Are AI-generated changes held to the same quality bar as human code?",
                guidance="Assess whether code review, test coverage, and standards are equally applied to AI and human-written code."
            ),
            AssessmentQuestion(
                id="QUALITY_CONTROLS_3",
                dimension="Governance",
                category="Quality Controls",
                dimension_sub="Quality Controls",
                question="How are edge cases and test coverage validated?",
                guidance="Check if edge case testing is explicit, automated, or delegated to AI. Assess test coverage metrics."
            ),

            # Security & Compliance (3 questions)
            AssessmentQuestion(
                id="SECURITY_COMPLIANCE_1",
                dimension="Governance",
                category="Security & Compliance",
                dimension_sub="Security & Compliance",
                question="Is there a formal AI usage policy? Data handling rules?",
                guidance="Look for documented policies on what data can be sent to AI, what restrictions apply, and how policies are communicated."
            ),
            AssessmentQuestion(
                id="SECURITY_COMPLIANCE_2",
                dimension="Governance",
                category="Security & Compliance",
                dimension_sub="Security & Compliance",
                question="What restrictions exist on what can be sent to AI?",
                guidance="Identify restricted data types (PII, secrets, proprietary algorithms). Check if policies are enforced or advisory."
            ),
            AssessmentQuestion(
                id="SECURITY_COMPLIANCE_3",
                dimension="Governance",
                category="Security & Compliance",
                dimension_sub="Security & Compliance",
                question="Are AI actions logged and auditable?",
                guidance="Check whether AI session activity, prompts, and responses are logged. Are logs retained and accessible for audits?"
            ),

            # Measurement & KPIs (5 questions)
            AssessmentQuestion(
                id="MEASUREMENT_KPIS_1",
                dimension="Governance",
                category="Measurement & KPIs",
                dimension_sub="Measurement & KPIs",
                question="What metrics do you track for AI adoption? (% of team, sessions/day, cycle time)",
                guidance="Identify tracked metrics: adoption rate, frequency, productivity impacts. Check if baselines exist and trends are monitored."
            ),
            AssessmentQuestion(
                id="MEASUREMENT_KPIS_2",
                dimension="Governance",
                category="Measurement & KPIs",
                dimension_sub="Measurement & KPIs",
                question="Is AI impact measured? Pre/post baselines? Quantified or anecdotal?",
                guidance="Assess whether impact is quantified (cycle time reduction, bug rate changes) or anecdotal. Check data quality and rigor."
            ),
            AssessmentQuestion(
                id="MEASUREMENT_KPIS_3",
                dimension="Governance",
                category="Measurement & KPIs",
                dimension_sub="Measurement & KPIs",
                question="Are metrics tied to business outcomes (velocity, quality, time-to-market)?",
                guidance="Check whether AI metrics are connected to team and business KPIs or exist in isolation."
            ),
            AssessmentQuestion(
                id="MEASUREMENT_KPIS_4",
                dimension="Governance",
                category="Measurement & KPIs",
                dimension_sub="Measurement & KPIs",
                question="Who owns metric collection and reporting? How often are metrics reviewed?",
                guidance="Verify ownership and cadence: is metric tracking automated or manual? Are results shared with the team?"
            ),
            AssessmentQuestion(
                id="MEASUREMENT_KPIS_5",
                dimension="Governance",
                category="Measurement & KPIs",
                dimension_sub="Measurement & KPIs",
                question="Have you set maturity goals for each dimension? What's the target timeline?",
                guidance="Check if team has explicit L1-L4 targets and timelines. Are targets documented and communicated?"
            ),
        ])

        # SECTION 4: Execution Ownership (Ways, Accountability, Scalability) - 9 questions
        self._questions.extend([
            # Ways of Working (3 questions)
            AssessmentQuestion(
                id="WAYS_OF_WORKING_1",
                dimension="Execution Ownership",
                category="Ways of Working",
                dimension_sub="Ways of Working",
                question="Is there a documented 'AI Ways of Working' page?",
                guidance="Look for CLAUDE.md or dedicated documentation on team protocols for AI usage, session patterns, and tools."
            ),
            AssessmentQuestion(
                id="WAYS_OF_WORKING_2",
                dimension="Execution Ownership",
                category="Ways of Working",
                dimension_sub="Ways of Working",
                question="What's the standard protocol for starting an AI session? (Load CLAUDE.md? Context?)",
                guidance="Assess if there's a documented onboarding sequence: context loading, tool setup, environment checks."
            ),
            AssessmentQuestion(
                id="WAYS_OF_WORKING_3",
                dimension="Execution Ownership",
                category="Ways of Working",
                dimension_sub="Ways of Working",
                question="When do developers use plan mode vs. direct generation?",
                guidance="Check if there are explicit guidelines for choosing between planning and direct code generation approaches."
            ),

            # Accountability & Ownership (5 questions)
            AssessmentQuestion(
                id="ACCOUNTABILITY_1",
                dimension="Execution Ownership",
                category="Accountability & Ownership",
                dimension_sub="Accountability & Ownership",
                question="Is there a designated AI champion? What are their responsibilities?",
                guidance="Identify the AI champion or lead. Check their responsibilities: evangelism, tooling, training, metrics, culture."
            ),
            AssessmentQuestion(
                id="ACCOUNTABILITY_2",
                dimension="Execution Ownership",
                category="Accountability & Ownership",
                dimension_sub="Accountability & Ownership",
                question="Who owns CLAUDE.md maintenance? Prompt library? Onboarding?",
                guidance="Assign ownership: document maintainers, prompt curators, onboarding coordinators. Check update frequency."
            ),
            AssessmentQuestion(
                id="ACCOUNTABILITY_3",
                dimension="Execution Ownership",
                category="Accountability & Ownership",
                dimension_sub="Accountability & Ownership",
                question="Are AI KPIs tied to team performance reviews?",
                guidance="Check if AI adoption, usage, and contribution are factored into individual or team evaluations."
            ),
            AssessmentQuestion(
                id="ACCOUNTABILITY_4",
                dimension="Execution Ownership",
                category="Accountability & Ownership",
                dimension_sub="Accountability & Ownership",
                question="How is feedback on AI usage collected and acted upon?",
                guidance="Check if there are mechanisms for developers to report issues, suggest improvements, and contribute to tool selection."
            ),
            AssessmentQuestion(
                id="ACCOUNTABILITY_5",
                dimension="Execution Ownership",
                category="Accountability & Ownership",
                dimension_sub="Accountability & Ownership",
                question="Is AI tool adoption tracked by role or level (junior, senior, architect)?",
                guidance="Assess if adoption patterns differ by experience. Check if seniors are modeling AI usage for juniors."
            ),

            # Scalability & Knowledge Transfer (4 questions)
            AssessmentQuestion(
                id="SCALABILITY_1",
                dimension="Execution Ownership",
                category="Scalability & Knowledge Transfer",
                dimension_sub="Scalability & Knowledge Transfer",
                question="What AI onboarding materials do new developers receive?",
                guidance="Assess onboarding completeness: training docs, video tutorials, hands-on exercises, mentorship, ramp time."
            ),
            AssessmentQuestion(
                id="SCALABILITY_2",
                dimension="Execution Ownership",
                category="Scalability & Knowledge Transfer",
                dimension_sub="Scalability & Knowledge Transfer",
                question="Is there a prompt library or playbook for common tasks?",
                guidance="Look for documented, curated collections of effective prompts, examples, and patterns for typical work."
            ),
            AssessmentQuestion(
                id="SCALABILITY_3",
                dimension="Execution Ownership",
                category="Scalability & Knowledge Transfer",
                dimension_sub="Scalability & Knowledge Transfer",
                question="How quickly do new team members become productive with AI?",
                guidance="Assess ramp time: days to first productive session, weeks to full capability, attrition during learning curve."
            ),
            AssessmentQuestion(
                id="SCALABILITY_4",
                dimension="Execution Ownership",
                category="Scalability & Knowledge Transfer",
                dimension_sub="Scalability & Knowledge Transfer",
                question="How do you scale AI expertise across a growing team? Is there mentoring or peer learning?",
                guidance="Check if power users mentor others, or if expertise stays siloed. Assess knowledge transfer mechanisms."
            ),
        ])

        # SECTION 5: Value Realization (Business Impact) - 9 additional questions
        # (Extends governance/execution focus on business value, adds depth to measurement)
        self._questions.extend([
            AssessmentQuestion(
                id="VALUE_REALIZATION_1",
                dimension="Value Realization",
                category="Business Impact",
                dimension_sub="Measurement & KPIs",
                question="Has AI adoption reduced cycle time? By how much?",
                guidance="Quantify cycle time impact: compare pre/post adoption. Look for data in sprint metrics, deployment frequency, lead time."
            ),
            AssessmentQuestion(
                id="VALUE_REALIZATION_2",
                dimension="Value Realization",
                category="Business Impact",
                dimension_sub="Measurement & KPIs",
                question="Has code quality improved (defect rate, test coverage, review feedback)?",
                guidance="Assess quality metrics: bug escape rate, test coverage percentage, review comment reduction, regression frequency."
            ),
            AssessmentQuestion(
                id="VALUE_REALIZATION_3",
                dimension="Value Realization",
                category="Business Impact",
                dimension_sub="Measurement & KPIs",
                question="Are developers satisfied with AI? How do you measure satisfaction?",
                guidance="Check for NPS, surveys, or anecdotal feedback. Assess adoption friction: resistance vs. enthusiasm."
            ),
            AssessmentQuestion(
                id="VALUE_REALIZATION_4",
                dimension="Value Realization",
                category="Business Impact",
                dimension_sub="Measurement & KPIs",
                question="Has AI freed time for high-value work? What's being reprioritized?",
                guidance="Assess whether developers are shifting from boilerplate to architecture, design, mentoring, or innovation."
            ),
            AssessmentQuestion(
                id="VALUE_REALIZATION_5",
                dimension="Value Realization",
                category="Business Impact",
                dimension_sub="Measurement & KPIs",
                question="What's the ROI? Tool cost vs. productivity gains?",
                guidance="Calculate return: licensing costs vs. time saved (salary impact), reduced bugs (support cost), faster delivery (market impact)."
            ),
            AssessmentQuestion(
                id="VALUE_REALIZATION_6",
                dimension="Value Realization",
                category="Business Impact",
                dimension_sub="Measurement & KPIs",
                question="Has onboarding time for new developers decreased?",
                guidance="Measure new-hire ramp time with AI vs. without. Check time-to-first-contribution, time-to-competence."
            ),
            AssessmentQuestion(
                id="VALUE_REALIZATION_7",
                dimension="Value Realization",
                category="Business Impact",
                dimension_sub="Measurement & KPIs",
                question="Are developers using AI for non-coding tasks (design, planning, documentation)?",
                guidance="Assess breadth of AI usage beyond code: architecture discussions, test planning, docs, technical decisions."
            ),
            AssessmentQuestion(
                id="VALUE_REALIZATION_8",
                dimension="Value Realization",
                category="Business Impact",
                dimension_sub="Measurement & KPIs",
                question="How has code review velocity changed since AI adoption?",
                guidance="Compare review time, number of review rounds, time-in-review. Check if AI reviews reduce human review cycles."
            ),
            AssessmentQuestion(
                id="VALUE_REALIZATION_9",
                dimension="Value Realization",
                category="Business Impact",
                dimension_sub="Measurement & KPIs",
                question="What unexpected benefits or challenges have emerged from AI adoption?",
                guidance="Capture learning: were there surprises (positive or negative)? What would you do differently?"
            ),
        ])

    def load_questions(self) -> List[AssessmentQuestion]:
        """
        Load and return all assessment questions.

        Returns:
            List of all 50 AssessmentQuestion objects
        """
        return self._questions.copy()

    def get_questions_by_dimension(self, dimension: str) -> List[AssessmentQuestion]:
        """
        Get all questions for a specific high-level dimension.

        Args:
            dimension: Name of the dimension (e.g., "Capability", "Integration", "Governance", "Execution Ownership", "Value Realization")

        Returns:
            List of AssessmentQuestion objects matching the dimension
        """
        return [q for q in self._questions if q.dimension == dimension]

    def get_questions_by_category(self, category: str) -> List[AssessmentQuestion]:
        """
        Get all questions for a specific category/sub-dimension.

        Args:
            category: Category name (e.g., "AI Tool Adoption", "Quality Controls", "CI/CD Integration")

        Returns:
            List of AssessmentQuestion objects matching the category
        """
        return [q for q in self._questions if q.category == category]

    def get_questions_by_subdimension(self, subdimension: str) -> List[AssessmentQuestion]:
        """
        Get all questions for a specific sub-dimension.

        Args:
            subdimension: Sub-dimension name (e.g., "AI Tool Adoption", "Quality Controls")

        Returns:
            List of AssessmentQuestion objects matching the sub-dimension
        """
        return [q for q in self._questions if q.dimension_sub == subdimension]

    def validate_responses(self, responses: List[AssessmentResponse]) -> Dict[str, List[str]]:
        """
        Validate a list of assessment responses.

        Checks for:
        - Missing required fields (question_id, answer, confidence)
        - Invalid confidence values
        - Unrecognized question IDs
        - Missing responses for all questions

        Args:
            responses: List of AssessmentResponse objects

        Returns:
            Dictionary with error keys and lists of error messages. Empty dict if all valid.
            Example: {"validation": ["Question XYZ not found"], "missing": ["AI_TOOL_ADOPTION_1"]}
        """
        errors: Dict[str, List[str]] = {
            "validation": [],
            "missing": [],
            "confidence": [],
        }

        valid_ids = {q.id for q in self._questions}
        valid_confidence = {"certain", "likely", "unsure"}
        responded_ids = set()

        for response in responses:
            # Check required fields
            if not response.question_id:
                errors["validation"].append("Response missing question_id")
            if not response.answer:
                errors["validation"].append(f"Response for {response.question_id} missing answer")
            if not response.confidence:
                errors["validation"].append(f"Response for {response.question_id} missing confidence")

            # Check valid question ID
            if response.question_id not in valid_ids:
                errors["validation"].append(f"Unknown question_id: {response.question_id}")

            # Check valid confidence
            if response.confidence and response.confidence not in valid_confidence:
                errors["confidence"].append(
                    f"Invalid confidence '{response.confidence}' for {response.question_id}. "
                    f"Must be one of: {', '.join(valid_confidence)}"
                )

            responded_ids.add(response.question_id)

        # Check for missing questions
        missing = valid_ids - responded_ids
        if missing:
            errors["missing"] = sorted(list(missing))

        # Clean up empty categories
        return {k: v for k, v in errors.items() if v}

    def get_all_dimensions(self) -> List[str]:
        """
        Get all unique high-level dimensions.

        Returns:
            Sorted list of dimension names
        """
        return sorted(set(q.dimension for q in self._questions))

    def get_all_categories(self) -> List[str]:
        """
        Get all unique categories.

        Returns:
            Sorted list of category names
        """
        return sorted(set(q.category for q in self._questions))

    def get_all_subdimensions(self) -> List[str]:
        """
        Get all unique sub-dimensions.

        Returns:
            Sorted list of sub-dimension names
        """
        return sorted(set(q.dimension_sub for q in self._questions))
