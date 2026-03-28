"""Storage protocol for reading and uploading Excel workbooks."""

from typing import Protocol, runtime_checkable

from excelalchemy._primitives.identity import UrlStr
from excelalchemy.core.table import WorksheetTable


@runtime_checkable
class ExcelStorage(Protocol):
    """Minimal workbook storage contract used by ExcelAlchemy."""

    def read_excel_table(self, input_excel_name: str, *, skiprows: int, sheet_name: str) -> WorksheetTable:
        """Read one workbook object into a worksheet table."""
        ...

    def upload_excel(self, output_name: str, content_with_prefix: str) -> UrlStr:
        """Upload one rendered workbook and return its URL."""
        ...
