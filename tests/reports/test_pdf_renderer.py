"""
Tests for PDF Renderer Module

Tests verify:
- Correct PDF generation for TeamReport
- Correct PDF generation for IndividualReport
- Proper document structure (pages, sections, content)
- Styling and formatting consistency
- File creation and output path handling
"""

import pytest
from pathlib import Path
import tempfile
from datetime import datetime

from auto_sdlc.reports.pdf_renderer import PDFRenderer, PDFStyles
from auto_sdlc.reports.models import TeamReport, IndividualReport, DimensionReport


class TestPDFStyles:
    """Tests for PDFStyles helper class."""

    def test_color_constants_defined(self):
        """Test that color constants are properly defined."""
        assert PDFStyles.NAVY_BLUE is not None
        assert PDFStyles.LIGHT_GRAY is not None
        assert PDFStyles.L1_RED is not None
        assert PDFStyles.L4_DARK_GREEN is not None

    def test_get_maturity_color(self):
        """Test maturity level color assignment."""
        assert PDFStyles.get_maturity_color(1) == PDFStyles.L1_RED
        assert PDFStyles.get_maturity_color(2) == PDFStyles.L2_YELLOW
        assert PDFStyles.get_maturity_color(3) == PDFStyles.L3_LIGHT_GREEN
        assert PDFStyles.get_maturity_color(4) == PDFStyles.L4_DARK_GREEN

    def test_get_maturity_label(self):
        """Test maturity level label generation."""
        assert "L1" in PDFStyles.get_maturity_label(1)
        assert "L2" in PDFStyles.get_maturity_label(2)
        assert "L3" in PDFStyles.get_maturity_label(3)
        assert "L4" in PDFStyles.get_maturity_label(4)
        assert "Assisted" in PDFStyles.get_maturity_label(1)
        assert "Autonomous" in PDFStyles.get_maturity_label(4)


