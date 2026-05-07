import pandas as pd
from .base import BaseTransformer


class WeekOverWeekTransformer(BaseTransformer):
    """Add week-over-week percentage change column."""

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        column = self.config.get("column", "revenue")
        df = df.copy()
        df["wow_change"] = df[column].pct_change() * 100
        return df


class RevenueKpiTransformer(BaseTransformer):
    """Compute total, average, and max revenue as new summary columns (single-row summary)."""

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        col = self.config.get("column", "revenue")
        if col not in df.columns:
            return df
        summary = pd.DataFrame(
            {
                "total_revenue": [df[col].sum()],
                "avg_revenue": [df[col].mean()],
                "max_revenue": [df[col].max()],
                "min_revenue": [df[col].min()],
            }
        )
        return summary


class RegionRankTransformer(BaseTransformer):
    """Rank rows by a numeric column descending."""

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        column = self.config.get("column", "revenue")
        df = df.copy()
        df["rank"] = df[column].rank(method="dense", ascending=False).astype(int)
        return df.sort_values("rank").reset_index(drop=True)


SALES_TRANSFORMER_REGISTRY = {
    "wow_change": WeekOverWeekTransformer,
    "revenue_kpi": RevenueKpiTransformer,
    "region_rank": RegionRankTransformer,
}
