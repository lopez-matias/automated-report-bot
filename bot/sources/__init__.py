from .base import BaseSource
from .postgres import PostgresSource
from .csv_source import CsvSource
from .api_source import ApiSource
from .excel_source import ExcelSource

SOURCE_REGISTRY = {
    "postgres": PostgresSource,
    "csv": CsvSource,
    "api": ApiSource,
    "excel": ExcelSource,
}


def get_source(config: dict) -> BaseSource:
    source_type = config.get("type", "").lower()
    cls = SOURCE_REGISTRY.get(source_type)
    if not cls:
        raise ValueError(f"Unknown source type: {source_type!r}")
    return cls(config)
