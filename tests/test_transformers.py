import pandas as pd
import pytest

from bot.transformers import apply_transforms
from bot.transformers.generic import (
    AddColumnTransformer,
    DropColumnsTransformer,
    FilterTransformer,
    FormatCurrencyTransformer,
    GroupByTransformer,
    RenameTransformer,
    SortTransformer,
)
from bot.transformers.sales import RegionRankTransformer, WeekOverWeekTransformer


@pytest.fixture
def sales_df():
    return pd.DataFrame(
        {
            "date": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "region": ["East", "West", "East"],
            "revenue": [1000.0, 1500.0, 800.0],
            "orders": [10, 15, 8],
        }
    )


def test_add_column(sales_df):
    t = AddColumnTransformer({"name": "avg_order_value", "formula": "revenue / orders"})
    df = t.transform(sales_df)
    assert "avg_order_value" in df.columns
    assert round(df["avg_order_value"].iloc[0], 2) == 100.0


def test_sort_descending(sales_df):
    t = SortTransformer({"by": "revenue", "ascending": False})
    df = t.transform(sales_df)
    assert df["revenue"].iloc[0] == 1500.0


def test_sort_ascending(sales_df):
    t = SortTransformer({"by": "revenue", "ascending": True})
    df = t.transform(sales_df)
    assert df["revenue"].iloc[0] == 800.0


def test_filter_gt(sales_df):
    t = FilterTransformer({"column": "revenue", "op": "gt", "value": 900})
    df = t.transform(sales_df)
    assert len(df) == 2


def test_filter_eq(sales_df):
    t = FilterTransformer({"column": "region", "op": "eq", "value": "East"})
    df = t.transform(sales_df)
    assert len(df) == 2


def test_rename():
    df = pd.DataFrame({"old_name": [1, 2]})
    t = RenameTransformer({"mapping": {"old_name": "new_name"}})
    df = t.transform(df)
    assert "new_name" in df.columns
    assert "old_name" not in df.columns


def test_drop_columns(sales_df):
    t = DropColumnsTransformer({"columns": ["orders"]})
    df = t.transform(sales_df)
    assert "orders" not in df.columns
    assert "revenue" in df.columns


def test_format_currency_converts_to_numeric(sales_df):
    df_str = sales_df.copy()
    df_str["revenue"] = df_str["revenue"].astype(str)
    t = FormatCurrencyTransformer({"columns": ["revenue"]})
    df = t.transform(df_str)
    assert pd.api.types.is_numeric_dtype(df["revenue"])


def test_region_rank(sales_df):
    t = RegionRankTransformer({"column": "revenue"})
    df = t.transform(sales_df)
    assert "rank" in df.columns
    assert df["rank"].iloc[0] == 1


def test_wow_change(sales_df):
    t = WeekOverWeekTransformer({"column": "revenue"})
    df = t.transform(sales_df)
    assert "wow_change" in df.columns


def test_apply_transforms_pipeline(sales_df):
    transforms = [
        {"type": "add_column", "name": "aov", "formula": "revenue / orders"},
        {"type": "sort", "by": "revenue", "ascending": False},
    ]
    df = apply_transforms(sales_df, transforms)
    assert "aov" in df.columns
    assert df["revenue"].iloc[0] == 1500.0


def test_apply_transforms_unknown_type(sales_df):
    with pytest.raises(ValueError, match="Unknown transformer type"):
        apply_transforms(sales_df, [{"type": "nonexistent"}])
