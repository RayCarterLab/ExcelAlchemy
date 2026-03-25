"""Header parsing and validation helpers for import workbooks."""

from excelalchemy.core.table import WorksheetTable
from excelalchemy.exc import ConfigError
from excelalchemy.types.alchemy import ImportMode
from excelalchemy.types.header import ExcelHeader
from excelalchemy.types.identity import Label, UniqueLabel
from excelalchemy.types.result import ValidateHeaderResult
from excelalchemy.util.file import value_is_nan

from .schema import ExcelSchemaLayout


class ExcelHeaderParser:
    """Parse raw worksheet header rows into normalized header objects."""

    def has_merged_header(self, header_df: WorksheetTable) -> bool:
        """Detect whether the workbook uses a merged two-row header."""
        return any(value_is_nan(value) for value in header_df.iloc[0].tolist()) or any(
            header_df.iloc[0].str.startswith('Unnamed')
        )

    def extract(self, header_df: WorksheetTable) -> list[ExcelHeader]:
        """Parse either a simple header row or a merged header block."""
        if self.has_merged_header(header_df):
            return self._extract_merged(header_df)
        return self._extract_simple(header_df)

    def _extract_simple(self, header_df: WorksheetTable) -> list[ExcelHeader]:
        return [ExcelHeader(label=Label(col), parent_label=Label(col)) for col in header_df.iloc[0].tolist()]

    def _extract_merged(self, header_df: WorksheetTable) -> list[ExcelHeader]:
        headers: list[ExcelHeader] = []
        last_header: str | None = None
        next_offset = 1

        for column_index, value in header_df.iloc[0].items():
            parent_value = value
            child_value = header_df.iloc[1][column_index]
            if value_is_nan(parent_value) or (isinstance(parent_value, str) and parent_value.startswith('Unnamed')):
                if value_is_nan(child_value):
                    raise ValueError('合并表头错误: 子表头不能为空')
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
                last_header, next_offset = value, 1
            headers.append(current_header)

        return headers

    def apply_columns(
        self,
        df: WorksheetTable,
        headers: list[ExcelHeader],
        allowed_labels: list[UniqueLabel],
    ) -> WorksheetTable:
        """Assign normalized unique labels as worksheet table columns."""
        columns: list[UniqueLabel] = []
        for header in headers:
            if header.unique_label not in allowed_labels:
                raise ConfigError(f'不支持的列名: {header.unique_label}')
            columns.append(header.unique_label)

        df.columns = columns  # type: ignore[assignment]
        return df


class ExcelHeaderValidator:
    """Validate parsed headers against one schema layout."""

    def validate(
        self,
        headers: list[ExcelHeader],
        layout: ExcelSchemaLayout,
        import_mode: ImportMode,
    ) -> ValidateHeaderResult:
        """Return the full header validation result consumed by the facade."""
        required_labels = [field_meta.label for field_meta in layout.ordered_field_meta if field_meta.required]
        primary_labels = [field_meta.label for field_meta in layout.ordered_field_meta if field_meta.is_primary_key]
        input_labels = [header.label for header in headers]

        visited: set[Label] = set()
        duplicated: list[Label] = []
        for label in input_labels:
            if label in visited:
                duplicated.append(label)
            else:
                visited.add(label)
        unrecognized = list(set(input_labels) - set(field_meta.label for field_meta in layout.ordered_field_meta))

        missing_primary: list[Label] = []
        if import_mode == ImportMode.UPDATE:
            missing_primary = list(set(primary_labels) - set(input_labels))
        missing_required = list(set(required_labels) - set(input_labels) - set(missing_primary))

        return ValidateHeaderResult(
            unrecognized=unrecognized,
            duplicated=duplicated,
            missing_required=missing_required,
            missing_primary=missing_primary,
            is_valid=not (missing_required or unrecognized or duplicated or missing_primary),
        )
