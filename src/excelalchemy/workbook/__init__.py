"""Workbook parsing and table primitives."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from excelalchemy.workbook.header_models import ExcelHeader
    from excelalchemy.workbook.headers import ExcelHeaderParser, ExcelHeaderValidator
    from excelalchemy.workbook.table import (
        WorksheetColumn,
        WorksheetColumns,
        WorksheetRow,
        WorksheetTable,
        WorksheetValue,
    )

__all__ = [
    'ExcelHeader',
    'ExcelHeaderParser',
    'ExcelHeaderValidator',
    'WorksheetColumn',
    'WorksheetColumns',
    'WorksheetRow',
    'WorksheetTable',
    'WorksheetValue',
]


def __getattr__(name: str) -> object:
    if name == 'ExcelHeader':
        from excelalchemy.workbook.header_models import ExcelHeader

        return ExcelHeader
    if name in {'ExcelHeaderParser', 'ExcelHeaderValidator'}:
        from excelalchemy.workbook.headers import ExcelHeaderParser, ExcelHeaderValidator

        return {'ExcelHeaderParser': ExcelHeaderParser, 'ExcelHeaderValidator': ExcelHeaderValidator}[name]
    if name in {'WorksheetColumn', 'WorksheetColumns', 'WorksheetRow', 'WorksheetTable', 'WorksheetValue'}:
        from excelalchemy.workbook.table import (
            WorksheetColumn,
            WorksheetColumns,
            WorksheetRow,
            WorksheetTable,
            WorksheetValue,
        )

        return {
            'WorksheetColumn': WorksheetColumn,
            'WorksheetColumns': WorksheetColumns,
            'WorksheetRow': WorksheetRow,
            'WorksheetTable': WorksheetTable,
            'WorksheetValue': WorksheetValue,
        }[name]
    raise AttributeError(name)
