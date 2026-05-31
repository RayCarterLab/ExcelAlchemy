"""Worksheet parsing and table primitives."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from excelalchemy.worksheet.header import ExcelHeader
    from excelalchemy.worksheet.header_parser import ExcelHeaderParser
    from excelalchemy.worksheet.header_validator import ExcelHeaderValidator
    from excelalchemy.worksheet.table import (
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
        from excelalchemy.worksheet.header import ExcelHeader

        return ExcelHeader
    if name == 'ExcelHeaderParser':
        from excelalchemy.worksheet.header_parser import ExcelHeaderParser

        return ExcelHeaderParser
    if name == 'ExcelHeaderValidator':
        from excelalchemy.worksheet.header_validator import ExcelHeaderValidator

        return ExcelHeaderValidator
    if name in {'WorksheetColumn', 'WorksheetColumns', 'WorksheetRow', 'WorksheetTable', 'WorksheetValue'}:
        from excelalchemy.worksheet.table import (
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
