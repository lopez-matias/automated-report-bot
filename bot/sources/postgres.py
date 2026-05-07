import time
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from .base import BaseSource
from bot.config import get_db_url

logger = logging.getLogger(__name__)


class PostgresSource(BaseSource):
    def __init__(self, config: dict, db_url: str = None):
        super().__init__(config)
        self.db_url = db_url or get_db_url()
        self.max_retries = 3

    def extract(self) -> pd.DataFrame:
        query = self.config.get("query")
        if not query:
            raise ValueError("PostgresSource requires a 'query' in config")

        for attempt in range(1, self.max_retries + 1):
            try:
                engine = create_engine(self.db_url)
                with engine.connect() as conn:
                    df = pd.read_sql(text(query), conn)
                logger.info(f"PostgresSource extracted {len(df)} rows")
                return df
            except Exception as e:
                logger.warning(f"DB attempt {attempt}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                else:
                    raise
