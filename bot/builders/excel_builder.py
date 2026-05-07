import io
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import openpyxl
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side, numbers
)
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule
from openpyxl.chart import BarChart, LineChart, Reference

logger = logging.getLogger(__name__)

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
ROW_ALT_FILL = PatternFill("solid", fgColor="F2F2F2")
HEADER_FONT = Font(bold=True, color="FFFFFF", name="Calibri", size=11)
BODY_FONT = Font(name="Calibri", size=10)
GREEN_FILL = PatternFill("solid", fgColor="C6EFCE")
RED_FILL = PatternFill("solid", fgColor="FFC7CE")

thin = Side(border_style="thin", color="D9D9D9")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)


def _auto_fit(ws):
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.value is not None:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_len + 4, 40)


def _write_data_sheet(ws, df: pd.DataFrame):
    ws.title = "Data"

    # Header row
    for c_idx, col_name in enumerate(df.columns, 1):
        cell = ws.cell(row=1, column=c_idx, value=str(col_name))
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER

    # Data rows
    for r_idx, row in enumerate(df.itertuples(index=False), 2):
        fill = ROW_ALT_FILL if r_idx % 2 == 0 else PatternFill()
        for c_idx, value in enumerate(row, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=value)
            cell.fill = fill
            cell.font = BODY_FONT
            cell.border = BORDER
            cell.alignment = Alignment(vertical="center")

    # Freeze header
    ws.freeze_panes = "A2"

    # Conditional formatting: green positive, red negative (numeric columns)
    if len(df) == 0:
        _auto_fit(ws)
        return
    for c_idx, col_name in enumerate(df.columns, 1):
        col_letter = get_column_letter(c_idx)
        data_range = f"{col_letter}2:{col_letter}{len(df) + 1}"
        ws.conditional_formatting.add(
            data_range,
            CellIsRule(operator="greaterThan", formula=["0"], fill=GREEN_FILL),
        )
        ws.conditional_formatting.add(
            data_range,
            CellIsRule(operator="lessThan", formula=["0"], fill=RED_FILL),
        )

    _auto_fit(ws)


def _write_summary_sheet(ws, df: pd.DataFrame):
    ws.title = "Summary"
    ws.sheet_view.showGridLines = False

    title_cell = ws.cell(row=1, column=1, value="Key Performance Indicators")
    title_cell.font = Font(bold=True, size=14, color="1F3864", name="Calibri")
    ws.merge_cells("A1:D1")

    ws.cell(row=2, column=1, value="Metric").font = HEADER_FONT
    ws.cell(row=2, column=1).fill = HEADER_FILL
    ws.cell(row=2, column=2, value="Value").font = HEADER_FONT
    ws.cell(row=2, column=2).fill = HEADER_FILL

    numeric_cols = df.select_dtypes(include="number").columns
    row = 3
    for col in numeric_cols:
        ws.cell(row=row, column=1, value=f"Total {col}").font = BODY_FONT
        ws.cell(row=row, column=2, value=round(df[col].sum(), 2)).font = BODY_FONT
        row += 1
        ws.cell(row=row, column=1, value=f"Avg {col}").font = BODY_FONT
        ws.cell(row=row, column=2, value=round(df[col].mean(), 2)).font = BODY_FONT
        row += 1
        ws.cell(row=row, column=1, value=f"Max {col}").font = BODY_FONT
        ws.cell(row=row, column=2, value=round(df[col].max(), 2)).font = BODY_FONT
        row += 1

    ws.cell(row=row, column=1, value="Total Rows").font = BODY_FONT
    ws.cell(row=row, column=2, value=len(df)).font = BODY_FONT

    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 18


def _write_chart_sheet(ws, df: pd.DataFrame, data_ws):
    ws.title = "Chart"

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        ws.cell(row=1, column=1, value="No numeric data available for chart")
        return

    chart = BarChart()
    chart.type = "col"
    chart.title = "Data Overview"
    chart.style = 10
    chart.y_axis.title = numeric_cols[0]
    chart.x_axis.title = df.columns[0]

    n_rows = len(df) + 1
    col_idx = df.columns.tolist().index(numeric_cols[0]) + 1

    data_ref = Reference(data_ws, min_col=col_idx, min_row=1, max_row=n_rows)
    cats = Reference(data_ws, min_col=1, min_row=2, max_row=n_rows)
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cats)
    chart.shape = 4
    ws.add_chart(chart, "A1")


def _write_info_sheet(ws, df: pd.DataFrame, report_name: str, source_type: str):
    ws.title = "Info"
    ws.sheet_view.showGridLines = False

    info = [
        ("Report Name", report_name),
        ("Generated At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ("Source Type", source_type),
        ("Row Count", len(df)),
        ("Column Count", len(df.columns)),
        ("Columns", ", ".join(df.columns.tolist())),
    ]

    ws.cell(row=1, column=1, value="Report Metadata").font = Font(
        bold=True, size=13, color="1F3864", name="Calibri"
    )
    ws.merge_cells("A1:B1")

    for r, (key, val) in enumerate(info, 3):
        ws.cell(row=r, column=1, value=key).font = Font(bold=True, name="Calibri")
        ws.cell(row=r, column=2, value=str(val)).font = BODY_FONT

    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 50


def build_excel(
    df: pd.DataFrame,
    report_name: str = "Report",
    source_type: str = "unknown",
    output_path: str = None,
) -> bytes:
    wb = openpyxl.Workbook()
    ws_data = wb.active
    _write_data_sheet(ws_data, df)

    ws_summary = wb.create_sheet()
    _write_summary_sheet(ws_summary, df)

    ws_chart = wb.create_sheet()
    _write_chart_sheet(ws_chart, df, ws_data)

    ws_info = wb.create_sheet()
    _write_info_sheet(ws_info, df, report_name, source_type)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        wb.save(output_path)
        logger.info(f"Excel saved to {output_path}")

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
