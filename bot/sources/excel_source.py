import logging
import pandas as pd
from .base import BaseSource

logger = logging.getLogger(__name__)


class ExcelSource(BaseSource):
    def fetch(self) -> pd.DataFrame:
        path = self.config["path"]
        sheet = self.config.get("sheet", 0)
        skiprows = self.config.get("skiprows", 0)

        df = pd.read_excel(path, sheet_name=sheet, skiprows=skiprows)
        logger.info("Excel fetched %d rows from %s (sheet=%s)", len(df), path, sheet)
        return df
