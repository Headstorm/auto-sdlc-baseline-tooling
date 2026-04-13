"""
PDF Rendering Module

Converts TeamReport and IndividualReport objects into professional PDF documents
using ReportLab. Generates 8-12 page team reports and 4-6 page individual profiles
with professional styling, maturity level visualizations, and executive summaries.
"""

from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    Image,
    KeepTogether,
)
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from src.auto_sdlc.reports.models import TeamReport, IndividualReport, DimensionReport


# ============================================================================
# STYLING CONSTANTS
# ============================================================================

class PDFStyles:
    """Professional styling constants for PDF generation."""

    # Color Palette
    NAVY_BLUE = colors.HexColor("#1a3a5c")
    LIGHT_GRAY = colors.HexColor("#f5f5f5")
    DARK_GRAY = colors.HexColor("#333333")
    ACCENT_BLUE = colors.HexColor("#0066cc")
    SUCCESS_GREEN = colors.HexColor("#27ae60")
    WARNING_ORANGE = colors.HexColor("#e67e22")
    DANGER_RED = colors.HexColor("#e74c3c")

    # Maturity Level Colors
    L1_RED = colors.HexColor("#e74c3c")  # Early/Assisted
    L2_YELLOW = colors.HexColor("#f39c12")  # Integrated
    L3_LIGHT_GREEN = colors.HexColor("#2ecc71")  # Agentic
    L4_DARK_GREEN = colors.HexColor("#27ae60")  # Autonomous

    # Font sizes
    TITLE_SIZE = 28
    HEADING1_SIZE = 20
    HEADING2_SIZE = 16
    HEADING3_SIZE = 13
    BODY_SIZE = 10
    SMALL_SIZE = 9

    # Spacing
    SECTION_SPACING = 0.3 * inch
    SUBSECTION_SPACING = 0.2 * inch
    PARAGRAPH_SPACING = 0.1 * inch

    @staticmethod
    def get_maturity_color(level: int) -> colors.Color:
        """Get color for maturity level."""
        if level == 1:
            return PDFStyles.L1_RED
        elif level == 2:
            return PDFStyles.L2_YELLOW
        elif level == 3:
            return PDFStyles.L3_LIGHT_GREEN
        elif level == 4:
            return PDFStyles.L4_DARK_GREEN
        return PDFStyles.LIGHT_GRAY

    @staticmethod
    def get_maturity_label(level: int) -> str:
        """Get label for maturity level."""
        labels = {1: "L1 (Assisted)", 2: "L2 (Integrated)",
                  3: "L3 (Agentic)", 4: "L4 (Autonomous)"}
        return labels.get(level, "Unknown")


# ============================================================================
# STYLE DEFINITIONS
# ============================================================================

def get_custom_styles() -> Dict:
    """Create and return custom paragraph styles."""
    styles = getSampleStyleSheet()

    # Title style
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=PDFStyles.TITLE_SIZE,
        textColor=PDFStyles.NAVY_BLUE,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    ))

    # Heading 1 style
    styles.add(ParagraphStyle(
        name='CustomHeading1',
        parent=styles['Heading1'],
        fontSize=PDFStyles.HEADING1_SIZE,
        textColor=PDFStyles.NAVY_BLUE,
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold',
    ))

    # Heading 2 style
    styles.add(ParagraphStyle(
        name='CustomHeading2',
        parent=styles['Heading2'],
        fontSize=PDFStyles.HEADING2_SIZE,
        textColor=PDFStyles.NAVY_BLUE,
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold',
    ))

    # Heading 3 style
    styles.add(ParagraphStyle(
        name='CustomHeading3',
        parent=styles['Heading3'],
        fontSize=PDFStyles.HEADING3_SIZE,
        textColor=PDFStyles.DARK_GRAY,
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold',
    ))

    # Body text style
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['BodyText'],
        fontSize=PDFStyles.BODY_SIZE,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leading=14,
    ))

    # Small text style
    styles.add(ParagraphStyle(
        name='CustomSmall',
        parent=styles['Normal'],
        fontSize=PDFStyles.SMALL_SIZE,
        textColor=PDFStyles.DARK_GRAY,
        spaceAfter=6,
    ))

    return styles


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _format_confidence(confidence: str) -> str:
    """Format confidence level for display."""
    level_map = {"high": "High", "medium": "Medium", "low": "Low"}
    return level_map.get(confidence, confidence)


