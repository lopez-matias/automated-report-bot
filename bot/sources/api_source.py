import logging
import requests
import pandas as pd
from .base import BaseSource

logger = logging.getLogger(__name__)


def _flatten(obj: dict, parent_key: str = "", sep: str = ".") -> dict:
    items = {}
    for k, v in obj.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(_flatten(v, new_key, sep))
        else:
            items[new_key] = v
    return items


class APISource(BaseSource):
    def extract(self) -> pd.DataFrame:
        url = self.config.get("url")
        if not url:
            raise ValueError("APISource requires a 'url' in config")

        headers = {}
        token = self.config.get("bearer_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        headers.update(self.config.get("headers", {}))

        params = self.config.get("params", {})
        data_key = self.config.get("data_key")
        next_page_key = self.config.get("next_page_key")

        records = []
        current_url = url

        while current_url:
            resp = requests.get(current_url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            payload = resp.json()

            rows = payload
            if data_key:
                for key in data_key.split("."):
                    rows = rows[key]

            if isinstance(rows, list):
                for row in rows:
                    records.append(_flatten(row) if isinstance(row, dict) else {"value": row})
            elif isinstance(rows, dict):
                records.append(_flatten(rows))

            current_url = None
            if next_page_key and isinstance(payload, dict):
                current_url = payload.get(next_page_key)
            params = {}

        df = pd.DataFrame(records)
        logger.info(f"APISource extracted {len(df)} rows from {url}")
        return df
