import logging
import pandas as pd
from .base import BaseSource

logger = logging.getLogger(__name__)

ENCODINGS = ["utf-8", "latin-1", "cp1252", "utf-8-sig"]


class CSVSource(BaseSource):
    def extract(self) -> pd.DataFrame:
        path = self.config.get("path")
        if not path:
            raise ValueError("CSVSource requires a 'path' in config")

        sep = self.config.get("separator", ",")
        skip_rows = self.config.get("skip_rows", 0)
        columns = self.config.get("columns")

        for encoding in ENCODINGS:
            try:
                df = pd.read_csv(path, sep=sep, skiprows=skip_rows, encoding=encoding)
                if columns:
                    available = [c for c in columns if c in df.columns]
                    df = df[available]
                logger.info(f"CSVSource extracted {len(df)} rows from {path}")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                raise RuntimeError(f"CSVSource failed to read {path}: {e}") from e

        raise RuntimeError(f"Could not decode {path} with any supported encoding")
