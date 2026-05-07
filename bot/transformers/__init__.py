import pandas as pd
from .generic import (
    AddColumnTransformer,
    FormatCurrencyTransformer,
    FormatPercentTransformer,
    SortTransformer,
    FilterTransformer,
    RenameTransformer,
    DropColumnsTransformer,
    FillNaTransformer,
)
from .sales import WeekOverWeekTransformer, RegionRankTransformer

TRANSFORMER_REGISTRY = {
    "add_column": AddColumnTransformer,
    "format_currency": FormatCurrencyTransformer,
    "format_percent": FormatPercentTransformer,
    "sort": SortTransformer,
    "filter": FilterTransformer,
    "rename": RenameTransformer,
    "drop_columns": DropColumnsTransformer,
    "fill_na": FillNaTransformer,
    "week_over_week": WeekOverWeekTransformer,
    "region_rank": RegionRankTransformer,
}


def apply_transforms(df: pd.DataFrame, transform_configs: list) -> pd.DataFrame:
    for cfg in transform_configs:
        t_type = cfg.get("type")
        cls = TRANSFORMER_REGISTRY.get(t_type)
        if not cls:
            raise ValueError(f"Unknown transformer: {t_type}. Valid: {list(TRANSFORMER_REGISTRY)}")
        df = cls(cfg).transform(df)
    return df
