from .excel_builder import ExcelBuilder
from .pdf_builder import PdfBuilder


def get_builder(fmt: str, config: dict):
    if fmt == "excel":
        return ExcelBuilder(config)
    if fmt == "pdf":
        return PdfBuilder(config)
    raise ValueError(f"Unknown format: {fmt!r}")