def _get_safe_value(value, default="Not assessed") -> str:
    """Safely convert value to string, handling None and empty cases."""
    if value is None:
        return default
    if isinstance(value, str) and not value.strip():
        return default
    if isinstance(value, (list, dict)) and not value:
        return "—"
    return str(value)


def _create_maturity_bar(level: int, width: float = 2.0) -> Table:
    """Create a visual maturity level bar."""
    bar_height = 0.4 * inch
    cell_width = width / 4

    # Create color boxes for each level
    data = []
    for i in range(1, 5):
        is_current = i <= level
        bg_color = PDFStyles.get_maturity_color(i) if is_current else colors.lightgrey

        # Create a small box showing the level
        cell = Paragraph(
            f"<font color='{bg_color}'><b>L{i}</b></font>",
            get_custom_styles()['CustomSmall']
        )
        data.append(cell)

    # Create table
    bar_table = Table(
        [data],
        colWidths=[cell_width * inch] * 4,
        rowHeights=[0.35 * inch],
    )

    # Style the table
    bar_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), PDFStyles.get_maturity_color(1)),
        ('BACKGROUND', (1, 0), (1, 0),
         PDFStyles.get_maturity_color(2) if level >= 2 else colors.lightgrey),
        ('BACKGROUND', (2, 0), (2, 0),
         PDFStyles.get_maturity_color(3) if level >= 3 else colors.lightgrey),
        ('BACKGROUND', (3, 0), (3, 0),
         PDFStyles.get_maturity_color(4) if level >= 4 else colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('BORDER', (0, 0), (-1, -1), 1, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))

    return bar_table


# ============================================================================
# PDF RENDERER CLASS
# ============================================================================

