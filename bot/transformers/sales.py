import pandas as pd
from .base import BaseTransformer


class WeekOverWeekTransformer(BaseTransformer):
    """Adds wow_change column comparing revenue to prior week."""

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        revenue_col = self.config.get("revenue_column", "revenue")
        df = df.copy()
        if revenue_col in df.columns:
            numeric = pd.to_numeric(
                df[revenue_col].astype(str).str.replace(r"[^\d.]", "", regex=True),
                errors="coerce",
            )
            df["wow_change_pct"] = numeric.pct_change() * 100
        return df


class RegionRankTransformer(BaseTransformer):
    """Rank rows by a metric column."""

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        metric = self.config.get("metric", "revenue")
        df = df.copy()
        if metric in df.columns:
            numeric = pd.to_numeric(
                df[metric].astype(str).str.replace(r"[^\d.]", "", regex=True),
                errors="coerce",
            )
            df["rank"] = numeric.rank(ascending=False, method="dense").astype("Int64")
        return df
