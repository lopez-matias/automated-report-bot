import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Image,
    NextPageTemplate,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)

NAVY = colors.HexColor("#1F3864")
LIGHT_GRAY = colors.HexColor("#F2F2F2")
WHITE = colors.white
BLACK = colors.black
GREEN = colors.HexColor("#70AD47")
RED = colors.HexColor("#FF0000")


class PdfBuilder:
    def __init__(self, config: dict):
        self.config = config
        self._styles = getSampleStyleSheet()

    def build(self, df: pd.DataFrame, output_path: str) -> str:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        use_landscape = len(df.columns) > 6
        pagesize = landscape(A4) if use_landscape else A4

        doc = SimpleDocTemplate(
            output_path,
            pagesize=pagesize,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        story = []
        story += self._header_section(df)
        story += self._kpi_section(df)
        story.append(Spacer(1, 0.5 * cm))
        story += self._data_table_section(df)

        doc.build(
            story,
            onFirstPage=self._page_footer,
            onLaterPages=self._page_footer,
        )

        logger.info("PDF report saved to %s", output_path)
        return output_path

    # ── Header ───────────────────────────────────────────────────────────────

    def _header_section(self, df: pd.DataFrame) -> list:
        title_style = ParagraphStyle(
            "title",
            parent=self._styles["Title"],
            textColor=NAVY,
            fontSize=22,
            spaceAfter=4,
        )
        sub_style = ParagraphStyle(
            "sub",
            parent=self._styles["Normal"],
            textColor=colors.gray,
            fontSize=10,
            spaceAfter=12,
        )

        report_name = self.config.get("name", "Report")
        date_range = self.config.get("date_range", datetime.now().strftime("%Y-%m-%d"))

        return [
            Paragraph(report_name, title_style),
            Paragraph(f"Period: {date_range} &nbsp;|&nbsp; Generated: {datetime.now():%Y-%m-%d %H:%M}", sub_style),
            self._divider(),
            Spacer(1, 0.4 * cm),
        ]

    def _divider(self):
        return Table(
            [[""]],
            colWidths=["100%"],
            style=TableStyle([("LINEBELOW", (0, 0), (-1, 0), 1, NAVY)]),
        )

    # ── KPI boxes ────────────────────────────────────────────────────────────

    def _kpi_section(self, df: pd.DataFrame) -> list:
        num_df = df.select_dtypes(include="number")
        if num_df.empty:
            return []

        kpi_style = ParagraphStyle("kpi_val", fontSize=18, textColor=NAVY, alignment=TA_CENTER, leading=22)
        lbl_style = ParagraphStyle("kpi_lbl", fontSize=9, textColor=colors.gray, alignment=TA_CENTER)

        kpis = []
        for col in list(num_df.columns)[:4]:
            val = num_df[col].sum()
            label = col.replace("_", " ").title()
            kpis.append(
                [
                    Paragraph(f"{val:,.2f}", kpi_style),
                    Paragraph(label, lbl_style),
                ]
            )

        # Pad to 4
        while len(kpis) < 4:
            kpis.append(["", ""])

        col_w = ["25%", "25%", "25%", "25%"]
        # Build a 2-row table: values on top, labels below
        data = [[k[0] for k in kpis], [k[1] for k in kpis]]
        t = Table(data, colWidths=col_w)
        t.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GRAY),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        return [
            Paragraph("Key Metrics", ParagraphStyle("h2", fontSize=12, textColor=NAVY, spaceAfter=6)),
            t,
        ]

    # ── Data table ───────────────────────────────────────────────────────────

    def _data_table_section(self, df: pd.DataFrame) -> list:
        MAX_ROWS = 200
        display_df = df.head(MAX_ROWS)

        header_style = ParagraphStyle("th", fontSize=9, textColor=WHITE, alignment=TA_CENTER)
        cell_style = ParagraphStyle("td", fontSize=8, alignment=TA_LEFT)

        headers = [Paragraph(str(c).replace("_", " ").title(), header_style) for c in display_df.columns]
        rows = [headers]

        for _, row in display_df.iterrows():
            rows.append([Paragraph(str(v) if v is not None else "", cell_style) for v in row])

        # Auto column widths (equal split)
        available_w = 25 * cm
        col_w = [available_w / len(display_df.columns)] * len(display_df.columns)

        t = Table(rows, colWidths=col_w, repeatRows=1)

        style = [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        t.setStyle(TableStyle(style))

        heading = Paragraph(
            "Data",
            ParagraphStyle("h2", fontSize=12, textColor=NAVY, spaceBefore=10, spaceAfter=6),
        )
        elements = [heading, t]

        if len(df) > MAX_ROWS:
            note_style = ParagraphStyle("note", fontSize=8, textColor=colors.gray, spaceBefore=4)
            elements.append(Paragraph(f"Showing first {MAX_ROWS} of {len(df)} rows.", note_style))

        return elements

    # ── Footer ───────────────────────────────────────────────────────────────

    def _page_footer(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.gray)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        canvas.drawString(1.5 * cm, 1 * cm, f"Generated: {ts}")
        canvas.drawRightString(
            doc.pagesize[0] - 1.5 * cm,
            1 * cm,
            f"Page {doc.page}",
        )
        canvas.restoreState()