class PDFRenderer:
    """
    Renders AI Maturity Assessment Reports to PDF documents.

    Supports both TeamReport (8-12 pages) and IndividualReport (4-6 pages)
    with professional styling and visual hierarchy.
    """

    def __init__(self):
        """Initialize the PDF renderer."""
        self.styles = get_custom_styles()
        self.page_width, self.page_height = letter

    def render_team_report(
        self,
        report: TeamReport,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Render a TeamReport to PDF.

        Args:
            report: TeamReport object with all required data
            output_path: Where to save the PDF. If None, uses default location.

        Returns:
            Path to the generated PDF file

        Raises:
            ValueError: If report data is invalid or missing
            IOError: If file cannot be written
        """
        # Determine output path
        if output_path is None:
            output_path = self._get_default_output_path("team_report.pdf")
        else:
            output_path = Path(output_path)

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Build document content
        elements = []

        # Cover page
        elements.extend(self._build_team_cover_page(report))
        elements.append(PageBreak())

        # Executive summary
        elements.extend(self._build_team_executive_summary(report))
        elements.append(PageBreak())

        # Methodology
        elements.extend(self._build_methodology_section())
        elements.append(PageBreak())

        # Assessment data sources
        elements.extend(self._build_data_sources_section(report))
        elements.append(PageBreak())

        # Dimension deep-dives
        for dimension_name in sorted(report.dimensions.keys()):
            dimension = report.dimensions[dimension_name]
            elements.extend(self._build_dimension_section(dimension))
            elements.append(PageBreak())

        # Strategic recommendations
        elements.extend(self._build_strategic_recommendations(report))
        elements.append(PageBreak())

        # Appendix
        elements.extend(self._build_appendix(report))

        # Build PDF
        doc.build(elements)

        return output_path

    def render_individual_report(
        self,
        report: IndividualReport,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Render an IndividualReport to PDF.

        Args:
            report: IndividualReport object with all required data
            output_path: Where to save the PDF. If None, uses default location.

        Returns:
            Path to the generated PDF file

        Raises:
            ValueError: If report data is invalid or missing
            IOError: If file cannot be written
        """
        # Determine output path
        if output_path is None:
            output_path = self._get_default_output_path(
                f"individual_report_{report.developer_id}.pdf"
            )
        else:
            output_path = Path(output_path)

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Build document content
        elements = []

        # Cover page
        elements.extend(self._build_individual_cover_page(report))
        elements.append(PageBreak())

        # Executive summary
        elements.extend(self._build_individual_executive_summary(report))
        elements.append(PageBreak())

        # Usage patterns
        elements.extend(self._build_usage_patterns_section(report))
        elements.append(PageBreak())

        # Dimension highlights
        elements.extend(self._build_dimension_highlights(report))
        elements.append(PageBreak())

        # Learning path
        elements.extend(self._build_learning_path_section(report))
        elements.append(PageBreak())

        # Appendix
        elements.extend(self._build_individual_appendix(report))

        # Build PDF
        doc.build(elements)

        return output_path

    # ========================================================================
    # TEAM REPORT SECTIONS
    # ========================================================================

    def _build_team_cover_page(self, report: TeamReport) -> List:
        """Build cover page for team report."""
        elements = []

        # Title
        elements.append(Spacer(1, 1.0 * inch))
        elements.append(Paragraph(
            "AI Maturity Assessment Report",
            self.styles['CustomTitle']
        ))

        # Team name
        elements.append(Paragraph(
            f"{report.team_name}",
            self.styles['CustomHeading1']
        ))
        elements.append(Spacer(1, 0.3 * inch))

        # Key information
        date_str = datetime.strptime(report.report_date, "%Y-%m-%d").strftime("%B %d, %Y")
        info_text = f"""
        <b>Assessment Date:</b> {date_str}<br/>
        <b>Team Size:</b> {report.team_size} developers<br/>
        <b>Assessment Period:</b> {report.assessment_period_weeks} weeks<br/>
        <b>Overall Maturity Level:</b> {_format_confidence(str(report.overall_maturity_level))}
        """
        elements.append(Paragraph(info_text, self.styles['CustomBody']))
        elements.append(Spacer(1, 0.3 * inch))

        # Maturity bar
        elements.append(Paragraph("Maturity Level:", self.styles['CustomHeading3']))
        elements.append(_create_maturity_bar(int(report.overall_maturity_level)))
        elements.append(Spacer(1, 0.3 * inch))

        # Key stat
        key_stat = f"This team is at {PDFStyles.get_maturity_label(int(report.overall_maturity_level))}"
        elements.append(Paragraph(
            f"<i>{key_stat}</i>",
            self.styles['CustomBody']
        ))

        return elements

    def _build_team_executive_summary(self, report: TeamReport) -> List:
        """Build executive summary section."""
        elements = []

        elements.append(Paragraph(
            "Executive Summary",
            self.styles['CustomHeading1']
        ))
        elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        # Main summary
        elements.append(Paragraph(
            _get_safe_value(report.executive_summary),
            self.styles['CustomBody']
        ))
        elements.append(Spacer(1, PDFStyles.SECTION_SPACING))

        # Key insights
        elements.append(Paragraph(
            "Key Findings",
            self.styles['CustomHeading2']
        ))

        for insight in report.key_insights[:5]:
            bullet_text = f"• {_get_safe_value(insight)}"
            elements.append(Paragraph(bullet_text, self.styles['CustomBody']))

        elements.append(Spacer(1, PDFStyles.SECTION_SPACING))

        # Next steps
        elements.append(Paragraph(
            "Next Steps",
            self.styles['CustomHeading2']
        ))

        for i, step in enumerate(report.next_steps[:3], 1):
            step_text = f"{i}. {_get_safe_value(step)}"
            elements.append(Paragraph(step_text, self.styles['CustomBody']))

        return elements

    def _build_methodology_section(self) -> List:
        """Build methodology section."""
        elements = []

        elements.append(Paragraph(
            "Methodology",
            self.styles['CustomHeading1']
        ))
        elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        methodology_text = """
        This assessment evaluates AI maturity across <b>12 dimensions</b> organized into
        <b>4 major areas</b>: Capability, Integration, Governance, and Execution Ownership.
        <br/><br/>

        <b>The 12 Dimensions:</b><br/>
        <b>Capability:</b> AI Tool Adoption, Prompt & Context Engineering, Agent Configuration<br/>
        <b>Integration:</b> CI/CD Integration, Ticketing & Planning, Cross-System Connectivity<br/>
        <b>Governance:</b> Quality Controls, Security & Compliance, Measurement & KPIs<br/>
        <b>Execution Ownership:</b> Ways of Working, Accountability & Ownership,
        Scalability & Knowledge Transfer<br/>
        <br/>

        <b>Maturity Levels:</b><br/>
        <b>L1 (Assisted):</b> Ad-hoc usage, unguided practices<br/>
        <b>L2 (Integrated):</b> Documented processes, enforced standards<br/>
        <b>L3 (Agentic):</b> Automated decision-making, multi-step workflows<br/>
        <b>L4 (Autonomous):</b> Self-improving systems, fully delegated<br/>
        """

        elements.append(Paragraph(methodology_text, self.styles['CustomBody']))

        return elements

    def _build_data_sources_section(self, report: TeamReport) -> List:
        """Build assessment data sources section."""
        elements = []

        elements.append(Paragraph(
            "Assessment Data Sources",
            self.styles['CustomHeading1']
        ))
        elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        # Create table of data sources
        data = [
            ["Source", "Available", "Confidence"],
        ]

        for source_name, is_available in report.data_sources.items():
            status = "✓" if is_available else "✗"
            data.append([
                source_name,
                status,
                _format_confidence(report.confidence_by_dimension.get(source_name, "medium"))
            ])

        # Create table
        source_table = Table(data, colWidths=[2.5*inch, 1.0*inch, 1.5*inch])
        source_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PDFStyles.NAVY_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), PDFStyles.LIGHT_GRAY),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFStyles.LIGHT_GRAY]),
        ]))

        elements.append(source_table)

        return elements

    def _build_dimension_section(self, dimension: DimensionReport) -> List:
        """Build a dimension deep-dive section."""
        elements = []

        # Dimension header
        elements.append(Paragraph(
            dimension.dimension,
            self.styles['CustomHeading1']
        ))
        elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        # Current level
        elements.append(Paragraph(
            f"<b>Current Maturity Level:</b> {PDFStyles.get_maturity_label(dimension.maturity_level)} "
            f"(Confidence: {_format_confidence(dimension.confidence)})",
            self.styles['CustomBody']
        ))
        elements.append(Spacer(1, 0.1 * inch))

        # Maturity bar
        elements.append(_create_maturity_bar(dimension.maturity_level, width=1.5))
        elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        # Current state
        elements.append(Paragraph(
            "<b>Current State:</b>",
            self.styles['CustomHeading2']
        ))
        elements.append(Paragraph(
            _get_safe_value(dimension.current_state),
            self.styles['CustomBody']
        ))
        elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        # Evidence summary
        if dimension.evidence_summary:
            elements.append(Paragraph(
                "<b>Evidence Summary:</b>",
                self.styles['CustomHeading2']
            ))
            for source, summary in dimension.evidence_summary.items():
                bullet = f"• <b>{source}:</b> {summary}"
                elements.append(Paragraph(bullet, self.styles['CustomBody']))
            elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        # Strengths
        if dimension.strengths:
            elements.append(Paragraph(
                "<b>Strengths:</b>",
                self.styles['CustomHeading3']
            ))
            for strength in dimension.strengths:
                bullet = f"✓ {strength}"
                elements.append(Paragraph(bullet, self.styles['CustomBody']))
            elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        # Gaps
        if dimension.gaps:
            elements.append(Paragraph(
                "<b>Gaps:</b>",
                self.styles['CustomHeading3']
            ))
            for gap in dimension.gaps:
                bullet = f"✗ {gap}"
                elements.append(Paragraph(bullet, self.styles['CustomBody']))
            elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        # Roadmap
        if dimension.roadmap:
            elements.append(Paragraph(
                f"<b>Roadmap to Level {dimension.maturity_level + 1}:</b>",
                self.styles['CustomHeading3']
            ))

            roadmap_data = [["Step", "Action", "Effort", "Owner"]]
            for i, action in enumerate(dimension.roadmap[:5], 1):
                step_text = f"{i}"
                action_text = action.get("title", "")
                effort_text = f"{action.get('effort_weeks', 0)}w"
                owner_text = ", ".join(action.get("owners", []))

                roadmap_data.append([
                    step_text,
                    action_text,
                    effort_text,
                    owner_text
                ])

            roadmap_table = Table(
                roadmap_data,
                colWidths=[0.5*inch, 2.5*inch, 0.75*inch, 1.25*inch]
            )
            roadmap_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), PDFStyles.NAVY_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), PDFStyles.LIGHT_GRAY),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFStyles.LIGHT_GRAY]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))

            elements.append(roadmap_table)

        return elements

    def _build_strategic_recommendations(self, report: TeamReport) -> List:
        """Build strategic recommendations section."""
        elements = []

        elements.append(Paragraph(
            "Strategic Recommendations",
            self.styles['CustomHeading1']
        ))
        elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        elements.append(Paragraph(
            "Based on the assessment, the following actions will most effectively advance maturity:",
            self.styles['CustomBody']
        ))
        elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        for i, rec in enumerate(report.recommendations[:10], 1):
            rec_text = f"<b>{i}. </b>{_get_safe_value(rec)}"
            elements.append(Paragraph(rec_text, self.styles['CustomBody']))
            elements.append(Spacer(1, PDFStyles.PARAGRAPH_SPACING))

        return elements

    def _build_appendix(self, report: TeamReport) -> List:
        """Build appendix section."""
        elements = []

        elements.append(Paragraph(
            "Appendix: Assessment Details",
            self.styles['CustomHeading1']
        ))
        elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        # Dimension scores table
        elements.append(Paragraph(
            "Dimension Scores and Confidence",
            self.styles['CustomHeading2']
        ))

        scores_data = [["Dimension", "Level", "Confidence"]]
        for dim_name in sorted(report.dimensions.keys()):
            dim = report.dimensions[dim_name]
            scores_data.append([
                dim_name,
                PDFStyles.get_maturity_label(dim.maturity_level),
                _format_confidence(dim.confidence)
            ])

        scores_table = Table(
            scores_data,
            colWidths=[3.0*inch, 1.5*inch, 1.5*inch]
        )
        scores_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PDFStyles.NAVY_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), PDFStyles.LIGHT_GRAY),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFStyles.LIGHT_GRAY]),
        ]))

        elements.append(scores_table)

        return elements

    # ========================================================================
    # INDIVIDUAL REPORT SECTIONS
    # ========================================================================

    def _build_individual_cover_page(self, report: IndividualReport) -> List:
        """Build cover page for individual report."""
        elements = []

        # Title
        elements.append(Spacer(1, 1.0 * inch))
        elements.append(Paragraph(
            "Developer AI Maturity Profile",
            self.styles['CustomTitle']
        ))

        # Developer ID
        elements.append(Paragraph(
            f"{report.developer_id}",
            self.styles['CustomHeading1']
        ))
        elements.append(Spacer(1, 0.3 * inch))

        # Key information
        date_str = datetime.strptime(report.report_date, "%Y-%m-%d").strftime("%B %d, %Y")
        info_text = f"""
        <b>Assessment Date:</b> {date_str}<br/>
        <b>Assessment Period:</b> {report.assessment_period_weeks} weeks<br/>
        <b>Individual Maturity Level:</b> {PDFStyles.get_maturity_label(int(report.overall_maturity_level))}<br/>
        <b>Fit with Team:</b> {_get_safe_value(report.fit_with_team_baseline)}
        """
        elements.append(Paragraph(info_text, self.styles['CustomBody']))
        elements.append(Spacer(1, 0.3 * inch))

        # Maturity bar
        elements.append(Paragraph("Maturity Level:", self.styles['CustomHeading3']))
        elements.append(_create_maturity_bar(int(report.overall_maturity_level)))

        return elements

    def _build_individual_executive_summary(self, report: IndividualReport) -> List:
        """Build executive summary for individual report."""
        elements = []

        elements.append(Paragraph(
            "Executive Summary",
            self.styles['CustomHeading1']
        ))
        elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        # Main summary
        elements.append(Paragraph(
            _get_safe_value(report.executive_summary),
            self.styles['CustomBody']
        ))
        elements.append(Spacer(1, PDFStyles.SECTION_SPACING))

        # Key insights
        if report.key_insights:
            elements.append(Paragraph(
                "Key Insights",
                self.styles['CustomHeading2']
            ))

            for insight in report.key_insights[:5]:
                bullet_text = f"• {_get_safe_value(insight)}"
                elements.append(Paragraph(bullet_text, self.styles['CustomBody']))

        return elements

    def _build_usage_patterns_section(self, report: IndividualReport) -> List:
        """Build usage patterns section."""
        elements = []

        elements.append(Paragraph(
            "Usage Patterns",
            self.styles['CustomHeading1']
        ))
        elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        # Create table of usage metrics
        if report.usage_patterns:
            usage_data = [["Metric", "Value"]]

            for metric_name, metric_value in list(report.usage_patterns.items())[:10]:
                metric_display = metric_name.replace("_", " ").title()
                usage_data.append([
                    metric_display,
                    f"{metric_value:.1f}" if isinstance(metric_value, (int, float)) else str(metric_value)
                ])

            usage_table = Table(usage_data, colWidths=[3.0*inch, 2.0*inch])
            usage_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), PDFStyles.NAVY_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), PDFStyles.LIGHT_GRAY),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFStyles.LIGHT_GRAY]),
            ]))

            elements.append(usage_table)
        else:
            elements.append(Paragraph(
                "No usage data available.",
                self.styles['CustomBody']
            ))

        return elements

    def _build_dimension_highlights(self, report: IndividualReport) -> List:
        """Build dimension highlights section."""
        elements = []

        elements.append(Paragraph(
            "Dimension Highlights",
            self.styles['CustomHeading1']
        ))
        elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        # Show strengths and gaps by dimension
        for dim_name in sorted(report.dimensions.keys())[:6]:
            dim = report.dimensions[dim_name]

            elements.append(Paragraph(
                dim_name,
                self.styles['CustomHeading2']
            ))
            elements.append(Paragraph(
                f"Level: {PDFStyles.get_maturity_label(dim.maturity_level)}",
                self.styles['CustomSmall']
            ))

            if dim.strengths:
                for strength in dim.strengths:
                    bullet = f"✓ {strength}"
                    elements.append(Paragraph(bullet, self.styles['CustomBody']))

            if dim.gaps:
                for gap in dim.gaps:
                    bullet = f"⚠ {gap}"
                    elements.append(Paragraph(bullet, self.styles['CustomBody']))

            elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        return elements

    def _build_learning_path_section(self, report: IndividualReport) -> List:
        """Build personalized learning path section."""
        elements = []

        elements.append(Paragraph(
            "Learning Path",
            self.styles['CustomHeading1']
        ))
        elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        elements.append(Paragraph(
            "Skills and areas to develop for the next level:",
            self.styles['CustomBody']
        ))
        elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        # Learning goals
        if report.learning_path:
            for i, goal in enumerate(report.learning_path[:8], 1):
                goal_text = f"{i}. {_get_safe_value(goal)}"
                elements.append(Paragraph(goal_text, self.styles['CustomBody']))
        else:
            elements.append(Paragraph(
                "No specific learning goals identified.",
                self.styles['CustomBody']
            ))

        elements.append(Spacer(1, PDFStyles.SECTION_SPACING))

        # Recommendations
        if report.recommendations:
            elements.append(Paragraph(
                "Recommended Actions",
                self.styles['CustomHeading2']
            ))

            for rec in report.recommendations[:5]:
                bullet = f"• {_get_safe_value(rec)}"
                elements.append(Paragraph(bullet, self.styles['CustomBody']))

        return elements

    def _build_individual_appendix(self, report: IndividualReport) -> List:
        """Build appendix for individual report."""
        elements = []

        elements.append(Paragraph(
            "Appendix: Detailed Metrics",
            self.styles['CustomHeading1']
        ))
        elements.append(Spacer(1, PDFStyles.SUBSECTION_SPACING))

        # Dimension scores
        elements.append(Paragraph(
            "Dimension Scores",
            self.styles['CustomHeading2']
        ))

        scores_data = [["Dimension", "Level", "Confidence"]]
        for dim_name in sorted(report.dimensions.keys()):
            dim = report.dimensions[dim_name]
            scores_data.append([
                dim_name,
                PDFStyles.get_maturity_label(dim.maturity_level),
                _format_confidence(dim.confidence)
            ])

        scores_table = Table(
            scores_data,
            colWidths=[3.0*inch, 1.5*inch, 1.5*inch]
        )
        scores_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PDFStyles.NAVY_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), PDFStyles.LIGHT_GRAY),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFStyles.LIGHT_GRAY]),
        ]))

        elements.append(scores_table)

        return elements

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def _get_default_output_path(self, filename: str) -> Path:
        """Get default output path for reports."""
        reports_dir = Path.home() / ".auto-sdlc" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir / filename
