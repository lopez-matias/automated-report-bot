import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from bot.pipeline import ReportPipeline


SAMPLE_CONFIG = {
    "name": "Test Pipeline Report",
    "schedule": "every monday at 08:00",
    "format": "excel",
    "source": {"type": "csv", "path": "data/inventory.csv"},
    "transform": [
        {"type": "sort", "by": "quantity", "ascending": False},
    ],
    "delivery": {
        "recipients": [],
        "attach_file": True,
    },
}


@pytest.fixture
def mock_df():
    return pd.DataFrame(
        {
            "region": ["East", "West", "North"],
            "revenue": [1000.0, 1500.0, 800.0],
            "orders": [10, 15, 8],
        }
    )


def test_pipeline_runs_without_error(tmp_path, mock_df):
    cfg = {**SAMPLE_CONFIG, "delivery": {"recipients": []}}

    with patch("bot.pipeline.get_source") as mock_src, \
         patch("bot.pipeline.get_builder") as mock_builder:

        mock_src.return_value.fetch.return_value = mock_df

        mock_b = MagicMock()
        mock_b.build.return_value = str(tmp_path / "report.xlsx")
        mock_builder.return_value = mock_b

        pipeline = ReportPipeline(cfg)
        pipeline.output_dir = tmp_path
        result = pipeline.run()

    assert result["status"] == "ok"
    assert result["rows"] == 3


def test_pipeline_returns_error_on_fetch_failure(tmp_path):
    cfg = {**SAMPLE_CONFIG, "delivery": {"recipients": []}}

    with patch("bot.pipeline.get_source") as mock_src, \
         patch.dict(os.environ, {"ALERT_EMAIL": ""}):
        mock_src.return_value.fetch.side_effect = RuntimeError("DB unreachable")

        pipeline = ReportPipeline(cfg)
        pipeline.output_dir = tmp_path
        result = pipeline.run()

    assert result["status"] == "error"
    assert "DB unreachable" in result["error"]


def test_pipeline_both_formats(tmp_path, mock_df):
    cfg = {**SAMPLE_CONFIG, "format": "both", "delivery": {"recipients": []}}

    with patch("bot.pipeline.get_source") as mock_src, \
         patch("bot.pipeline.get_builder") as mock_builder:

        mock_src.return_value.fetch.return_value = mock_df
        mock_b = MagicMock()
        mock_b.build.side_effect = lambda df, path: path
        mock_builder.return_value = mock_b

        pipeline = ReportPipeline(cfg)
        pipeline.output_dir = tmp_path
        result = pipeline.run()

    assert len(result["files"]) == 2


def test_pipeline_skips_delivery_with_no_recipients(tmp_path, mock_df):
    cfg = {**SAMPLE_CONFIG, "format": "excel", "delivery": {"recipients": []}}

    with patch("bot.pipeline.get_source") as mock_src, \
         patch("bot.pipeline.get_builder") as mock_builder, \
         patch("bot.pipeline.EmailDelivery") as mock_email:

        mock_src.return_value.fetch.return_value = mock_df
        mock_b = MagicMock()
        mock_b.build.return_value = str(tmp_path / "r.xlsx")
        mock_builder.return_value = mock_b

        pipeline = ReportPipeline(cfg)
        pipeline.output_dir = tmp_path
        pipeline.run()

    mock_email.return_value.send.assert_not_called()


def test_pipeline_duration_recorded(tmp_path, mock_df):
    cfg = {**SAMPLE_CONFIG, "delivery": {"recipients": []}}

    with patch("bot.pipeline.get_source") as mock_src, \
         patch("bot.pipeline.get_builder") as mock_builder:
        mock_src.return_value.fetch.return_value = mock_df
        mock_b = MagicMock()
        mock_b.build.return_value = str(tmp_path / "r.xlsx")
        mock_builder.return_value = mock_b

        pipeline = ReportPipeline(cfg)
        pipeline.output_dir = tmp_path
        result = pipeline.run()

    assert "duration_s" in result
    assert result["duration_s"] >= 0
