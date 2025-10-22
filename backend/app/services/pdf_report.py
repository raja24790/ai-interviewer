from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..deps import SettingsType, get_settings
from ..utils.logging import get_logger

logger = get_logger("pdf")


def create_pdf(
    session_id: str,
    questions: Iterable[Mapping[str, str]],
    scores: Iterable[Mapping[str, int | str]],
    attention_summary: Mapping[str, float] | None,
    summary_text: str,
    settings: SettingsType | None = None,
) -> Path:
    settings = settings or get_settings()
    report_dir = settings.report_dir / session_id
    report_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = report_dir / "final_report.pdf"

    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=48, bottomMargin=36)
    elements: list = []

    title_style = ParagraphStyle("Title", fontSize=20, leading=24, spaceAfter=12)
    normal_style = ParagraphStyle("Normal", fontSize=11, leading=14)
    small_style = ParagraphStyle("Small", fontSize=10, leading=12)

    header = f"<b>{settings.company_name}</b> — AI Interview Summary"
    elements.append(Paragraph(header, title_style))
    elements.append(Paragraph(f"Session ID: {session_id}", small_style))
    elements.append(Paragraph(f"Generated: {datetime.utcnow().isoformat()}Z", small_style))
    elements.append(Spacer(1, 0.25 * inch))

    data = [["Question", "Response", "Clarity", "Relevance", "Structure", "Conciseness", "Confidence", "Total"]]
    for q, score in zip(questions, scores):
        data.append(
            [
                Paragraph(q["question"], small_style),
                Paragraph(q["transcript"], small_style),
                str(score.get("clarity", "")),
                str(score.get("relevance", "")),
                str(score.get("structure", "")),
                str(score.get("conciseness", "")),
                str(score.get("confidence", "")),
                str(score.get("total", "")),
            ]
        )

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (2, 1), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 0.3 * inch))

    if attention_summary:
        attention_details = "<br/>".join(
            f"<b>{k.replace('_', ' ').title()}</b>: {v:.1%}" for k, v in attention_summary.items()
        )
        elements.append(Paragraph("<b>Attention Analysis</b>", normal_style))
        elements.append(Paragraph(attention_details, small_style))
        elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph("<b>Summary</b>", normal_style))
    elements.append(Paragraph(summary_text, small_style))

    doc.build(elements)
    logger.info("PDF report generated at %s", pdf_path)
    return pdf_path
