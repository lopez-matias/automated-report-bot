import io
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable, PageBreak,
)
from reportlab.platypus.frames import Frame
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)

NAVY = colors.HexColor("#1F3864")
LIGHT_GRAY = colors.HexColor("#F2F2F2")
MID_GRAY = colors.HexColor("#BFBFBF")
WHITE = colors.white
GREEN = colors.HexColor("#70AD47")
RED = colors.HexColor("#FF0000")


def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = doc.pagesize

    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 1.5 * cm, w, 1.5 * cm, fill=True, stroke=False)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(1 * cm, h - 1 * cm, doc.report_title)
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(w - 1 * cm, h - 1 * cm, doc.date_range)

    canvas.setFillColor(MID_GRAY)
    canvas.rect(0, 0, w, 0.8 * cm, fill=True, stroke=False)
    canvas.setFillColor(colors.black)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(1 * cm, 0.25 * cm, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    canvas.drawRightString(w - 1 * cm, 0.25 * cm, f"Page {doc.page}")
    canvas.restoreState()


def _kpi_table(df: pd.DataFrame, styles) -> list:
    numeric_cols = df.select_dtypes(include="number").columns.tolist()[:4]
    if not numeric_cols:
        return []

    kpi_data = []
    for col in numeric_cols:
        total = df[col].sum()
        kpi_data.append((col.replace("_", " ").title(), f"{total:,.2f}"))

    table_data = [["Metric", "Value"]] + kpi_data

    t = Table(table_data, colWidths=[8 * cm, 6 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [t]


def _data_table(df: pd.DataFrame) -> Table:
    max_cols = 10
    display_df = df.iloc[:, :max_cols]

    headers = [str(c).replace("_", " ").title() for c in display_df.columns]
    rows = [headers]
    for _, row in display_df.iterrows():
        rows.append([str(v) if v is not None else "" for v in row])

    n_cols = len(headers)
    page_w = landscape(A4)[0] - 4 * cm
    col_w = page_w / n_cols

    t = Table(rows, colWidths=[col_w] * n_cols, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, MID_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GRAY))

    t.setStyle(TableStyle(style_cmds))
    return t


def build_pdf(
    df: pd.DataFrame,
    report_name: str = "Report",
    date_range: str = "",
    output_path: str = None,
) -> bytes:
    buf = io.BytesIO()
    page_size = landscape(A4) if len(df.columns) > 5 else A4

    doc = SimpleDocTemplate(
        buf,
        pagesize=page_size,
        topMargin=2 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )
    doc.report_title = report_name
    doc.date_range = date_range

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=18,
        textColor=NAVY,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=NAVY,
        spaceBefore=12,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )

    story = [
        Spacer(1, 0.5 * cm),
        Paragraph(report_name, title_style),
        Paragraph(date_range or datetime.now().strftime("%B %d, %Y"), styles["Normal"]),
        HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=12),
        Paragraph("Executive Summary", section_style),
    ]

    story.extend(_kpi_table(df, styles))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Detailed Data", section_style))
    story.append(Spacer(1, 0.2 * cm))
    story.append(_data_table(df))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)

    pdf_bytes = buf.getvalue()

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        logger.info(f"PDF saved to {output_path}")

    return pdf_bytes
