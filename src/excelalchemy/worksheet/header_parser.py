"""Worksheet header parsing helpers."""

from excelalchemy.errors import ConfigError
from excelalchemy.messages import MessageKey
from excelalchemy.messages import message as msg
from excelalchemy.primitives.identity import Label, UniqueLabel
from excelalchemy.util.file import value_is_nan
from excelalchemy.worksheet.header import ExcelHeader
from excelalchemy.worksheet.table import WorksheetTable


class ExcelHeaderParser:
    """Parse raw worksheet header rows into normalized header objects."""

    def has_merged_header(self, header_table: WorksheetTable) -> bool:
        """Detect whether the worksheet uses a merged two-row header."""
        return any(value_is_nan(value) for value in header_table.iloc[0].tolist()) or any(
            header_table.iloc[0].str.startswith('Unnamed')
        )

    def extract(self, header_table: WorksheetTable) -> list[ExcelHeader]:
        """Parse either a simple header row or a merged header block."""
        if self.has_merged_header(header_table):
            return self._extract_merged(header_table)
        return self._extract_simple(header_table)

    def extract_simple(self, header_table: WorksheetTable) -> list[ExcelHeader]:
        """Parse one simple header row without merged-header detection."""
        return self._extract_simple(header_table)

    def extract_merged(self, header_table: WorksheetTable) -> list[ExcelHeader]:
        """Parse a two-row merged header block without auto-detection."""
        return self._extract_merged(header_table)

    def _extract_simple(self, header_table: WorksheetTable) -> list[ExcelHeader]:
        return [ExcelHeader(label=Label(col), parent_label=Label(col)) for col in header_table.iloc[0].tolist()]

    def _extract_merged(self, header_table: WorksheetTable) -> list[ExcelHeader]:
        headers: list[ExcelHeader] = []
        last_header: str | None = None
        next_offset = 1

        for column_index, value in header_table.iloc[0].items():
            parent_value = value
            child_value = header_table.iloc[1][column_index]
            if value_is_nan(parent_value) or (isinstance(parent_value, str) and parent_value.startswith('Unnamed')):
                if value_is_nan(child_value):
                    raise ValueError(msg(MessageKey.INVALID_MERGED_HEADER_CHILD_EMPTY))
                current_header = ExcelHeader(
                    label=Label(child_value),
                    parent_label=Label(last_header),
                    offset=next_offset,
                )
                next_offset += 1
            else:
                if value_is_nan(child_value):
                    child_value = parent_value
                current_header = ExcelHeader(label=Label(child_value), parent_label=Label(value))
                last_header, next_offset = str(value), 1
            headers.append(current_header)

        return headers

    def apply_columns(
        self,
        worksheet_table: WorksheetTable,
        headers: list[ExcelHeader],
        allowed_labels: list[UniqueLabel],
    ) -> WorksheetTable:
        """Assign normalized unique labels as worksheet table columns."""
        columns: list[UniqueLabel] = []
        for header in headers:
            if header.unique_label not in allowed_labels:
                raise ConfigError(msg(MessageKey.UNSUPPORTED_COLUMN_NAME, unique_label=header.unique_label))
            columns.append(header.unique_label)

        worksheet_table.columns = columns
        return worksheet_table


__all__ = ['ExcelHeaderParser']
