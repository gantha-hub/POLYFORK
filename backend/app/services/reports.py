"""PDF report generation service using ReportLab.

Generates audit-ready forest reports including:
- Stand summary metrics (Tree count +/- interval, Carbon stock +/- interval)
- Methodology disclosure & biophysical limitations
- Prominent diagonal 'SYNTHETIC DATA DEMO' watermark when mock model is used.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.schemas.tree import SurveyResultsSummary
from app.config import settings
from app.core.logging import logger


class WatermarkCanvas(canvas.Canvas):
    """Custom ReportLab canvas that draws a diagonal watermark if data is synthetic."""

    def __init__(self, *args, **kwargs):
        self.is_synthetic = kwargs.pop("is_synthetic", False)
        super().__init__(*args, **kwargs)

    def draw_watermark(self):
        """Draws semi-transparent diagonal watermark across the page."""
        if not self.is_synthetic:
            return

        self.saveState()
        self.setFont("Helvetica-Bold", 42)
        self.setFillColor(colors.HexColor("#ef4444"), alpha=0.18)
        self.translate(300, 400)
        self.rotate(45)
        self.drawCentredString(0, 0, "SYNTHETIC DATA DEMO")
        self.setFont("Helvetica", 14)
        self.drawCentredString(0, -35, "NOT FOR REGULATORY CARBON COMPLIANCE")
        self.restoreState()

    def showPage(self):
        self.draw_watermark()
        super().showPage()

    def save(self):
        self.draw_watermark()
        super().save()


def generate_survey_pdf_report(
    summary: SurveyResultsSummary,
    output_path: Path | str,
    project_name: str = "Forest Inventory Project",
) -> Path:
    """Generates an executive PDF report for a survey.

    Args:
        summary: SurveyResultsSummary object with counts, intervals, and carbon.
        output_path: Path where the PDF should be saved.
        project_name: Project display title.

    Returns:
        Path to the generated PDF.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    is_synth = summary.data_source == "synthetic"

    # Define canvas maker closure to pass is_synthetic flag
    def canvas_maker(*args, **kwargs):
        kwargs["is_synthetic"] = is_synth
        return WatermarkCanvas(*args, **kwargs)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#064e3b"),  # Deep forest green
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=15,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#065f46"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
    )
    callout_style = ParagraphStyle(
        "Callout",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#64748b"),
    )

    story = []

    # Title & Header
    story.append(Paragraph("VrikshaVision: Tree Digital Twin", title_style))
    date_str = datetime.now().strftime("%B %d, %Y - %H:%M UTC")
    story.append(
        Paragraph(
            f"<b>Project:</b> {project_name} | <b>Survey ID:</b> {summary.survey_id[:8]}... | <b>Generated:</b> {date_str}",
            subtitle_style,
        )
    )

    # 1. Executive Summary Table
    story.append(Paragraph("1. Stand Summary & Calibrated Enumeration", section_heading))

    count_info = summary.count
    cal_label = "Calibrated (Split-Conformal GLM)" if count_info.calibrated else "Uncalibrated Raw (Heuristic Normal)"
    cal_color = colors.HexColor("#059669") if count_info.calibrated else colors.HexColor("#b45309")

    carbon_info = summary.carbon

    summary_data = [
        ["Metric", "Value", "Statistical Details"],
        ["Detected Tree Count", str(count_info.raw_count), "Direct computer vision instance detections"],
        [
            "Calibrated Tree Estimate",
            f"<b>{count_info.calibrated_count}</b>",
            f"<b>[{count_info.interval.low} - {count_info.interval.high}]</b> (90% prediction interval)",
        ],
        ["Calibration Status", Paragraph(f"<font color='{cal_color}'><b>{cal_label}</b></font>", body_style), "Ground-truth audit compliance"],
        ["Total Carbon Stock", f"<b>{carbon_info.mean_carbon_tonnes} tonnes C</b>", f"[{carbon_info.interval_tonnes.low} - {carbon_info.interval_tonnes.high}] tonnes (1,000 draws)"],
        ["Mean Crown Area", f"{summary.mean_crown_area_sqm} m²", "Average ground crown projection"],
        ["Mean Est. DBH", f"{summary.mean_dbh_cm} cm", "Allometric scaling from crown projection area"],
        ["Data Provenance", "SYNTHETIC" if is_synth else "REAL WEIGHTS", "ML inference model backend"],
    ]

    t_summary = Table(summary_data, colWidths=[1.8 * inch, 2.0 * inch, 3.2 * inch])
    t_summary.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0fdf4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#065f46")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ])
    )
    story.append(t_summary)
    story.append(Spacer(1, 10))

    # 2. Allometric Biomass & Methodology
    story.append(Paragraph("2. Methodology & Scientific Parameterization", section_heading))
    method_text = (
        "<b>Canopy Crown Segmentation:</b> High-resolution aerial imagery is tiled into windowed 512×512 slices "
        "with 20% spatial overlap. Overlapping crowns are partitioned via distance-transform marker-controlled watershed, "
        "and duplicate cross-tile seams are pruned using Polygon Non-Maximum Suppression (IoU threshold = 0.35).<br/><br/>"
        "<b>Split-Conformal Calibration:</b> When ≥10 field audit plots are uploaded, a Negative Binomial Generalized "
        "Linear Model with log(detected count) offset is fitted against true ground observations. Residual non-conformity "
        "scores on a held-out calibration split define the 90% finite-sample conformal prediction interval.<br/><br/>"
        "<b>Monte Carlo Carbon Propagation:</b> Individual tree Crown Projection Area (CPA) is mapped to Diameter at "
        "Breast Height (DBH) and Above-Ground Biomass (AGB) using biome-specific pantropical allometric equations "
        f"(Forest type: <i>{summary.forest_type}</i>; Carbon fraction: <i>{carbon_info.carbon_fraction}</i>). "
        "Stand total carbon is evaluated across 1,000 Monte Carlo draws to propagate allometric residual errors."
    )
    story.append(Paragraph(method_text, body_style))
    story.append(Spacer(1, 10))

    # 3. Limitations & Disclaimers
    story.append(Paragraph("3. Biophysical Limitations & Regulatory Disclaimers", section_heading))
    disclaimer_text = (
        "• Optical aerial surveys cannot distinguish suppressed sub-canopy vegetation obscured by dense dominant crowns.<br/>"
        "• Allometric equations rely on regional literature constants and require local destructive harvest or terrestrial "
        "LiDAR validation for verified carbon credit issuance.<br/>"
        f"• <b>Notice on Synthetic Detections:</b> {'This report was generated using procedural synthetic mock detections for platform verification and MUST NOT be used for regulatory compliance.' if is_synth else 'Report generated using real trained deep-learning weights.'}"
    )
    story.append(Paragraph(disclaimer_text, callout_style))

    doc.build(story, canvasmaker=canvas_maker)
    logger.info(f"PDF report generated at {output_path} (is_synthetic={is_synth})")
    return output_path
