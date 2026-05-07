import io
import pytest
import pandas as pd
import openpyxl

from bot.builders.excel_builder import build_excel
from bot.builders.pdf_builder import build_pdf


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "region": ["North", "South", "East", "West"],
        "revenue": [5000.0, 3000.0, 7000.0, 4000.0],
        "orders": [50, 30, 70, 40],
        "avg_order_value": [100.0, 100.0, 100.0, 100.0],
    })


# --- Excel ---

def test_excel_returns_bytes(sample_df):
    result = build_excel(sample_df)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_excel_is_valid_workbook(sample_df):
    result = build_excel(sample_df)
    wb = openpyxl.load_workbook(io.BytesIO(result))
    assert wb is not None


def test_excel_has_four_sheets(sample_df):
    result = build_excel(sample_df)
    wb = openpyxl.load_workbook(io.BytesIO(result))
    assert len(wb.sheetnames) == 4
    assert "Data" in wb.sheetnames
    assert "Summary" in wb.sheetnames
    assert "Chart" in wb.sheetnames
    assert "Info" in wb.sheetnames


def test_excel_data_sheet_header(sample_df):
    result = build_excel(sample_df)
    wb = openpyxl.load_workbook(io.BytesIO(result))
    ws = wb["Data"]
    headers = [ws.cell(row=1, column=i).value for i in range(1, len(sample_df.columns) + 1)]
    for col in sample_df.columns:
        assert col in headers


def test_excel_data_row_count(sample_df):
    result = build_excel(sample_df)
    wb = openpyxl.load_workbook(io.BytesIO(result))
    ws = wb["Data"]
    assert ws.max_row == len(sample_df) + 1  # header + data rows


def test_excel_saves_to_disk(sample_df, tmp_path):
    out = str(tmp_path / "test.xlsx")
    build_excel(sample_df, output_path=out)
    import os
    assert os.path.exists(out)
    assert os.path.getsize(out) > 0


def test_excel_empty_df():
    df = pd.DataFrame({"a": [], "b": []})
    result = build_excel(df)
    assert isinstance(result, bytes)
    wb = openpyxl.load_workbook(io.BytesIO(result))
    assert "Data" in wb.sheetnames


# --- PDF ---

def test_pdf_returns_bytes(sample_df):
    result = build_pdf(sample_df)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_pdf_is_pdf_format(sample_df):
    result = build_pdf(sample_df)
    assert result[:4] == b"%PDF"


def test_pdf_saves_to_disk(sample_df, tmp_path):
    out = str(tmp_path / "report.pdf")
    build_pdf(sample_df, report_name="Test", output_path=out)
    import os
    assert os.path.exists(out)
    assert os.path.getsize(out) > 0


def test_pdf_with_date_range(sample_df):
    result = build_pdf(sample_df, report_name="Sales", date_range="Jan 1–Jan 7, 2025")
    assert result[:4] == b"%PDF"


def test_pdf_many_columns():
    df = pd.DataFrame({f"col_{i}": range(5) for i in range(15)})
    result = build_pdf(df)
    assert result[:4] == b"%PDF"
