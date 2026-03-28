"""High-level rendering helpers built on top of the low-level writer module."""

from typing import cast

from excelalchemy._internal.identity import Base64Str, ColumnIndex, RowIndex, UniqueLabel
from excelalchemy.core.table import WorksheetTable
from excelalchemy.core.writer import render_data_excel, render_merged_header_excel, render_simple_header_excel
from excelalchemy.exceptions import ExcelCellError
from excelalchemy.metadata import FieldMetaInfo


class ExcelRenderer:
    """Render templates and result workbooks for the facade layer."""

    def render_template(
        self, df: WorksheetTable, field_meta_mapping: dict[UniqueLabel, FieldMetaInfo], *, has_merged_header: bool
    ) -> Base64Str:
        """Render a template workbook with either a simple or merged header layout."""
        if has_merged_header:
            return cast(Base64Str, render_merged_header_excel(df, field_meta_mapping))
        return cast(Base64Str, render_simple_header_excel(df, field_meta_mapping))

    def render_data(
        self,
        df: WorksheetTable,
        field_meta_mapping: dict[UniqueLabel, FieldMetaInfo],
        *,
        has_merged_header: bool,
        errors: dict[RowIndex, dict[ColumnIndex, list[ExcelCellError]]] | None = None,
    ) -> Base64Str:
        """Render a data workbook and optionally annotate cell-level import errors."""
        return render_data_excel(
            df,
            errors=errors or {},
            field_meta_mapping=field_meta_mapping,
            has_merged_header=has_merged_header,
        )
