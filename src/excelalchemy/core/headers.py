"""Header parsing and validation helpers for import workbooks."""

from excelalchemy._internal.header_models import ExcelHeader
from excelalchemy._internal.identity import Label, UniqueLabel
from excelalchemy.config import ImportMode
from excelalchemy.core.table import WorksheetTable
from excelalchemy.exceptions import ConfigError
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import message as msg
from excelalchemy.results import ValidateHeaderResult
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
                raise ConfigError(msg(MessageKey.UNSUPPORTED_COLUMN_NAME, unique_label=header.unique_label))
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
        required_labels = [field_meta.unique_label for field_meta in layout.ordered_field_meta if field_meta.required]
        primary_labels = [field_meta.unique_label for field_meta in layout.ordered_field_meta if field_meta.is_primary_key]
        schema_labels = [field_meta.unique_label for field_meta in layout.ordered_field_meta]
        input_labels = [header.unique_label for header in headers]

        visited: set[Label] = set()
        duplicated: list[Label] = []
        for label in input_labels:
            if label in visited:
                duplicated.append(label)
            else:
                visited.add(label)

        schema_label_set = set(schema_labels)
        input_label_set = set(input_labels)
        unrecognized = self._ordered_difference(input_labels, schema_label_set)

        missing_primary: list[Label] = []
        if import_mode == ImportMode.UPDATE:
            missing_primary = self._ordered_missing(primary_labels, input_label_set)
        missing_required = self._ordered_missing(required_labels, input_label_set, excluded=set(missing_primary))

        return ValidateHeaderResult(
            unrecognized=unrecognized,
            duplicated=duplicated,
            missing_required=missing_required,
            missing_primary=missing_primary,
            is_valid=not (missing_required or unrecognized or duplicated or missing_primary),
        )

    @staticmethod
    def _ordered_difference(values: list[Label], allowed: set[Label]) -> list[Label]:
        seen: set[Label] = set()
        result: list[Label] = []
        for value in values:
            if value in allowed or value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result

    @staticmethod
    def _ordered_missing(
        expected: list[Label],
        actual: set[Label],
        *,
        excluded: set[Label] | None = None,
    ) -> list[Label]:
        excluded = excluded or set()
        return [value for value in expected if value not in actual and value not in excluded]
