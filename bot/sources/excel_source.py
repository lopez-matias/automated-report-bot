import logging
import pandas as pd
from .base import BaseSource

logger = logging.getLogger(__name__)


class ExcelSource(BaseSource):
    def extract(self) -> pd.DataFrame:
        path = self.config.get("path")
        if not path:
            raise ValueError("ExcelSource requires a 'path' in config")

        sheet = self.config.get("sheet", 0)
        skip_rows = self.config.get("skip_rows", 0)
        columns = self.config.get("columns")

        try:
            df = pd.read_excel(path, sheet_name=sheet, skiprows=skip_rows)
        except Exception as e:
            raise RuntimeError(f"ExcelSource failed to read {path}: {e}") from e

        if columns:
            available = [c for c in columns if c in df.columns]
            df = df[available]

        logger.info(f"ExcelSource extracted {len(df)} rows from {path}")
        return df
