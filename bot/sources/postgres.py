import time
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from .base import BaseSource

logger = logging.getLogger(__name__)


class PostgresSource(BaseSource):
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def fetch(self) -> pd.DataFrame:
        url = self.config.get("url") or self._build_url()
        query = self.config["query"]

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                engine = create_engine(url)
                with engine.connect() as conn:
                    df = pd.read_sql(text(query), conn)
                logger.info("PostgreSQL fetched %d rows", len(df))
                return df
            except Exception as exc:
                logger.warning("Attempt %d/%d failed: %s", attempt, self.MAX_RETRIES, exc)
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY * attempt)
                else:
                    raise

    def _build_url(self) -> str:
        c = self.config
        return (
            f"postgresql+psycopg2://{c['user']}:{c['password']}"
            f"@{c['host']}:{c.get('port', 5432)}/{c['database']}"
        )
