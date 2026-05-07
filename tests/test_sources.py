import os
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from bot.sources import get_source
from bot.sources.csv_source import CsvSource
from bot.sources.api_source import ApiSource
from bot.sources.excel_source import ExcelSource


# ── CSV Source ────────────────────────────────────────────────────────────────

def test_csv_source_basic(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("a,b,c\n1,2,3\n4,5,6\n")
    src = CsvSource({"path": str(csv_file)})
    df = src.fetch()
    assert len(df) == 2
    assert list(df.columns) == ["a", "b", "c"]


def test_csv_source_semicolon_sep(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("a;b\n1;2\n3;4\n")
    src = CsvSource({"path": str(csv_file), "separator": ";"})
    df = src.fetch()
    assert len(df) == 2


def test_csv_source_missing_columns_logged(tmp_path, caplog):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("x,y\n1,2\n")
    src = CsvSource({"path": str(csv_file), "columns": ["x", "z"]})
    import logging
    with caplog.at_level(logging.WARNING):
        df = src.fetch()
    assert "z" in caplog.text


def test_csv_source_inventory(tmp_path):
    # Test with the real seed file
    real_path = Path(__file__).parent.parent / "data" / "inventory.csv"
    if not real_path.exists():
        pytest.skip("Seed file not found")
    src = CsvSource({"path": str(real_path)})
    df = src.fetch()
    assert len(df) == 15
    assert "sku" in df.columns


# ── API Source ────────────────────────────────────────────────────────────────

def test_api_source_basic():
    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": 1, "value": 42}, {"id": 2, "value": 99}]
    mock_response.raise_for_status = MagicMock()

    with patch("bot.sources.api_source.requests.get", return_value=mock_response):
        src = ApiSource({"url": "http://example.com/api", "paginate": False})
        df = src.fetch()

    assert len(df) == 2
    assert "id" in df.columns
    assert "value" in df.columns


def test_api_source_data_key():
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {"items": [{"x": 1}, {"x": 2}]}}
    mock_response.raise_for_status = MagicMock()

    with patch("bot.sources.api_source.requests.get", return_value=mock_response):
        src = ApiSource({"url": "http://example.com/api", "data_key": "data.items"})
        df = src.fetch()

    assert len(df) == 2


def test_api_source_bearer_token():
    mock_response = MagicMock()
    mock_response.json.return_value = [{"k": "v"}]
    mock_response.raise_for_status = MagicMock()

    with patch("bot.sources.api_source.requests.get", return_value=mock_response) as mock_get:
        src = ApiSource({"url": "http://example.com/api", "token": "secret123"})
        src.fetch()

    _, kwargs = mock_get.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer secret123"


# ── Excel Source ──────────────────────────────────────────────────────────────

def test_excel_source(tmp_path):
    df_orig = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
    xlsx = tmp_path / "test.xlsx"
    df_orig.to_excel(str(xlsx), index=False)

    src = ExcelSource({"path": str(xlsx)})
    df = src.fetch()
    assert len(df) == 3
    assert "col1" in df.columns


# ── Registry ──────────────────────────────────────────────────────────────────

def test_get_source_unknown_type():
    with pytest.raises(ValueError, match="Unknown source type"):
        get_source({"type": "foobar"})


def test_get_source_returns_correct_class():
    from bot.sources.csv_source import CsvSource as CSV
    src = get_source({"type": "csv", "path": "/tmp/x.csv"})
    assert isinstance(src, CSV)
