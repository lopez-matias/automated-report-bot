from .postgres import PostgresSource
from .csv_source import CSVSource
from .api_source import APISource
from .excel_source import ExcelSource

SOURCE_REGISTRY = {
    "postgres": PostgresSource,
    "csv": CSVSource,
    "api": APISource,
    "excel": ExcelSource,
}


def get_source(source_config: dict):
    source_type = source_config.get("type")
    cls = SOURCE_REGISTRY.get(source_type)
    if not cls:
        raise ValueError(f"Unknown source type: {source_type}. Valid: {list(SOURCE_REGISTRY)}")
    return cls(source_config)
