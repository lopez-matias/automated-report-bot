import pytest
import pandas as pd

from bot.transformers import apply_transforms
from bot.transformers.generic import (
    AddColumnTransformer,
    FormatCurrencyTransformer,
    FormatPercentTransformer,
    SortTransformer,
    FilterTransformer,
    RenameTransformer,
    DropColumnsTransformer,
    FillNaTransformer,
)
from bot.transformers.sales import WeekOverWeekTransformer, RegionRankTransformer


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "region": ["North", "South", "East", "West"],
        "revenue": [5000.0, 3000.0, 7000.0, 4000.0],
        "orders": [50, 30, 70, 40],
    })


def test_add_column(sample_df):
    t = AddColumnTransformer({"name": "aov", "formula": "revenue / orders"})
    df = t.transform(sample_df)
    assert "aov" in df.columns
    assert round(df.loc[0, "aov"], 2) == 100.0


def test_format_currency(sample_df):
    t = FormatCurrencyTransformer({"columns": ["revenue"]})
    df = t.transform(sample_df)
    assert df.loc[0, "revenue"].startswith("$")
    assert "," in df.loc[2, "revenue"]


def test_format_percent():
    df = pd.DataFrame({"rate": [0.5, 1.2, -0.3]})
    t = FormatPercentTransformer({"columns": ["rate"], "decimals": 1})
    out = t.transform(df)
    assert out.loc[0, "rate"] == "0.5%"


def test_sort_ascending(sample_df):
    t = SortTransformer({"by": "revenue", "ascending": True})
    df = t.transform(sample_df)
    assert df.iloc[0]["revenue"] == 3000.0


def test_sort_descending(sample_df):
    t = SortTransformer({"by": "revenue", "ascending": False})
    df = t.transform(sample_df)
    assert df.iloc[0]["revenue"] == 7000.0


def test_filter(sample_df):
    t = FilterTransformer({"query": "revenue > 4000"})
    df = t.transform(sample_df)
    assert len(df) == 2
    assert all(df["revenue"] > 4000)


def test_rename(sample_df):
    t = RenameTransformer({"columns": {"revenue": "total_revenue"}})
    df = t.transform(sample_df)
    assert "total_revenue" in df.columns
    assert "revenue" not in df.columns


def test_drop_columns(sample_df):
    t = DropColumnsTransformer({"columns": ["orders"]})
    df = t.transform(sample_df)
    assert "orders" not in df.columns
    assert "revenue" in df.columns


def test_fill_na():
    df = pd.DataFrame({"a": [1.0, None, 3.0], "b": [None, 2.0, None]})
    t = FillNaTransformer({"value": 0})
    out = t.transform(df)
    assert out.isnull().sum().sum() == 0


def test_region_rank(sample_df):
    t = RegionRankTransformer({"metric": "revenue"})
    df = t.transform(sample_df)
    assert "rank" in df.columns
    east_rank = df.loc[df["region"] == "East", "rank"].iloc[0]
    assert east_rank == 1


def test_apply_transforms_chain(sample_df):
    transforms = [
        {"type": "add_column", "name": "aov", "formula": "revenue / orders"},
        {"type": "sort", "by": "revenue", "ascending": False},
    ]
    df = apply_transforms(sample_df, transforms)
    assert "aov" in df.columns
    assert df.iloc[0]["revenue"] == 7000.0


def test_apply_transforms_unknown():
    with pytest.raises(ValueError, match="Unknown transformer"):
        apply_transforms(pd.DataFrame(), [{"type": "nonexistent"}])
