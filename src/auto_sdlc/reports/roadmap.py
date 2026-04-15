"""
Roadmap Generator Module

Produces actionable steps for teams to progress from their current maturity level
to the next level (L1→L2, L2→L3, L3→L4) per dimension.

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


@dataclass
class RoadmapAction:
    """
    A single actionable step in a roadmap transition.

    Attributes:
        action_id: Unique identifier (e.g., "QC_L1L2_001")
        step: Sequence number (1, 2, 3, etc.)
        title: Short action title
        description: Detailed explanation of what to do
        effort_hours: Estimated person-hours to complete
        effort_weeks: Estimated calendar weeks (accounting for coordination)
        owners: Roles responsible (e.g., ["Tech Lead", "AI Champion"])
        dependencies: IDs of actions that must complete first (empty if none)
        success_criteria: How to know the action is complete
        risk: Potential blockers or challenges
    """

    action_id: str
    step: int
    title: str
    description: str
    effort_hours: int
    effort_weeks: int
    owners: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    success_criteria: str = ""
    risk: str = ""


@dataclass
class RoadmapItem:
    """
    A complete roadmap for one dimension's transition from current to target level.

    Attributes:
        dimension: Name of the dimension (one of 12)
        current_level: Current maturity level (1-4)
        target_level: Target maturity level (current_level + 1)
        actions: Ordered list of RoadmapAction objects
        total_effort_hours: Sum of all action effort_hours
        total_effort_weeks: Sum of all action effort_weeks
        key_insight: One-liner on what's most critical for this transition
    """

    dimension: str
    current_level: int
    target_level: int
    actions: List[RoadmapAction] = field(default_factory=list)
    total_effort_hours: int = 0
    total_effort_weeks: int = 0
    key_insight: str = ""


class RoadmapGenerator:
    """
    Generates roadmaps for AI maturity transitions per dimension.

    Provides built-in knowledge of L1→L2→L3→L4 transitions for all 12 dimensions.
    - L1 = Assisted (Ad-hoc, unguided usage)
    - L2 = Integrated (Documented, enforced practices)
    - L3 = Agentic (Automated decision-making, multi-step workflows)
    - L4 = Autonomous (Self-improving, fully delegated)
    """

    def __init__(self):
        """Initialize the roadmap generator."""
        self._roadmap_data = self._build_roadmap_data()

    def _build_roadmap_data(self) -> Dict[str, Dict[str, List[RoadmapAction]]]:
        """
        Build the complete roadmap knowledge base.

        Returns:
            Dict mapping dimension → (transition → list of actions)
            Example: data["Quality Controls"]["L1→L2"] = [action1, action2, ...]
        """
        data = {}

        # ===== DIMENSION 1: AI TOOL ADOPTION =====
        data["AI Tool Adoption"] = {
            "L1→L2": [
                RoadmapAction(
                    action_id="ATA_L1L2_001",
                    step=1,
                    title="Audit current tool usage across team",
                    description="Survey team on which AI tools they use (Claude, ChatGPT, Gemini, etc.). Document current patterns, preferences, and pain points.",
                    effort_hours=4,
                    effort_weeks=1,
                    owners=["Tech Lead", "AI Champion"],
                    dependencies=[],
                    success_criteria="Tool usage spreadsheet completed with 90%+ team participation",
                    risk="Low participation; outdated data",
                ),
                RoadmapAction(
                    action_id="ATA_L1L2_002",
                    step=2,
                    title="Define tool selection policy",
                    description="Collaborate with team to agree on preferred AI tools (e.g., Claude Code as primary). Document in CLAUDE.md with rationale and license agreements.",
                    effort_hours=6,
                    effort_weeks=1,
                    owners=["Tech Lead", "Product Manager"],
                    dependencies=["ATA_L1L2_001"],
                    success_criteria="Policy documented in CLAUDE.md; team consensus achieved",
                    risk="Resistance to standardization; licensing costs",
                ),
                RoadmapAction(
                    action_id="ATA_L1L2_003",
                    step=3,
                    title="Set up centralized license management",
                    description="Consolidate tool licenses under team/company account. Set up SSO, revoke personal accounts, distribute credentials securely.",
                    effort_hours=8,
                    effort_weeks=2,
                    owners=["Tech Lead", "Admin"],
                    dependencies=["ATA_L1L2_002"],
                    success_criteria="100% of team using organizational accounts; personal accounts revoked",
                    risk="Onboarding friction; account migration issues",
                ),
                RoadmapAction(
                    action_id="ATA_L1L2_004",
                    step=4,
                    title="Train team on approved tools",
                    description="Deliver hands-on training on standard tools (e.g., Claude Code features, best practices, integrations). Provide recorded session.",
                    effort_hours=6,
                    effort_weeks=1,
                    owners=["AI Champion"],
                    dependencies=["ATA_L1L2_003"],
                    success_criteria="Training completed; 90%+ attendance; team confirms understanding",
                    risk="Low engagement; training not retained",
                ),
            ],
            "L2→L3": [
                RoadmapAction(
                    action_id="ATA_L2L3_001",
                    step=1,
                    title="Evaluate advanced tool integrations",
                    description="Research how tools integrate with IDE, CI/CD, MCP systems. Prototype integrations with top 2-3 tools.",
                    effort_hours=12,
                    effort_weeks=2,
                    owners=["Tech Lead", "Architect"],
                    dependencies=[],
                    success_criteria="Proof-of-concept integrations validated; decision matrix completed",
                    risk="Integration complexity; tool limitations",
                ),
                RoadmapAction(
                    action_id="ATA_L2L3_002",
                    step=2,
                    title="Implement IDE plugins and integrations",
                    description="Deploy tool integrations into development workflows (VSCode extensions, IDE plugins, etc.). Automate tool invocation where possible.",
                    effort_hours=16,
                    effort_weeks=3,
                    owners=["Tech Lead"],
                    dependencies=["ATA_L2L3_001"],
                    success_criteria="Plugins deployed to all developers; adoption tracking enabled",
                    risk="Plugin conflicts; version compatibility issues",
                ),
                RoadmapAction(
                    action_id="ATA_L2L3_003",
                    step=3,
                    title="Establish tool health monitoring",
                    description="Track tool availability, usage patterns, performance, cost. Create dashboard for leadership visibility.",
                    effort_hours=8,
                    effort_weeks=2,
                    owners=["AI Champion", "DevOps"],
                    dependencies=["ATA_L2L3_002"],
                    success_criteria="Dashboard live with 90% uptime; weekly health reports generated",
                    risk="Monitoring overhead; false alerts",
                ),
            ],
            "L3→L4": [
                RoadmapAction(
                    action_id="ATA_L3L4_001",
                    step=1,
                    title="Develop tool recommendation engine",
                    description="Build intelligent system to recommend appropriate tool for task type (e.g., Claude Code for coding, ChatGPT for brainstorming).",
                    effort_hours=20,
                    effort_weeks=4,
                    owners=["Architect", "ML Engineer"],
                    dependencies=[],
                    success_criteria="Engine deployed; recommendations accurate 85%+ of the time",
                    risk="High development effort; hard to validate",
                ),
                RoadmapAction(
                    action_id="ATA_L3L4_002",
                    step=2,
                    title="Implement tool auto-switching",
                    description="Enable automatic switching between tools based on task/context. Users can opt-in or override.",
                    effort_hours=16,
                    effort_weeks=3,
                    owners=["Tech Lead"],
                    dependencies=["ATA_L3L4_001"],
                    success_criteria="Auto-switch reduces manual tool selection by 70%+",
                    risk="User confusion; over-automation",
                ),
            ],
        }

        # ===== DIMENSION 2: PROMPT & CONTEXT ENGINEERING =====
        data["Prompt & Context Engineering"] = {
            "L1→L2": [
                RoadmapAction(
                    action_id="PCE_L1L2_001",
                    step=1,
                    title="Create CLAUDE.md template",
                    description="Document team's AI conventions in root CLAUDE.md: architecture, coding standards, testing practices, MCP tools. Target 1-2 pages.",
                    effort_hours=8,
                    effort_weeks=1,
                    owners=["Tech Lead", "AI Champion"],
                    dependencies=[],
                    success_criteria="CLAUDE.md present in repo; covers all key areas; team reviews and approves",
                    risk="Outdated quickly; effort to maintain",
                ),
                RoadmapAction(
                    action_id="PCE_L1L2_002",
                    step=2,
                    title="Build shared prompt library",
                    description="Create repo for reusable prompts organized by task (code review, test generation, refactoring). Include examples and variations.",
                    effort_hours=10,
                    effort_weeks=1,
                    owners=["AI Champion"],
                    dependencies=["PCE_L1L2_001"],
                    success_criteria="Prompt library live; 10+ templates; team using 5+ daily",
                    risk="Templates go stale; low adoption",
                ),
                RoadmapAction(
                    action_id="PCE_L1L2_003",
                    step=3,
                    title="Establish context loading best practices",
                    description="Document how to structure AI sessions: load CLAUDE.md, include relevant files, set constraints. Create quick-start guide.",
                    effort_hours=6,
                    effort_weeks=1,
                    owners=["AI Champion"],
                    dependencies=["PCE_L1L2_001"],
                    success_criteria="Quick-start guide published; team feedback incorporated",
                    risk="Complexity; developers skip steps",
                ),
                RoadmapAction(
                    action_id="PCE_L1L2_004",
                    step=4,
                    title="Train team on context engineering",
                    description="Conduct workshop on how to write effective prompts: be specific, include context, use examples, verify understanding.",
                    effort_hours=4,
                    effort_weeks=1,
                    owners=["AI Champion"],
                    dependencies=["PCE_L1L2_002", "PCE_L1L2_003"],
                    success_criteria="Training delivered; 90%+ attendance; team commits to using library",
                    risk="Training not retained; old habits persist",
                ),
            ],
            "L2→L3": [
                RoadmapAction(
                    action_id="PCE_L2L3_001",
                    step=1,
                    title="Implement prompt versioning & A/B testing",
                    description="Set up system to track prompt variations, measure effectiveness (time to solve, accuracy, cost). Run A/B tests on variants.",
                    effort_hours=12,
                    effort_weeks=2,
                    owners=["AI Champion", "Analytics"],
                    dependencies=[],
                    success_criteria="Versioning system live; 3+ A/B tests completed; results documented",
                    risk="Complex tracking; statistical significance hard to prove",
                ),
                RoadmapAction(
                    action_id="PCE_L2L3_002",
                    step=2,
                    title="Develop context auto-loading system",
                    description="Automate loading of CLAUDE.md, relevant code files, and project context at session start. Integrate with IDE or Claude Code.",
                    effort_hours=16,
                    effort_weeks=3,
                    owners=["Tech Lead"],
                    dependencies=["PCE_L2L3_001"],
                    success_criteria="Auto-load reduces manual context loading by 80%",
                    risk="Over-loading context; token limits",
                ),
                RoadmapAction(
                    action_id="PCE_L2L3_003",
                    step=3,
                    title="Create dynamic prompt generation",
                    description="Build system to generate task-specific prompts based on context (file type, task, team standards). Reduces manual prompt writing.",
                    effort_hours=14,
                    effort_weeks=3,
                    owners=["Architect"],
                    dependencies=["PCE_L2L3_001"],
                    success_criteria="Generator covers 80%+ of common task types",
                    risk="Over-automation; loss of control",
                ),
            ],
            "L3→L4": [
                RoadmapAction(
                    action_id="PCE_L3L4_001",
                    step=1,
                    title="Implement adaptive prompting based on feedback",
                    description="System learns from prompt outcomes: if a variation works better, adopt it; if worse, revert. Continuous optimization.",
                    effort_hours=24,
                    effort_weeks=4,
                    owners=["ML Engineer", "Architect"],
                    dependencies=[],
                    success_criteria="Adaptive system reduces failed interactions by 40%+",
                    risk="Unexpected behavior changes; hard to debug",
                ),
            ],
        }

        # ===== DIMENSION 3: AGENT CONFIGURATION =====
        data["Agent Configuration"] = {
            "L1→L2": [
                RoadmapAction(
                    action_id="AC_L1L2_001",
                    step=1,
                    title="Audit existing custom skills",
                    description="Inventory all custom slash commands and agents being used. Document what each does, who maintains it, how mature it is.",
                    effort_hours=4,
                    effort_weeks=1,
                    owners=["Tech Lead"],
                    dependencies=[],
                    success_criteria="Inventory spreadsheet with 90%+ coverage; maturity assessed",
                    risk="Incomplete inventory; skills forgotten",
                ),
                RoadmapAction(
                    action_id="AC_L1L2_002",
                    step=2,
                    title="Document skill definitions in AGENTS.md",
                    description="Create AGENTS.md in repo documenting all skills: purpose, inputs, outputs, parameters, examples, maintenance owner.",
                    effort_hours=8,
                    effort_weeks=1,
                    owners=["AI Champion"],
                    dependencies=["AC_L1L2_001"],
                    success_criteria="AGENTS.md complete; 100% of skills documented; team reviews",
                    risk="Documentation skipped; maintenance unclear",
                ),
                RoadmapAction(
                    action_id="AC_L1L2_003",
                    step=3,
                    title="Implement core skills (/review, /commit, /plan)",
                    description="Build 3 foundational skills: /review (code review), /commit (message generation), /plan (project planning). Make them available to team.",
                    effort_hours=12,
                    effort_weeks=2,
                    owners=["Tech Lead", "AI Champion"],
                    dependencies=["AC_L1L2_002"],
                    success_criteria="Skills deployed; adopted by 80%+ of team; feedback collected",
                    risk="Skills too rigid; team prefers alternatives",
                ),
                RoadmapAction(
                    action_id="AC_L1L2_004",
                    step=4,
                    title="Establish skill governance policy",
                    description="Define how new skills are created, tested, approved, and retired. Assign ownership and SLAs.",
                    effort_hours=6,
                    effort_weeks=1,
                    owners=["Tech Lead"],
                    dependencies=["AC_L1L2_002"],
                    success_criteria="Governance policy documented; review board formed",
                    risk="Process too rigid; slows innovation",
                ),
            ],
            "L2→L3": [
                RoadmapAction(
                    action_id="AC_L2L3_001",
                    step=1,
                    title="Build multi-step agents",
                    description="Enhance skills to handle multi-step workflows (e.g., /plan decomposes into /design, /scaffold, /test). Add conditional logic and error recovery.",
                    effort_hours=18,
                    effort_weeks=3,
                    owners=["Tech Lead"],
                    dependencies=[],
                    success_criteria="Multi-step agents deployed; success rate 90%+",
                    risk="Complexity; hard to debug",
                ),
                RoadmapAction(
                    action_id="AC_L2L3_002",
                    step=2,
                    title="Implement agent self-testing",
                    description="Agents validate their own outputs before returning results. Add guardrails, format checks, and confidence scoring.",
                    effort_hours=10,
                    effort_weeks=2,
                    owners=["Tech Lead"],
                    dependencies=["AC_L2L3_001"],
                    success_criteria="Self-test catches 95%+ of errors before output",
                    risk="Over-validation; slows agents",
                ),
                RoadmapAction(
                    action_id="AC_L2L3_003",
                    step=3,
                    title="Set up agent monitoring and tracing",
                    description="Log all agent invocations, inputs, outputs, errors, and performance. Create dashboard for monitoring and debugging.",
                    effort_hours=12,
                    effort_weeks=2,
                    owners=["DevOps", "AI Champion"],
                    dependencies=["AC_L2L3_001"],
                    success_criteria="Dashboard live; logs retained for 30 days; issues flagged automatically",
                    risk="Logging overhead; privacy concerns",
                ),
            ],
            "L3→L4": [
                RoadmapAction(
                    action_id="AC_L3L4_001",
                    step=1,
                    title="Implement autonomous agent delegation",
                    description="Agents decide when to invoke other agents without user prompting. Enables hands-off workflows (e.g., auto-plan, auto-code, auto-review).",
                    effort_hours=20,
                    effort_weeks=4,
                    owners=["Architect"],
                    dependencies=[],
                    success_criteria="Autonomous workflows active; 70%+ of tasks complete without intervention",
                    risk="Loss of control; unexpected behavior",
                ),
                RoadmapAction(
                    action_id="AC_L3L4_002",
                    step=2,
                    title="Add agent learning from outcomes",
                    description="Agents track success/failure of delegated tasks. Adjust future decisions based on historical outcomes.",
                    effort_hours=16,
                    effort_weeks=3,
                    owners=["ML Engineer"],
                    dependencies=["AC_L3L4_001"],
                    success_criteria="Agent success rate improves 10%+ month-over-month",
                    risk="Unexpected behavior shifts; hard to audit",
                ),
            ],
        }

        # ===== DIMENSION 4: CI/CD INTEGRATION =====
        data["CI/CD Integration"] = {
            "L1→L2": [
                RoadmapAction(
                    action_id="CCI_L1L2_001",
                    step=1,
                    title="Map current CI/CD pipeline",
                    description="Document existing pipeline: triggers, stages, tools, approval gates. Identify opportunities for AI integration.",
                    effort_hours=4,
                    effort_weeks=1,
                    owners=["DevOps", "Tech Lead"],
                    dependencies=[],
                    success_criteria="Pipeline diagram created; 3+ integration points identified",
                    risk="Pipeline complexity; documentation out of date",
                ),
                RoadmapAction(
                    action_id="CCI_L1L2_002",
                    step=2,
                    title="Implement AI code review step",
                    description="Add /review step in PR pipeline before human review. Checks style, security, complexity. Fails if critical issues found.",
                    effort_hours=10,
                    effort_weeks=2,
                    owners=["Tech Lead"],
                    dependencies=["CCI_L1L2_001"],
                    success_criteria="AI review step live; 100% of PRs reviewed; false positives <5%",
                    risk="Over-strictness; blocks legitimate changes",
                ),
                RoadmapAction(
                    action_id="CCI_L1L2_003",
                    step=3,
                    title="Add AI test generation to CI",
                    description="Integrate AI test generation into build process. Generate unit tests for new code automatically.",
                    effort_hours=8,
                    effort_weeks=2,
                    owners=["Tech Lead"],
                    dependencies=["CCI_L1L2_001"],
                    success_criteria="Generated tests cover 70%+ of new code; pass rate 90%+",
                    risk="Generated tests may be incomplete; false security",
                ),
                RoadmapAction(
                    action_id="CCI_L1L2_004",
                    step=4,
                    title="Set up AI results reporting",
                    description="Create reports showing AI review results, test coverage, issues found. Share with team and leadership.",
                    effort_hours=6,
                    effort_weeks=1,
                    owners=["DevOps"],
                    dependencies=["CCI_L1L2_002", "CCI_L1L2_003"],
                    success_criteria="Reports generated automatically; shared weekly; actionable insights",
                    risk="Report fatigue; data not actionable",
                ),
            ],
            "L2→L3": [
                RoadmapAction(
                    action_id="CCI_L2L3_001",
                    step=1,
                    title="Expand AI review to multiple stages",
                    description="Add AI review at multiple pipeline stages: PR creation, merge, release. Each stage has different rules and severity thresholds.",
                    effort_hours=12,
                    effort_weeks=2,
                    owners=["Tech Lead"],
                    dependencies=[],
                    success_criteria="Multi-stage review deployed; catches issues at each stage",
                    risk="Complexity; slow pipeline",
                ),
                RoadmapAction(
                    action_id="CCI_L2L3_002",
                    step=2,
                    title="Implement AI test coverage analysis",
                    description="AI analyzes code and identifies gaps in test coverage. Generates tests for high-risk areas automatically.",
                    effort_hours=14,
                    effort_weeks=2,
                    owners=["Tech Lead"],
                    dependencies=["CCI_L2L3_001"],
                    success_criteria="Coverage gaps identified; 80%+ closure rate",
                    risk="Generated tests may miss critical cases",
                ),
                RoadmapAction(
                    action_id="CCI_L2L3_003",
                    step=3,
                    title="Add security scanning to AI review",
                    description="Extend AI review to detect security issues: injection flaws, exposed secrets, insecure patterns. Integrate SAST tools.",
                    effort_hours=10,
                    effort_weeks=2,
                    owners=["Security", "Tech Lead"],
                    dependencies=["CCI_L2L3_001"],
                    success_criteria="Security issues caught pre-merge; 95%+ accuracy",
                    risk="False positives; over-flagging",
                ),
            ],
            "L3→L4": [
                RoadmapAction(
                    action_id="CCI_L3L4_001",
                    step=1,
                    title="Implement autonomous code generation in CI",
                    description="AI generates entire features or bug fixes automatically from tickets. Human review only for complex changes.",
                    effort_hours=24,
                    effort_weeks=4,
                    owners=["Architect"],
                    dependencies=[],
                    success_criteria="Auto-generation reduces manual coding time by 40%+",
                    risk="Generated code quality issues; loss of control",
                ),
                RoadmapAction(
                    action_id="CCI_L3L4_002",
                    step=2,
                    title="Enable self-healing of failed tests",
                    description="When tests fail, AI automatically diagnoses and attempts fixes. Escalates to human only if fix fails.",
                    effort_hours=16,
                    effort_weeks=3,
                    owners=["Tech Lead"],
                    dependencies=["CCI_L3L4_001"],
                    success_criteria="Auto-healing fixes 70%+ of test failures",
                    risk="Unexpected behavior changes; hard to audit",
                ),
            ],
        }

        # ===== DIMENSION 5: TICKETING & PLANNING =====
        data["Ticketing & Planning"] = {
            "L1→L2": [
                RoadmapAction(
                    action_id="TP_L1L2_001",
                    step=1,
                    title="Define ticket structure and quality standards",
                    description="Document what makes a good ticket: clear title, detailed description, acceptance criteria, effort estimate. Provide template.",
                    effort_hours=6,
                    effort_weeks=1,
                    owners=["Tech Lead", "PM"],
                    dependencies=[],
                    success_criteria="Template published; team uses it for 80%+ of new tickets",
                    risk="Template too prescriptive; friction creating tickets",
                ),
                RoadmapAction(
                    action_id="TP_L1L2_002",
                    step=2,
                    title="Implement AI ticket validation",
                    description="Build /validate skill to check ticket quality: is it clear? Are acceptance criteria measurable? Suggest improvements.",
                    effort_hours=8,
                    effort_weeks=1,
                    owners=["AI Champion"],
                    dependencies=["TP_L1L2_001"],
                    success_criteria="Validation skill deployed; validates 100% of new tickets",
                    risk="False positives; developers skip validation",
                ),
                RoadmapAction(
                    action_id="TP_L1L2_003",
                    step=3,
                    title="Add AI pre-development review",
                    description="Before starting a ticket, developers use AI to review it: uncover edge cases, ask clarifying questions, suggest approach.",
                    effort_hours=6,
                    effort_weeks=1,
                    owners=["AI Champion"],
                    dependencies=["TP_L1L2_002"],
                    success_criteria="80%+ of developers use pre-dev review; uncover 15%+ more edge cases",
                    risk="Adds time to start; developers skip",
                ),
                RoadmapAction(
                    action_id="TP_L1L2_004",
                    step=4,
                    title="Set up planning metrics dashboard",
                    description="Track: ticket quality score, AI flag rate, edge cases discovered pre-dev, rework due to unclear requirements.",
                    effort_hours=6,
                    effort_weeks=1,
                    owners=["Analytics"],
                    dependencies=["TP_L1L2_002"],
                    success_criteria="Dashboard live; metrics show 20%+ improvement in planning quality",
                    risk="Metrics hard to define; data collection overhead",
                ),
            ],
            "L2→L3": [
                RoadmapAction(
                    action_id="TP_L2L3_001",
                    step=1,
                    title="Implement AI task decomposition",
                    description="AI automatically breaks down complex tickets into sub-tasks with dependencies. Developers can use or override.",
                    effort_hours=14,
                    effort_weeks=2,
                    owners=["Architect"],
                    dependencies=[],
                    success_criteria="Decomposition used for 70%+ of tickets; saves 3+ hours per complex ticket",
                    risk="Over-decomposition; too many sub-tasks",
                ),
                RoadmapAction(
                    action_id="TP_L2L3_002",
                    step=2,
                    title="Add AI effort estimation",
                    description="AI estimates effort (hours, story points) based on ticket complexity, team history, similar past tickets.",
                    effort_hours=10,
                    effort_weeks=2,
                    owners=["Analytics"],
                    dependencies=["TP_L2L3_001"],
                    success_criteria="Estimates accurate within ±20%; used for sprint planning",
                    risk="Historical data biased; estimates drift",
                ),
                RoadmapAction(
                    action_id="TP_L2L3_003",
                    step=3,
                    title="Implement acceptance criteria generation",
                    description="AI generates comprehensive acceptance criteria from ticket description. Includes edge cases, security, performance.",
                    effort_hours=12,
                    effort_weeks=2,
                    owners=["Architect"],
                    dependencies=["TP_L2L3_001"],
                    success_criteria="Generated criteria cover 90%+ of test cases; reduce rework",
                    risk="Generated criteria may be incomplete; false sense of completeness",
                ),
            ],
            "L3→L4": [
                RoadmapAction(
                    action_id="TP_L3L4_001",
                    step=1,
                    title="Enable autonomous work assignment",
                    description="AI automatically assigns tickets to team members based on skills, capacity, history. Developers can request changes.",
                    effort_hours=16,
                    effort_weeks=3,
                    owners=["Architect"],
                    dependencies=[],
                    success_criteria="80%+ of assignments accepted without change; load balanced",
                    risk="Developers feel over-managed; low morale",
                ),
                RoadmapAction(
                    action_id="TP_L3L4_002",
                    step=2,
                    title="Implement adaptive planning",
                    description="AI adjusts sprint plans based on progress, blockers, team velocity. Suggests reprioritization or scope changes.",
                    effort_hours=12,
                    effort_weeks=3,
                    owners=["PM", "Architect"],
                    dependencies=["TP_L3L4_001"],
                    success_criteria="Sprint velocity more predictable; scope creep reduced by 30%+",
                    risk="Frequent changes reduce team focus",
                ),
            ],
        }

        # ===== DIMENSION 6: CROSS-SYSTEM CONNECTIVITY =====
        data["Cross-System Connectivity"] = {
            "L1→L2": [
                RoadmapAction(
                    action_id="CSC_L1L2_001",
                    step=1,
                    title="Audit external system access",
                    description="Inventory systems AI needs to access: Git, JIRA, Slack, Confluence, docs. Document current access, gaps, security constraints.",
                    effort_hours=4,
                    effort_weeks=1,
                    owners=["Tech Lead", "Security"],
                    dependencies=[],
                    success_criteria="Access matrix documented; 5+ systems identified; permissions reviewed",
                    risk="Incomplete inventory; security gaps",
                ),
                RoadmapAction(
                    action_id="CSC_L1L2_002",
                    step=2,
                    title="Enable Git integration",
                    description="Grant AI read access to Git repos via SSH or tokens. Test: AI can clone, browse, diff code.",
                    effort_hours=6,
                    effort_weeks=1,
                    owners=["DevOps"],
                    dependencies=["CSC_L1L2_001"],
                    success_criteria="All team repos accessible to AI; no auth errors",
                    risk="Token exposure; over-permissive access",
                ),
                RoadmapAction(
                    action_id="CSC_L1L2_003",
                    step=3,
                    title="Integrate JIRA for ticket context",
                    description="Connect AI to JIRA. Ability to search, fetch, comment on tickets. Enable /ticket skill.",
                    effort_hours=8,
                    effort_weeks=1,
                    owners=["Tech Lead"],
                    dependencies=["CSC_L1L2_001"],
                    success_criteria="JIRA integration live; 90%+ of developers reference tickets from AI",
                    risk="Performance issues; rate limits",
                ),
                RoadmapAction(
                    action_id="CSC_L1L2_004",
                    step=4,
                    title="Document integration architecture",
                    description="Create INTEGRATIONS.md explaining how to access each system, auth mechanism, rate limits, fallbacks.",
                    effort_hours=4,
                    effort_weeks=1,
                    owners=["Tech Lead"],
                    dependencies=["CSC_L1L2_002", "CSC_L1L2_003"],
                    success_criteria="Integration docs complete; used to onboard new systems",
                    risk="Docs go out of date",
                ),
            ],
            "L2→L3": [
                RoadmapAction(
                    action_id="CSC_L2L3_001",
                    step=1,
                    title="Implement MCP integrations",
                    description="Build Model Context Protocol (MCP) integrations for key systems (Slack, Confluence, GitHub, JIRA). Enable context passing.",
                    effort_hours=16,
                    effort_weeks=3,
                    owners=["Tech Lead"],
                    dependencies=[],
                    success_criteria="3+ MCP integrations live; AI can use them in workflows",
                    risk="MCP protocol complexity; versioning issues",
                ),
                RoadmapAction(
                    action_id="CSC_L2L3_002",
                    step=2,
                    title="Build cross-system context fusion",
                    description="AI automatically pulls related context from multiple systems (e.g., for a ticket: GitHub PR, code, test results, Slack discussion).",
                    effort_hours=12,
                    effort_weeks=2,
                    owners=["Architect"],
                    dependencies=["CSC_L2L3_001"],
                    success_criteria="Context fusion reduces manual gathering by 60%+",
                    risk="Too much context; overwhelming",
                ),
                RoadmapAction(
                    action_id="CSC_L2L3_003",
                    step=3,
                    title="Enable bi-directional system updates",
                    description="AI can not only read from systems but also update them: push code to Git, update JIRA status, post to Slack.",
                    effort_hours=14,
                    effort_weeks=2,
                    owners=["Tech Lead"],
                    dependencies=["CSC_L2L3_001"],
                    success_criteria="Updates working for 3+ systems; zero permission errors",
                    risk="Over-automation; unexpected changes",
                ),
            ],
            "L3→L4": [
                RoadmapAction(
                    action_id="CSC_L3L4_001",
                    step=1,
                    title="Implement intelligent system orchestration",
                    description="AI decides which systems to query/update based on task. Optimizes for speed, cost, and relevance. No manual selection.",
                    effort_hours=20,
                    effort_weeks=4,
                    owners=["Architect"],
                    dependencies=[],
                    success_criteria="Orchestration reduces tool selection time by 80%+",
                    risk="Over-automation; unexpected system calls",
                ),
            ],
        }

        # ===== DIMENSION 7: QUALITY CONTROLS =====
        data["Quality Controls"] = {
            "L1→L2": [
                RoadmapAction(
                    action_id="QC_L1L2_001",
                    step=1,
                    title="Document code review checklist with AI items",
                    description="Create review checklist covering: logic, tests, security, style. Include AI-specific items: are generated tests sufficient? Is code readable?",
                    effort_hours=4,
                    effort_weeks=1,
                    owners=["Tech Lead"],
                    dependencies=[],
                    success_criteria="Checklist published; team uses it for 90%+ of reviews",
                    risk="Checklist too long; skipped",
                ),
                RoadmapAction(
                    action_id="QC_L1L2_002",
                    step=2,
                    title="Build /review skill for automated checks",
                    description="Implement /review skill: checks code style, catches common errors, generates test suggestions. Runs before human review.",
                    effort_hours=10,
                    effort_weeks=2,
                    owners=["Tech Lead"],
                    dependencies=["QC_L1L2_001"],
                    success_criteria="/review catches 80%+ of style issues; zero false positives on security",
                    risk="Over-flagging; blocks legitimate code",
                ),
                RoadmapAction(
                    action_id="QC_L1L2_003",
                    step=3,
                    title="Require /review before human review",
                    description="Configure CI/CD to require /review to pass before human review gates. Fail if critical issues found.",
                    effort_hours=4,
                    effort_weeks=1,
                    owners=["DevOps"],
                    dependencies=["QC_L1L2_002"],
                    success_criteria="All PRs reviewed by /review first; 0 merge blocks",
                    risk="Slows merge process; developer frustration",
                ),
                RoadmapAction(
                    action_id="QC_L1L2_004",
                    step=4,
                    title="Train team on review standards",
                    description="Workshop: what makes good code? How to use /review? How to interpret findings? Establish team norms.",
                    effort_hours=4,
                    effort_weeks=1,
                    owners=["Tech Lead"],
                    dependencies=["QC_L1L2_003"],
                    success_criteria="Training done; 90%+ attendance; team applies standards consistently",
                    risk="Low adoption; old habits persist",
                ),
            ],
            "L2→L3": [
                RoadmapAction(
                    action_id="QC_L2L3_001",
                    step=1,
                    title="Expand review to multiple quality dimensions",
                    description="Add reviews for: performance (O(n)? caching?), accessibility, internationalization, error handling, logging.",
                    effort_hours=12,
                    effort_weeks=2,
                    owners=["Tech Lead"],
                    dependencies=[],
                    success_criteria="Multi-dimensional review deployed; catches 15%+ more issues",
                    risk="Complexity; false positives",
                ),
                RoadmapAction(
                    action_id="QC_L2L3_002",
                    step=2,
                    title="Implement test quality validation",
                    description="AI reviews test code: are tests meaningful? Do they cover edge cases? Adequate setup/teardown? Suggest improvements.",
                    effort_hours=10,
                    effort_weeks=2,
                    owners=["Tech Lead"],
                    dependencies=["QC_L2L3_001"],
                    success_criteria="Test quality score increases 20%+; coverage improves",
                    risk="Generated suggestions wrong; not followed",
                ),
                RoadmapAction(
                    action_id="QC_L2L3_003",
                    step=3,
                    title="Add continuous quality monitoring",
                    description="Monitor code quality metrics over time: coverage, duplication, complexity, issue density. Alert on regressions.",
                    effort_hours=8,
                    effort_weeks=2,
                    owners=["DevOps"],
                    dependencies=["QC_L2L3_001"],
                    success_criteria="Dashboard live; catches 90%+ of regressions",
                    risk="Alert fatigue; noise",
                ),
            ],
            "L3→L4": [
                RoadmapAction(
                    action_id="QC_L3L4_001",
                    step=1,
                    title="Implement self-healing code review",
                    description="When /review finds issues, AI automatically generates fixes. Developer reviews and merges. Reduces manual rework.",
                    effort_hours=16,
                    effort_weeks=3,
                    owners=["Tech Lead"],
                    dependencies=[],
                    success_criteria="Auto-fixes resolve 70%+ of style issues",
                    risk="Loss of control; unexpected changes",
                ),
                RoadmapAction(
                    action_id="QC_L3L4_002",
                    step=2,
                    title="Enable predictive quality analysis",
                    description="AI predicts likelihood of defects in code pre-merge. Assigns risk score. Increases scrutiny for high-risk changes.",
                    effort_hours=14,
                    effort_weeks=3,
                    owners=["ML Engineer"],
                    dependencies=["QC_L3L4_001"],
                    success_criteria="Risk prediction accurate 85%+; guides review effort allocation",
                    risk="Bias in training data; over-flagging",
                ),
            ],
        }

        # ===== DIMENSION 8: SECURITY & COMPLIANCE =====
        data["Security & Compliance"] = {
            "L1→L2": [
                RoadmapAction(
                    action_id="SC_L1L2_001",
                    step=1,
                    title="Document AI usage policy",
                    description="Create formal policy on: what data can be sent to AI, what cannot (PII, secrets, proprietary). Review with legal/security.",
                    effort_hours=6,
                    effort_weeks=1,
                    owners=["Security", "Legal"],
                    dependencies=[],
                    success_criteria="Policy documented; signed off by leadership; communicated to team",
                    risk="Policy too restrictive; adoption low",
                ),
                RoadmapAction(
                    action_id="SC_L1L2_002",
                    step=2,
                    title="Implement data handling guardrails",
                    description="Build checks in Claude Code: detect PII/secrets before sending to AI. Block or warn. Log for audit.",
                    effort_hours=10,
                    effort_weeks=2,
                    owners=["Tech Lead", "Security"],
                    dependencies=["SC_L1L2_001"],
                    success_criteria="Guardrails active; zero accidental PII leaks in 1 month",
                    risk="False positives; over-blocking",
                ),
                RoadmapAction(
                    action_id="SC_L1L2_003",
                    step=3,
                    title="Set up AI session logging and audit",
                    description="Log all AI interactions: user, timestamp, model, tokens, cost. Store securely. Enable audit trails.",
                    effort_hours=8,
                    effort_weeks=2,
                    owners=["DevOps", "Security"],
                    dependencies=["SC_L1L2_001"],
                    success_criteria="Logs retained for 90 days; audit trail complete; compliance verified",
                    risk="Logging overhead; privacy concerns",
                ),
                RoadmapAction(
                    action_id="SC_L1L2_004",
                    step=4,
                    title="Train team on AI security",
                    description="Workshop: what's safe to send to AI? How to recognize PII? What to do if you accidentally leak data?",
                    effort_hours=4,
                    effort_weeks=1,
                    owners=["Security"],
                    dependencies=["SC_L1L2_002"],
                    success_criteria="Training delivered; 95%+ team completion; understanding confirmed",
                    risk="Training not retained",
                ),
            ],
            "L2→L3": [
                RoadmapAction(
                    action_id="SC_L2L3_001",
                    step=1,
                    title="Implement model selection governance",
                    description="Define which models can be used, when, and by whom. Document reasoning: cost, latency, security.",
                    effort_hours=6,
                    effort_weeks=1,
                    owners=["Architecture", "Security"],
                    dependencies=[],
                    success_criteria="Model selection policy enforced in code",
                    risk="Policy too prescriptive",
                ),
                RoadmapAction(
                    action_id="SC_L2L3_002",
                    step=2,
                    title="Add compliance reporting",
                    description="Generate reports on: AI usage by team member, data types sent, cost, compliance status. Share quarterly.",
                    effort_hours=8,
                    effort_weeks=2,
                    owners=["Compliance", "DevOps"],
                    dependencies=["SC_L2L3_001"],
                    success_criteria="Reports auto-generated; no compliance violations found",
                    risk="Report complexity; hard to interpret",
                ),
                RoadmapAction(
                    action_id="SC_L2L3_003",
                    step=3,
                    title="Implement data retention policies",
                    description="Define how long AI session data is retained. Encrypt at rest. Implement secure deletion.",
                    effort_hours=10,
                    effort_weeks=2,
                    owners=["Security", "DevOps"],
                    dependencies=["SC_L2L3_001"],
                    success_criteria="Retention policy enforced; encryption verified; audit confirms",
                    risk="Data loss; recovery issues",
                ),
            ],
            "L3→L4": [
                RoadmapAction(
                    action_id="SC_L3L4_001",
                    step=1,
                    title="Implement adaptive security controls",
                    description="Security controls learn from usage patterns. Flag anomalous behavior (unusual data, off-hours, unusual user).",
                    effort_hours=16,
                    effort_weeks=3,
                    owners=["Security"],
                    dependencies=[],
                    success_criteria="Anomaly detection catches 90%+ of suspicious activity",
                    risk="False positives; disruption",
                ),
                RoadmapAction(
                    action_id="SC_L3L4_002",
                    step=2,
                    title="Enable zero-trust verification",
                    description="Every AI request verified: user identity, device posture, network location. MFA required for sensitive operations.",
                    effort_hours=12,
                    effort_weeks=2,
                    owners=["Security"],
                    dependencies=["SC_L3L4_001"],
                    success_criteria="Zero-trust model deployed; zero unauthorized accesses",
                    risk="User friction; adoption resistance",
                ),
            ],
        }

        # ===== DIMENSION 9: MEASUREMENT & KPIs =====
        data["Measurement & KPIs"] = {
            "L1→L2": [
                RoadmapAction(
                    action_id="MK_L1L2_001",
                    step=1,
                    title="Define AI adoption metrics",
                    description="Choose metrics: % of team using AI, sessions/day, messages/session, skill invocations, code review adoption.",
                    effort_hours=4,
                    effort_weeks=1,
                    owners=["Analytics", "Leadership"],
                    dependencies=[],
                    success_criteria="3-5 key metrics selected; baseline established",
                    risk="Wrong metrics chosen; changing later",
                ),
                RoadmapAction(
                    action_id="MK_L1L2_002",
                    step=2,
                    title="Set up metrics collection infrastructure",
                    description="Build logging/tracking for chosen metrics. Integrate with analytics platform. Automate daily collection.",
                    effort_hours=8,
                    effort_weeks=2,
                    owners=["DevOps", "Analytics"],
                    dependencies=["MK_L1L2_001"],
                    success_criteria="Metrics collected daily with <5% downtime",
                    risk="Data quality issues; gaps",
                ),
                RoadmapAction(
                    action_id="MK_L1L2_003",
                    step=3,
                    title="Create metrics dashboard",
                    description="Build dashboard showing adoption trends, team participation, skill usage. Refresh weekly. Share with leadership.",
                    effort_hours=6,
                    effort_weeks=1,
                    owners=["Analytics"],
                    dependencies=["MK_L1L2_002"],
                    success_criteria="Dashboard live; metrics visible to 100% of team",
                    risk="Dashboard not used; metrics ignored",
                ),
                RoadmapAction(
                    action_id="MK_L1L2_004",
                    step=4,
                    title="Establish baseline and targets",
                    description="Document current metrics (baseline). Set targets for next quarter. Define how targets will be achieved.",
                    effort_hours=4,
                    effort_weeks=1,
                    owners=["Leadership"],
                    dependencies=["MK_L1L2_003"],
                    success_criteria="Targets published; team aligned; progress tracked",
                    risk="Targets unrealistic; demoralizing",
                ),
            ],
            "L2→L3": [
                RoadmapAction(
                    action_id="MK_L2L3_001",
                    step=1,
                    title="Add business impact metrics",
                    description="Track: cycle time (pre/post AI), defect escape rate, customer satisfaction, team satisfaction. Correlate with AI adoption.",
                    effort_hours=10,
                    effort_weeks=2,
                    owners=["Analytics", "Product"],
                    dependencies=[],
                    success_criteria="Impact metrics show 15%+ improvement in cycle time",
                    risk="Causation hard to prove; confounding factors",
                ),
                RoadmapAction(
                    action_id="MK_L2L3_002",
                    step=2,
                    title="Implement cost tracking",
                    description="Track AI costs: API usage, compute, licenses. Break down by team, project, tool. Optimize high-cost areas.",
                    effort_hours=8,
                    effort_weeks=1,
                    owners=["Finance", "DevOps"],
                    dependencies=["MK_L2L3_001"],
                    success_criteria="Cost tracking accurate; 20%+ optimization achieved",
                    risk="Attribution complex; false economy",
                ),
                RoadmapAction(
                    action_id="MK_L2L3_003",
                    step=3,
                    title="Build predictive KPI models",
                    description="Use historical data to predict future adoption, velocity, cost. Enable forecasting and planning.",
                    effort_hours=12,
                    effort_weeks=2,
                    owners=["Analytics"],
                    dependencies=["MK_L2L3_001"],
                    success_criteria="Predictions accurate within ±10%; used for planning",
                    risk="Data too sparse; inaccurate predictions",
                ),
            ],
            "L3→L4": [
                RoadmapAction(
                    action_id="MK_L3L4_001",
                    step=1,
                    title="Implement autonomous KPI optimization",
                    description="System automatically tunes parameters (model choice, agent behavior, tool selection) to optimize KPIs.",
                    effort_hours=18,
                    effort_weeks=3,
                    owners=["ML Engineer"],
                    dependencies=[],
                    success_criteria="KPIs improve 10%+ without manual intervention",
                    risk="Unexpected side effects; loss of control",
                ),
            ],
        }

        # ===== DIMENSION 10: WAYS OF WORKING =====
        data["Ways of Working"] = {
            "L1→L2": [
                RoadmapAction(
                    action_id="WOW_L1L2_001",
                    step=1,
                    title="Document AI Ways of Working",
                    description="Create 1-2 page guide: how to start an AI session, load context, structure prompts, use shared tools, when to use plan mode.",
                    effort_hours=6,
                    effort_weeks=1,
                    owners=["AI Champion"],
                    dependencies=[],
                    success_criteria="Guide published; linked from CLAUDE.md; referenced by 80%+ of team",
                    risk="Not adopted; habits don't change",
                ),
                RoadmapAction(
                    action_id="WOW_L1L2_002",
                    step=2,
                    title="Establish session protocols",
                    description="Define standard: load CLAUDE.md first, set constraints, include relevant files, save session summaries. Make it a habit.",
                    effort_hours=4,
                    effort_weeks=1,
                    owners=["AI Champion"],
                    dependencies=["WOW_L1L2_001"],
                    success_criteria="Protocols documented; 80%+ adoption in logs",
                    risk="Low adoption; perceived as overhead",
                ),
                RoadmapAction(
                    action_id="WOW_L1L2_003",
                    step=3,
                    title="Create role-specific playbooks",
                    description="Playbooks for: Frontend Dev (UI tasks), Backend (API design), QA (test strategy), DevOps (infra). Include AI workflows.",
                    effort_hours=8,
                    effort_weeks=2,
                    owners=["AI Champion"],
                    dependencies=["WOW_L1L2_001"],
                    success_criteria="Playbooks adopted by 70%+ of their respective teams",
                    risk="Playbooks too prescriptive; not followed",
                ),
                RoadmapAction(
                    action_id="WOW_L1L2_004",
                    step=4,
                    title="Hold AI practice review meetings",
                    description="Bi-weekly: review how team is using AI. Share wins, discuss blockers, refine practices. Share session wins.",
                    effort_hours=2,
                    effort_weeks=0.5,  # Recurring, not one-time
                    owners=["AI Champion"],
                    dependencies=["WOW_L1L2_003"],
                    success_criteria="Meetings held 2x/month; 80%+ attendance; action items addressed",
                    risk="Meetings become theater; no action",
                ),
            ],
            "L2→L3": [
                RoadmapAction(
                    action_id="WOW_L2L3_001",
                    step=1,
                    title="Implement workflow automation",
                    description="Automate common workflows: file loading, context retrieval, model selection, session logging. Reduce manual steps.",
                    effort_hours=12,
                    effort_weeks=2,
                    owners=["Tech Lead"],
                    dependencies=[],
                    success_criteria="Automation reduces setup time by 60%+",
                    risk="Over-automation; loss of control",
                ),
                RoadmapAction(
                    action_id="WOW_L2L3_002",
                    step=2,
                    title="Build AI-assisted task selection",
                    description="System recommends best AI approach for a given task (direct generation, plan mode, multi-step agent). Guidance improves over time.",
                    effort_hours=10,
                    effort_weeks=2,
                    owners=["Architect"],
                    dependencies=["WOW_L2L3_001"],
                    success_criteria="Recommendations accurate 80%+; team uses them",
                    risk="Recommendations too rigid; limit flexibility",
                ),
                RoadmapAction(
                    action_id="WOW_L2L3_003",
                    step=3,
                    title="Enable workflow templates and shortcuts",
                    description="Pre-configured workflows for common tasks: start sprint, do code review, release, debug, refactor. One-click invocation.",
                    effort_hours=8,
                    effort_weeks=2,
                    owners=["AI Champion"],
                    dependencies=["WOW_L2L3_001"],
                    success_criteria="Templates used for 60%+ of tasks; time savings quantified",
                    risk="Templates not maintained; go stale",
                ),
            ],
            "L3→L4": [
                RoadmapAction(
                    action_id="WOW_L3L4_001",
                    step=1,
                    title="Implement adaptive workflows",
                    description="Workflows learn from team preferences. Adjust recommendations, defaults, and suggestions based on actual usage patterns.",
                    effort_hours=14,
                    effort_weeks=3,
                    owners=["ML Engineer"],
                    dependencies=[],
                    success_criteria="Personalization increases adoption 15%+",
                    risk="Over-personalization; unexpected behavior",
                ),
            ],
        }

        # ===== DIMENSION 11: ACCOUNTABILITY & OWNERSHIP =====
        data["Accountability & Ownership"] = {
            "L1→L2": [
                RoadmapAction(
                    action_id="AO_L1L2_001",
                    step=1,
                    title="Designate AI Champion role",
                    description="Identify and formally assign AI Champion. Document role: maintain CLAUDE.md, own skill development, drive adoption, answer questions.",
                    effort_hours=2,
                    effort_weeks=1,
                    owners=["Leadership"],
                    dependencies=[],
                    success_criteria="Champion appointed; role documented; dedicated time allocated (20% minimum)",
                    risk="Wrong person chosen; insufficient time allocated",
                ),
                RoadmapAction(
                    action_id="AO_L1L2_002",
                    step=2,
                    title="Establish AI governance board",
                    description="Create small board: Champion, Tech Lead, PM, optional Security. Meet monthly to discuss strategy, approve new skills, address concerns.",
                    effort_hours=2,
                    effort_weeks=1,
                    owners=["Leadership"],
                    dependencies=["AO_L1L2_001"],
                    success_criteria="Board established; first 3 meetings held; decisions documented",
                    risk="Board becomes rubber-stamp; no real decision authority",
                ),
                RoadmapAction(
                    action_id="AO_L1L2_003",
                    step=3,
                    title="Define accountability metrics",
                    description="What is Champion accountable for? Metrics: adoption rate, skill coverage, team satisfaction, velocity improvement.",
                    effort_hours=4,
                    effort_weeks=1,
                    owners=["Leadership"],
                    dependencies=["AO_L1L2_002"],
                    success_criteria="Metrics defined; targets set; Champion aligned",
                    risk="Metrics too strict; demoralizing",
                ),
                RoadmapAction(
                    action_id="AO_L1L2_004",
                    step=4,
                    title="Create knowledge handoff documentation",
                    description="Champion documents: how skills are built, how to maintain CLAUDE.md, decision processes, known issues. Enables backup.",
                    effort_hours=6,
                    effort_weeks=1,
                    owners=["AI Champion"],
                    dependencies=["AO_L1L2_001"],
                    success_criteria="Documentation complete; one backup trained",
                    risk="Documentation incomplete; hard to transfer",
                ),
            ],
            "L2→L3": [
                RoadmapAction(
                    action_id="AO_L2L3_001",
                    step=1,
                    title="Implement distributed ownership model",
                    description="Skill/domain owners: each team member owns 1-2 skills. Champion provides guidance. Reduces single-point-of-failure.",
                    effort_hours=4,
                    effort_weeks=1,
                    owners=["AI Champion"],
                    dependencies=[],
                    success_criteria="Ownership matrix created; every skill has 2+ owners",
                    risk="Diffuse responsibility; nothing owned well",
                ),
                RoadmapAction(
                    action_id="AO_L2L3_002",
                    step=2,
                    title="Establish skill review cycles",
                    description="Quarterly: each skill owner reviews their skills. Update, deprecate, or archive as needed. Report to governance board.",
                    effort_hours=4,
                    effort_weeks=0.5,  # Recurring quarterly
                    owners=["AI Champion"],
                    dependencies=["AO_L2L3_001"],
                    success_criteria="Review cycles established; skills kept current",
                    risk="Reviews become checkbox; no real maintenance",
                ),
                RoadmapAction(
                    action_id="AO_L2L3_003",
                    step=3,
                    title="Link AI metrics to team performance reviews",
                    description="Include AI adoption/contribution in individual performance reviews. Recognize high performers. Motivate laggards.",
                    effort_hours=4,
                    effort_weeks=1,
                    owners=["HR", "Leadership"],
                    dependencies=["AO_L2L3_001"],
                    success_criteria="Metrics integrated into reviews; first cycle complete",
                    risk="Creates perverse incentives; gaming metrics",
                ),
            ],
            "L3→L4": [
                RoadmapAction(
                    action_id="AO_L3L4_001",
                    step=1,
                    title="Enable autonomous ownership delegation",
                    description="System recommends or automatically delegates skill ownership based on expertise, capacity, growth goals. Humans can override.",
                    effort_hours=12,
                    effort_weeks=2,
                    owners=["Architect"],
                    dependencies=[],
                    success_criteria="Delegations made autonomously; 90%+ acceptance rate",
                    risk="Over-automation; poor fit decisions",
                ),
            ],
        }

        # ===== DIMENSION 12: SCALABILITY & KNOWLEDGE TRANSFER =====
        data["Scalability & Knowledge Transfer"] = {
            "L1→L2": [
                RoadmapAction(
                    action_id="SKT_L1L2_001",
                    step=1,
                    title="Create AI onboarding module",
                    description="For new developers: 30-minute module covering what is Claude Code, how the team uses it, where to get help. Recorded video + slides.",
                    effort_hours=6,
                    effort_weeks=1,
                    owners=["AI Champion"],
                    dependencies=[],
                    success_criteria="Module created; 100% of new hires complete it",
                    risk="Module outdated; not updated",
                ),
                RoadmapAction(
                    action_id="SKT_L1L2_002",
                    step=2,
                    title="Build prompt/skill library with examples",
                    description="Curate library of working prompts, shared skills, common patterns. Include examples: before/after, dos/don'ts.",
                    effort_hours=8,
                    effort_weeks=1,
                    owners=["AI Champion"],
                    dependencies=["SKT_L1L2_001"],
                    success_criteria="Library has 15+ entries; new hires use it for 80% of tasks",
                    risk="Library not discovered; low adoption",
                ),
                RoadmapAction(
                    action_id="SKT_L1L2_003",
                    step=3,
                    title="Establish buddy/pairing program",
                    description="Pair new developers with experienced AI users. 2-3 paired sessions in first week. Accelerates ramp time.",
                    effort_hours=2,
                    effort_weeks=1,
                    owners=["AI Champion"],
                    dependencies=["SKT_L1L2_001"],
                    success_criteria="Program operational; new dev ramp time reduced by 30%",
                    risk="Low participation from buddies",
                ),
                RoadmapAction(
                    action_id="SKT_L1L2_004",
                    step=4,
                    title="Measure ramp-up time",
                    description="Track metrics for new hires: days to first AI usage, days to productive usage (5+ daily interactions), independent task completion.",
                    effort_hours=4,
                    effort_weeks=1,
                    owners=["Analytics"],
                    dependencies=["SKT_L1L2_003"],
                    success_criteria="Metrics tracked; baseline established; improvement visible",
                    risk="Metrics hard to define; data collection slow",
                ),
            ],
            "L2→L3": [
                RoadmapAction(
                    action_id="SKT_L2L3_001",
                    step=1,
                    title="Implement AI certification program",
                    description="Multi-level certification: Beginner (knows tools), Intermediate (writes good prompts), Advanced (owns skills). Badge system.",
                    effort_hours=10,
                    effort_weeks=2,
                    owners=["AI Champion"],
                    dependencies=[],
                    success_criteria="Program launched; 50%+ of team certified at some level",
                    risk="Certification becomes burden; cheating",
                ),
                RoadmapAction(
                    action_id="SKT_L2L3_002",
                    step=2,
                    title="Create advanced training course",
                    description="For developers ready to develop skills: architecture, testing, debugging, deployment. 4-week course. 10 hours per week.",
                    effort_hours=30,  # Initial creation
                    effort_weeks=2,
                    owners=["Tech Lead"],
                    dependencies=["SKT_L2L3_001"],
                    success_criteria="Course delivered; 5+ developers upskilled; 2+ new skills created",
                    risk="Course not completed; low engagement",
                ),
                RoadmapAction(
                    action_id="SKT_L2L3_003",
                    step=3,
                    title="Build knowledge base and wiki",
                    description="Comprehensive wiki: FAQs, troubleshooting, skill development guide, case studies. Searchable, regularly updated.",
                    effort_hours=12,
                    effort_weeks=2,
                    owners=["AI Champion"],
                    dependencies=["SKT_L2L3_001"],
                    success_criteria="Wiki launched; 100+ articles; used for 60%+ of questions",
                    risk="Wiki goes stale; information out of date",
                ),
            ],
            "L3→L4": [
                RoadmapAction(
                    action_id="SKT_L3L4_001",
                    step=1,
                    title="Implement AI-assisted onboarding",
                    description="AI generates personalized onboarding path based on new hire's background, role, goals. Adaptive learning.",
                    effort_hours=14,
                    effort_weeks=2,
                    owners=["ML Engineer"],
                    dependencies=[],
                    success_criteria="New dev ramp time reduced to <2 weeks; satisfaction 4.5/5",
                    risk="Personalization too narrow; not generalizable",
                ),
                RoadmapAction(
                    action_id="SKT_L3L4_002",
                    step=2,
                    title="Enable self-service skill learning",
                    description="Developers can learn and deploy new skills autonomously using provided templates/framework. No Champion approval required (post-review).",
                    effort_hours=12,
                    effort_weeks=2,
                    owners=["Tech Lead"],
                    dependencies=["SKT_L3L4_001"],
                    success_criteria="Self-service skills deployed; quality acceptable; community-driven",
                    risk="Quality degrades; maintenance burden",
                ),
            ],
        }

        return data

    def generate_roadmap_for_dimension(
        self, dimension: str, current_level: int, target_level: int
    ) -> RoadmapItem:
        """
        Generate a roadmap for a single dimension's transition.

        Args:
            dimension: Name of the dimension (one of 12)
            current_level: Current maturity level (1-4)
            target_level: Target level (typically current_level + 1)

        Returns:
            RoadmapItem with actions, effort estimates, and key insight

        Raises:
            ValueError: If dimension not found or invalid level range
        """
        if dimension not in self._roadmap_data:
            available = ", ".join(sorted(self._roadmap_data.keys()))
            raise ValueError(
                f"Dimension '{dimension}' not found. Available: {available}"
            )

        if not (1 <= current_level <= 4) or not (1 <= target_level <= 4):
            raise ValueError("Levels must be between 1 and 4")

        if target_level <= current_level:
            raise ValueError("Target level must be greater than current level")

        transition_key = f"L{current_level}→L{target_level}"
        dim_data = self._roadmap_data.get(dimension, {})

        if transition_key not in dim_data:
            raise ValueError(
                f"No roadmap found for {dimension} transition {transition_key}"
            )

        actions = dim_data[transition_key]
        total_effort_hours = sum(a.effort_hours for a in actions)
        total_effort_weeks = sum(a.effort_weeks for a in actions)

        # Generate key insight based on transition
        key_insights = {
            "L1→L2": f"Shift from ad-hoc {dimension.lower()} to documented, enforced practices",
            "L2→L3": f"Automate {dimension.lower()} with multi-step workflows and intelligent decision-making",
            "L3→L4": f"Enable fully autonomous {dimension.lower()} with self-improving systems",
        }
        key_insight = key_insights.get(transition_key, "Progress to next maturity level")

        return RoadmapItem(
            dimension=dimension,
            current_level=current_level,
            target_level=target_level,
            actions=actions,
            total_effort_hours=total_effort_hours,
            total_effort_weeks=total_effort_weeks,
            key_insight=key_insight,
        )

    def generate_all_roadmaps(
        self, dimensions_and_levels: Dict[str, int]
    ) -> List[RoadmapItem]:
        """
        Generate roadmaps for all dimensions to their next level.

        Args:
            dimensions_and_levels: Dict mapping dimension name → current level (1-4)

        Returns:
            List of RoadmapItem objects, one per dimension
        """
        roadmaps = []

        for dimension, current_level in dimensions_and_levels.items():
            if current_level >= 4:
                # Already at max level - create a placeholder roadmap
                roadmap = RoadmapItem(
                    dimension=dimension,
                    current_level=4,
                    target_level=4,
                    actions=[],
                    total_effort_hours=0,
                    total_effort_weeks=0,
                    key_insight="This dimension is at the highest maturity level (L4). Continue to maintain and refine practices.",
                )
                roadmaps.append(roadmap)
                continue

            target_level = current_level + 1
            roadmap = self.generate_roadmap_for_dimension(
                dimension, current_level, target_level
            )
            roadmaps.append(roadmap)

        return roadmaps
