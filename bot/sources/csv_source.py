import logging
import pandas as pd
from .base import BaseSource

logger = logging.getLogger(__name__)

ENCODINGS = ["utf-8", "latin-1", "cp1252", "utf-8-sig"]


class CsvSource(BaseSource):
    def fetch(self) -> pd.DataFrame:
        path = self.config["path"]
        sep = self.config.get("separator", ",")
        required_columns = self.config.get("columns")

        df = self._read(path, sep)

        if required_columns:
            missing = [c for c in required_columns if c not in df.columns]
            if missing:
                logger.warning("Missing columns in CSV: %s", missing)

        logger.info("CSV fetched %d rows from %s", len(df), path)
        return df

    def _read(self, path: str, sep: str) -> pd.DataFrame:
        for enc in ENCODINGS:
            try:
                return pd.read_csv(path, sep=sep, encoding=enc)
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Cannot decode CSV file at {path}")
