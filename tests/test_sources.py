import os
import json
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open

from bot.sources import get_source
from bot.sources.csv_source import CSVSource
from bot.sources.api_source import APISource
from bot.sources.excel_source import ExcelSource
from bot.sources.postgres import PostgresSource


# --- CSVSource ---

def test_csv_source_reads_file(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("name,value\nalpha,10\nbeta,20\n")
    source = CSVSource({"path": str(csv_file)})
    df = source.extract()
    assert len(df) == 2
    assert list(df.columns) == ["name", "value"]


def test_csv_source_column_filter(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("name,value,extra\na,1,x\nb,2,y\n")
    source = CSVSource({"path": str(csv_file), "columns": ["name", "value"]})
    df = source.extract()
    assert "extra" not in df.columns
    assert "name" in df.columns


def test_csv_source_missing_file():
    source = CSVSource({"path": "/nonexistent/file.csv"})
    with pytest.raises(RuntimeError):
        source.extract()


def test_csv_source_requires_path():
    source = CSVSource({})
    with pytest.raises(ValueError, match="path"):
        source.extract()


# --- APISource ---

def test_api_source_flat_response():
    mock_resp = MagicMock()
    mock_resp.json.return_value = [{"id": 1, "name": "foo"}, {"id": 2, "name": "bar"}]
    mock_resp.raise_for_status = MagicMock()

    with patch("bot.sources.api_source.requests.get", return_value=mock_resp):
        source = APISource({"url": "http://fake.api/data"})
        df = source.extract()

    assert len(df) == 2
    assert "id" in df.columns


def test_api_source_data_key():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"results": [{"a": 1}, {"a": 2}]}
    mock_resp.raise_for_status = MagicMock()

    with patch("bot.sources.api_source.requests.get", return_value=mock_resp):
        source = APISource({"url": "http://fake.api/data", "data_key": "results"})
        df = source.extract()

    assert len(df) == 2


def test_api_source_bearer_token():
    mock_resp = MagicMock()
    mock_resp.json.return_value = [{"x": 1}]
    mock_resp.raise_for_status = MagicMock()

    with patch("bot.sources.api_source.requests.get", return_value=mock_resp) as mock_get:
        source = APISource({"url": "http://fake.api/data", "bearer_token": "tok123"})
        source.extract()
        call_kwargs = mock_get.call_args
        assert "Authorization" in call_kwargs.kwargs["headers"]
        assert "Bearer tok123" == call_kwargs.kwargs["headers"]["Authorization"]


def test_api_source_requires_url():
    source = APISource({})
    with pytest.raises(ValueError, match="url"):
        source.extract()


# --- ExcelSource ---

def test_excel_source_reads_file(tmp_path):
    xlsx = tmp_path / "test.xlsx"
    df_orig = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
    df_orig.to_excel(str(xlsx), index=False)

    source = ExcelSource({"path": str(xlsx)})
    df = source.extract()
    assert len(df) == 2
    assert "col1" in df.columns


def test_excel_source_requires_path():
    source = ExcelSource({})
    with pytest.raises(ValueError, match="path"):
        source.extract()


# --- get_source factory ---

def test_get_source_unknown_type():
    with pytest.raises(ValueError, match="Unknown source type"):
        get_source({"type": "ftp"})


def test_get_source_returns_correct_class():
    from bot.sources.csv_source import CSVSource
    src = get_source({"type": "csv", "path": "x.csv"})
    assert isinstance(src, CSVSource)
