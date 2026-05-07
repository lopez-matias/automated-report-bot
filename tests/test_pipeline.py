import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from bot.pipeline import run_report, _date_range_label, _extract_kpis


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "region": ["North", "South", "East"],
        "revenue": [5000.0, 3000.0, 7000.0],
        "orders": [50, 30, 70],
    })


@pytest.fixture
def csv_report_config(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("region,revenue,orders\nNorth,5000,50\nSouth,3000,30\n")
    return {
        "name": "Test CSV Report",
        "format": "excel",
        "source": {"type": "csv", "path": str(csv_file)},
        "transform": [
            {"type": "sort", "by": "revenue", "ascending": False},
        ],
        "delivery": {},
    }


def test_date_range_label_no_dates(sample_df):
    label = _date_range_label(sample_df)
    assert "–" in label


def test_date_range_label_with_dates():
    df = pd.DataFrame({"date": ["2025-01-01", "2025-01-07"], "val": [1, 2]})
    label = _date_range_label(df)
    assert "Jan" in label


def test_extract_kpis(sample_df):
    kpis = _extract_kpis(sample_df)
    assert len(kpis) > 0
    assert "label" in kpis[0]
    assert "value" in kpis[0]


def test_run_report_csv_no_email(csv_report_config, tmp_path):
    with patch.dict("os.environ", {"OUTPUT_DIR": str(tmp_path)}):
        result = run_report(csv_report_config)
    assert result["status"] == "success"
    assert result["rows"] == 2
    assert len(result["files"]) == 1


def test_run_report_pdf_format(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("product,stock,cost\nA,100,5.0\nB,50,12.0\n")
    config = {
        "name": "PDF Report",
        "format": "pdf",
        "source": {"type": "csv", "path": str(csv_file)},
        "delivery": {},
    }
    with patch.dict("os.environ", {"OUTPUT_DIR": str(tmp_path)}):
        result = run_report(config)
    assert result["status"] == "success"
    assert any(f.endswith(".pdf") for f in result["files"])


def test_run_report_both_formats(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("x,y\n1,2\n3,4\n")
    config = {
        "name": "Both Report",
        "format": "both",
        "source": {"type": "csv", "path": str(csv_file)},
        "delivery": {},
    }
    with patch.dict("os.environ", {"OUTPUT_DIR": str(tmp_path)}):
        result = run_report(config)
    assert result["status"] == "success"
    assert len(result["files"]) == 2


def test_run_report_error_returns_error_dict(tmp_path):
    config = {
        "name": "Bad Report",
        "format": "excel",
        "source": {"type": "csv", "path": "/nonexistent/bad.csv"},
        "delivery": {},
    }
    with patch("bot.pipeline.send_alert"):
        with patch.dict("os.environ", {"OUTPUT_DIR": str(tmp_path)}):
            result = run_report(config)
    assert result["status"] == "error"
    assert "error" in result


def test_run_report_with_transforms(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("region,revenue,orders\nNorth,5000,50\nSouth,3000,30\n")
    config = {
        "name": "Transform Report",
        "format": "excel",
        "source": {"type": "csv", "path": str(csv_file)},
        "transform": [
            {"type": "add_column", "name": "aov", "formula": "revenue / orders"},
            {"type": "sort", "by": "revenue", "ascending": False},
        ],
        "delivery": {},
    }
    with patch.dict("os.environ", {"OUTPUT_DIR": str(tmp_path)}):
        result = run_report(config)
    assert result["status"] == "success"
