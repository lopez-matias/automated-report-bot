import logging
import requests
import pandas as pd
from .base import BaseSource

logger = logging.getLogger(__name__)


class ApiSource(BaseSource):
    def fetch(self) -> pd.DataFrame:
        url = self.config["url"]
        token = self.config.get("token")
        params = self.config.get("params", {})
        data_key = self.config.get("data_key")
        page_param = self.config.get("page_param", "page")
        paginate = self.config.get("paginate", False)

        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        records = []
        page = 1

        while True:
            if paginate:
                params = {**params, page_param: page}

            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            payload = resp.json()

            page_records = payload
            if data_key:
                for key in data_key.split("."):
                    page_records = page_records[key]

            if not page_records:
                break

            records.extend(page_records if isinstance(page_records, list) else [page_records])

            if not paginate:
                break
            page += 1

        df = pd.json_normalize(records)
        logger.info("API fetched %d rows from %s", len(df), url)
        return df
