import pandas as pd
from .base import BaseTransformer


class AddColumnTransformer(BaseTransformer):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        name = self.config["name"]
        formula = self.config["formula"]
        df = df.copy()
        df[name] = df.eval(formula)
        return df


class FormatCurrencyTransformer(BaseTransformer):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        columns = self.config.get("columns", [])
        symbol = self.config.get("symbol", "$")
        df = df.copy()
        for col in columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df


class SortTransformer(BaseTransformer):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        by = self.config["by"]
        ascending = self.config.get("ascending", True)
        return df.sort_values(by=by, ascending=ascending).reset_index(drop=True)


class FilterTransformer(BaseTransformer):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        column = self.config["column"]
        op = self.config["op"]
        value = self.config["value"]
        ops = {
            "eq": lambda s: s == value,
            "ne": lambda s: s != value,
            "gt": lambda s: s > value,
            "lt": lambda s: s < value,
            "gte": lambda s: s >= value,
            "lte": lambda s: s <= value,
            "contains": lambda s: s.str.contains(str(value), na=False),
        }
        if op not in ops:
            raise ValueError(f"Unsupported filter op: {op!r}")
        return df[ops[op](df[column])].reset_index(drop=True)


class RenameTransformer(BaseTransformer):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        mapping = self.config["mapping"]
        return df.rename(columns=mapping)


class DropColumnsTransformer(BaseTransformer):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        columns = self.config["columns"]
        return df.drop(columns=[c for c in columns if c in df.columns])


class GroupByTransformer(BaseTransformer):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        by = self.config["by"]
        agg = self.config["agg"]
        return df.groupby(by).agg(agg).reset_index()


TRANSFORMER_REGISTRY = {
    "add_column": AddColumnTransformer,
    "format_currency": FormatCurrencyTransformer,
    "sort": SortTransformer,
    "filter": FilterTransformer,
    "rename": RenameTransformer,
    "drop_columns": DropColumnsTransformer,
    "group_by": GroupByTransformer,
}
