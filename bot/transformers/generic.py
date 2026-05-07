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
        cols = self.config.get("columns", [])
        symbol = self.config.get("symbol", "$")
        df = df.copy()
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                df[col] = df[col].apply(
                    lambda x: f"{symbol}{x:,.2f}" if pd.notna(x) else ""
                )
        return df


class FormatPercentTransformer(BaseTransformer):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = self.config.get("columns", [])
        decimals = self.config.get("decimals", 1)
        df = df.copy()
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                df[col] = df[col].apply(
                    lambda x: f"{x:.{decimals}f}%" if pd.notna(x) else ""
                )
        return df


class SortTransformer(BaseTransformer):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        by = self.config.get("by")
        ascending = self.config.get("ascending", True)
        if by and by in df.columns:
            df = df.sort_values(by=by, ascending=ascending).reset_index(drop=True)
        return df


class FilterTransformer(BaseTransformer):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        query = self.config.get("query")
        if query:
            df = df.query(query).reset_index(drop=True)
        return df


class RenameTransformer(BaseTransformer):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        mapping = self.config.get("columns", {})
        return df.rename(columns=mapping)


class DropColumnsTransformer(BaseTransformer):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = self.config.get("columns", [])
        existing = [c for c in cols if c in df.columns]
        return df.drop(columns=existing)


class FillNaTransformer(BaseTransformer):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        value = self.config.get("value", 0)
        cols = self.config.get("columns")
        df = df.copy()
        if cols:
            for col in cols:
                if col in df.columns:
                    df[col] = df[col].fillna(value)
        else:
            df = df.fillna(value)
        return df
