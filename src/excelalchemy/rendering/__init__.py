"""Workbook rendering helpers."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from excelalchemy.rendering.renderer import ExcelRenderer
    from excelalchemy.rendering.writer import (
        render_data_excel,
        render_merged_header_excel,
        render_simple_header_excel,
    )

__all__ = [
    'ExcelRenderer',
    'render_data_excel',
    'render_merged_header_excel',
    'render_simple_header_excel',
]


def __getattr__(name: str) -> object:
    if name == 'ExcelRenderer':
        from excelalchemy.rendering.renderer import ExcelRenderer

        return ExcelRenderer
    if name in {'render_data_excel', 'render_merged_header_excel', 'render_simple_header_excel'}:
        from excelalchemy.rendering.writer import (
            render_data_excel,
            render_merged_header_excel,
            render_simple_header_excel,
        )

        return {
            'render_data_excel': render_data_excel,
            'render_merged_header_excel': render_merged_header_excel,
            'render_simple_header_excel': render_simple_header_excel,
        }[name]
    raise AttributeError(name)