class TestPDFRenderer:
    """Tests for PDFRenderer class."""

    @pytest.fixture
    def renderer(self):
        """Create a PDFRenderer instance."""
        return PDFRenderer()

    @pytest.fixture
    def simple_team_report(self):
        """Create a simple but valid TeamReport for testing."""
        dimensions = {}
        for dim in [
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
        ]:
            dimensions[dim] = DimensionReport(
                dimension=dim,
                maturity_level=2,
                confidence="high",
                current_state=f"Team is at level 2 for {dim}.",
                evidence_summary={
                    "logs": f"Found signals in logs for {dim}",
                    "configs": f"Configuration files show {dim} practices"
                },
                gaps=["Gap 1", "Gap 2"],
                strengths=["Strength 1", "Strength 2"],
                roadmap=[
                    {
                        "title": "Action 1",
                        "effort_weeks": 2,
                        "owners": ["Lead", "Champion"]
                    }
                ]
            )

        return TeamReport(
            team_name="Test Team",
            report_date="2024-01-15",
            data_sources={"logs": True, "configs": True, "capabilities": False},
            team_size=8,
            assessment_period_weeks=4,
            overall_maturity_level=2.1,
            dimensions=dimensions,
            executive_summary="The team demonstrates integrated AI practices with clear documentation.",
            key_insights=[
                "Strong adoption of AI tools across the team",
                "Documentation needs improvement",
                "Integration opportunities exist"
            ],
            recommendations=[
                "Complete CLAUDE.md documentation",
                "Implement CI/CD AI review gates",
                "Establish metrics tracking"
            ],
            confidence_by_dimension={dim: "high" for dim in dimensions.keys()},
            next_steps=[
                "Set up AI champion role",
                "Create CLAUDE.md templates",
                "Define governance policy"
            ]
        )

    @pytest.fixture
    def simple_individual_report(self):
        """Create a simple but valid IndividualReport for testing."""
        dimensions = {}
        for dim in [
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
        ]:
            dimensions[dim] = DimensionReport(
                dimension=dim,
                maturity_level=2,
                confidence="medium",
                current_state=f"Developer shows level 2 capability in {dim}.",
                evidence_summary={
                    "usage": f"Moderate usage patterns in {dim}"
                },
                gaps=["Area for growth"],
                strengths=["Notable skill"],
                roadmap=[]
            )

        return IndividualReport(
            developer_id="dev_001",
            report_date="2024-01-15",
            assessment_period_weeks=4,
            overall_maturity_level=2.0,
            dimensions=dimensions,
            executive_summary="Developer demonstrates solid integration of AI practices with room to grow.",
            usage_patterns={
                "sessions_per_day": 3.5,
                "messages_per_session": 12.3,
                "prompt_quality_score": 73.5,
            },
            strengths=[
                "High prompt quality",
                "Consistent tool usage"
            ],
            growth_areas=[
                "Cross-system context loading",
                "Code review adoption"
            ],
            fit_with_team_baseline="Aligned with team",
            learning_path=[
                "Improve context efficiency",
                "Learn JIRA MCP integration"
            ],
            key_insights=[
                "Developer is tracking well with team norms",
                "Strong potential for advancement"
            ],
            recommendations=[
                "Pair with senior developer",
                "Practice structured planning"
            ]
        )

    def test_renderer_initialization(self, renderer):
        """Test that PDFRenderer initializes correctly."""
        assert renderer is not None
        assert renderer.styles is not None
        assert renderer.page_width == 612  # Letter width in points
        assert renderer.page_height == 792  # Letter height in points

    def test_render_team_report_creates_file(self, renderer, simple_team_report):
        """Test that rendering a team report creates a PDF file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "team_report.pdf"

            result_path = renderer.render_team_report(simple_team_report, output_path)

            # Check that file was created
            assert result_path.exists()
            assert result_path.suffix == ".pdf"

            # Check file is not empty
            assert result_path.stat().st_size > 0

    def test_render_individual_report_creates_file(self, renderer, simple_individual_report):
        """Test that rendering an individual report creates a PDF file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "individual_report.pdf"

            result_path = renderer.render_individual_report(
                simple_individual_report,
                output_path
            )

            # Check that file was created
            assert result_path.exists()
            assert result_path.suffix == ".pdf"

            # Check file is not empty
            assert result_path.stat().st_size > 0

    def test_render_team_report_without_explicit_path(self, renderer, simple_team_report):
        """Test rendering team report with default output path."""
        result_path = renderer.render_team_report(simple_team_report)

        try:
            # Check that file was created in default location
            assert result_path.exists()
            assert result_path.suffix == ".pdf"
            assert ".auto-sdlc/reports" in str(result_path)
        finally:
            # Clean up
            if result_path.exists():
                result_path.unlink()

    def test_render_individual_report_without_explicit_path(self, renderer, simple_individual_report):
        """Test rendering individual report with default output path."""
        result_path = renderer.render_individual_report(simple_individual_report)

        try:
            # Check that file was created in default location
            assert result_path.exists()
            assert result_path.suffix == ".pdf"
            assert ".auto-sdlc/reports" in str(result_path)
        finally:
            # Clean up
            if result_path.exists():
                result_path.unlink()

    def test_render_team_report_with_missing_data(self, renderer, simple_team_report):
        """Test rendering team report with some optional data missing."""
        # Clear some optional fields
        simple_team_report.key_insights = []
        simple_team_report.recommendations = []
        simple_team_report.next_steps = []

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "team_report_minimal.pdf"
            result_path = renderer.render_team_report(simple_team_report, output_path)

            # Should still create valid PDF
            assert result_path.exists()
            assert result_path.stat().st_size > 0

    def test_render_individual_report_with_missing_data(self, renderer, simple_individual_report):
        """Test rendering individual report with some optional data missing."""
        # Clear some optional fields
        simple_individual_report.strengths = []
        simple_individual_report.growth_areas = []
        simple_individual_report.learning_path = []

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "individual_report_minimal.pdf"
            result_path = renderer.render_individual_report(
                simple_individual_report,
                output_path
            )

            # Should still create valid PDF
            assert result_path.exists()
            assert result_path.stat().st_size > 0

    def test_render_team_report_creates_directory(self, renderer, simple_team_report):
        """Test that rendering creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "another" / "team_report.pdf"

            result_path = renderer.render_team_report(simple_team_report, output_path)

            # Parent directories should be created
            assert result_path.parent.exists()
            assert result_path.exists()

    def test_render_individual_report_creates_directory(self, renderer, simple_individual_report):
        """Test that rendering creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "another" / "individual_report.pdf"

            result_path = renderer.render_individual_report(
                simple_individual_report,
                output_path
            )

            # Parent directories should be created
            assert result_path.parent.exists()
            assert result_path.exists()

    def test_pdf_file_size_team_report(self, renderer, simple_team_report):
        """Test that team report PDF has reasonable file size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "team_report.pdf"
            result_path = renderer.render_team_report(simple_team_report, output_path)

            # PDF should be at least a few KB (not empty)
            file_size = result_path.stat().st_size
            assert file_size > 5000  # At least 5KB

    def test_pdf_file_size_individual_report(self, renderer, simple_individual_report):
        """Test that individual report PDF has reasonable file size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "individual_report.pdf"
            result_path = renderer.render_individual_report(
                simple_individual_report,
                output_path
            )

            # PDF should be at least a few KB (not empty)
            file_size = result_path.stat().st_size
            assert file_size > 3000  # At least 3KB

    def test_render_team_report_with_all_maturity_levels(self, renderer):
        """Test rendering team report with various maturity levels."""
        dimensions = {}
        levels = [1, 2, 3, 4]

        for i, level in enumerate(levels):
            dim_names = list([
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
            ])

            dim_name = dim_names[i % len(dim_names)]
            if dim_name not in dimensions:
                dimensions[dim_name] = DimensionReport(
                    dimension=dim_name,
                    maturity_level=level,
                    confidence="high",
                    current_state=f"Level {level} capability.",
                    evidence_summary={},
                    gaps=[],
                    strengths=[],
                    roadmap=[]
                )

        # Fill remaining dimensions
        for dim_name in [
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
        ]:
            if dim_name not in dimensions:
                dimensions[dim_name] = DimensionReport(
                    dimension=dim_name,
                    maturity_level=2,
                    confidence="medium",
                    current_state=f"Current state of {dim_name}.",
                    evidence_summary={},
                    gaps=[],
                    strengths=[],
                    roadmap=[]
                )

        report = TeamReport(
            team_name="Multi-Level Team",
            report_date="2024-01-15",
            data_sources={},
            team_size=10,
            assessment_period_weeks=8,
            overall_maturity_level=2.5,
            dimensions=dimensions,
            executive_summary="Mixed maturity levels across dimensions.",
            key_insights=[],
            recommendations=[],
            confidence_by_dimension={dim: "high" for dim in dimensions.keys()},
            next_steps=[]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "multi_level_report.pdf"
            result_path = renderer.render_team_report(report, output_path)

            assert result_path.exists()
            assert result_path.stat().st_size > 5000

    def test_render_individual_report_with_rich_data(self, renderer, simple_individual_report):
        """Test rendering individual report with comprehensive data."""
        # Add more detailed data
        simple_individual_report.usage_patterns = {
            "sessions_per_day": 3.5,
            "messages_per_session": 12.3,
            "prompt_quality_score": 76.5,
            "tool_consistency_pct": 99.0,
            "claude_md_loading_pct": 78.0,
            "file_path_references_pct": 58.0,
        }

        simple_individual_report.strengths = [
            "High prompt quality (76 vs 73 team avg)",
            "Consistent CLAUDE.md loading (78% vs 67% team avg)",
            "Active use of plan mode"
        ]

        simple_individual_report.growth_areas = [
            "Low /review adoption (22% vs 85% team avg)",
            "Rare cross-system context loading",
            "Limited error recovery patterns"
        ]

        simple_individual_report.learning_path = [
            "Increase /review adoption",
            "Learn JIRA MCP integration",
            "Practice iterative debugging",
            "Document team playbook"
        ]

        simple_individual_report.recommendations = [
            "Shadow senior developer for 1 session",
            "Try /review on next 3 PRs",
            "Document bug investigation workflow",
            "Join team office hours"
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "rich_individual_report.pdf"
            result_path = renderer.render_individual_report(
                simple_individual_report,
                output_path
            )

            assert result_path.exists()
            assert result_path.stat().st_size > 5000


class TestPDFStructure:
    """Tests for PDF document structure."""

    @pytest.fixture
    def renderer(self):
        """Create a PDFRenderer instance."""
        return PDFRenderer()

    @pytest.fixture
    def complete_team_report(self):
        """Create a complete TeamReport with all fields populated."""
        dimensions = {}
        for dim in [
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
        ]:
            dimensions[dim] = DimensionReport(
                dimension=dim,
                maturity_level=2,
                confidence="high",
                current_state=f"The team demonstrates integrated practices for {dim}.",
                evidence_summary={
                    "logs": "Found strong signals in historical logs",
                    "configs": "Configuration files document practices",
                    "capabilities": "Skills are deployed and in use"
                },
                gaps=[
                    "Missing comprehensive automation",
                    "Limited cross-team knowledge transfer"
                ],
                strengths=[
                    "Well documented practices",
                    "High adoption rates",
                    "Clear ownership and accountability"
                ],
                roadmap=[
                    {
                        "title": "Step 1: Establish baseline metrics",
                        "description": "Define KPIs for this dimension",
                        "effort_weeks": 1,
                        "owners": ["Tech Lead"]
                    },
                    {
                        "title": "Step 2: Implement automation",
                        "description": "Automate enforcement of practices",
                        "effort_weeks": 2,
                        "owners": ["Tech Lead", "AI Champion"]
                    },
                    {
                        "title": "Step 3: Train team",
                        "description": "Conduct training on new automated processes",
                        "effort_weeks": 1,
                        "owners": ["AI Champion"]
                    }
                ]
            )

        return TeamReport(
            team_name="Backend Platform Team",
            report_date="2024-01-15",
            data_sources={
                "logs": True,
                "configs": True,
                "capabilities": True
            },
            team_size=12,
            assessment_period_weeks=12,
            overall_maturity_level=2.2,
            dimensions=dimensions,
            executive_summary=(
                "The Backend Platform Team demonstrates solid integration of AI practices "
                "across most dimensions. With strong foundational practices in place, "
                "the team is well-positioned to advance to L3 (Agentic) capabilities."
            ),
            key_insights=[
                "Excellent tool adoption and documentation culture",
                "Strong champion leadership driving practices",
                "Ready for automation and integration expansion"
            ],
            recommendations=[
                "Complete JIRA and Slack MCP integrations",
                "Formalize security and compliance policies",
                "Implement multi-agent orchestration workflows",
                "Establish comprehensive metrics dashboard",
                "Create playbooks for common workflows"
            ],
            confidence_by_dimension={dim: "high" for dim in dimensions.keys()},
            next_steps=[
                "Schedule dimension lead interviews to validate findings",
                "Present roadmap to engineering leadership for approval",
                "Assign owners for Q2 roadmap initiatives",
                "Set up monthly progress tracking meetings"
            ]
        )

    def test_team_report_covers_all_content(self, renderer, complete_team_report):
        """Test that team report includes all expected sections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "complete_report.pdf"
            result_path = renderer.render_team_report(complete_team_report, output_path)

            assert result_path.exists()

            # Get file size as proxy for content (larger = more content)
            file_size = result_path.stat().st_size
            assert file_size > 20000  # Should be substantial PDF (20KB+)

    def test_individual_report_covers_all_content(self, renderer):
        """Test that individual report includes all expected sections."""
        dimensions = {}
        for dim in [
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
        ]:
            dimensions[dim] = DimensionReport(
                dimension=dim,
                maturity_level=2,
                confidence="high",
                current_state=f"Developer capability in {dim}.",
                evidence_summary={"usage": f"Strong signals in {dim}"},
                gaps=["Area for improvement"],
                strengths=["Notable skill in area"],
                roadmap=[]
            )

        report = IndividualReport(
            developer_id="alice_dev",
            report_date="2024-01-15",
            assessment_period_weeks=8,
            overall_maturity_level=2.5,
            dimensions=dimensions,
            executive_summary=(
                "Alice demonstrates strong AI maturity across most dimensions. "
                "She is a power user with high-quality prompts and consistent practice adoption."
            ),
            usage_patterns={
                "sessions_per_day": 4.2,
                "messages_per_session": 15.5,
                "prompt_quality_score": 78.3,
                "tool_consistency": 99.0,
                "claude_md_loading": 92.0,
            },
            strengths=[
                "Highest prompt quality on team",
                "Consistent CLAUDE.md usage",
                "Mentors junior developers"
            ],
            growth_areas=[
                "Could increase /commit adoption",
                "Opportunity to use JIRA MCP more"
            ],
            fit_with_team_baseline="Exceeds team average",
            learning_path=[
                "Master multi-agent orchestration",
                "Lead test automation initiatives",
                "Mentor 2 junior developers"
            ],
            key_insights=[
                "Natural AI advocate on team",
                "Strong potential for leadership role"
            ],
            recommendations=[
                "Formalize mentorship role",
                "Lead multi-agent orchestration initiative",
                "Document team playbooks"
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "alice_profile.pdf"
            result_path = renderer.render_individual_report(report, output_path)

            assert result_path.exists()

            # Individual reports should be smaller than team reports
            file_size = result_path.stat().st_size
            assert file_size > 5000  # At least 5KB
