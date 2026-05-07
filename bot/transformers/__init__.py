from .generic import TRANSFORMER_REGISTRY
from .sales import SALES_TRANSFORMER_REGISTRY
from .base import BaseTransformer

ALL_TRANSFORMERS = {**TRANSFORMER_REGISTRY, **SALES_TRANSFORMER_REGISTRY}


def apply_transforms(df, transform_configs: list):
    for cfg in transform_configs:
        t_type = cfg.get("type")
        cls = ALL_TRANSFORMERS.get(t_type)
        if not cls:
            raise ValueError(f"Unknown transformer type: {t_type!r}")
        df = cls(cfg).transform(df)
    return df
