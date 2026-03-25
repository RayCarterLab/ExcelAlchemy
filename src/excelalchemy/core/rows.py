"""Row aggregation and import issue tracking helpers."""

from collections import defaultdict
from typing import Any, cast

from excelalchemy.exc import ConfigError, ExcelCellError, ExcelRowError
from excelalchemy.types.alchemy import ImportMode
from excelalchemy.types.field import FieldMetaInfo
from excelalchemy.types.identity import ColumnIndex, Key, RowIndex, UniqueLabel
from excelalchemy.types.result import ValidateRowResult
from excelalchemy.util.file import value_is_nan

from .schema import ExcelSchemaLayout
from .table import WorksheetTable


class RowAggregator:
    """Group flattened worksheet cells back into model-shaped payloads."""

    def __init__(self, layout: ExcelSchemaLayout, import_mode: ImportMode):
        self.layout = layout
        self.import_mode = import_mode

    def aggregate(self, row_data: dict[UniqueLabel, Any]) -> dict[Key, Any]:
        """Aggregate one worksheet row into a serializer-ready payload."""
        return self._serialize(self._aggregate(row_data))

    def _aggregate(self, row_data: dict[UniqueLabel, Any]) -> dict[Key, Any]:
        aggregated: dict[Key, Any] = {}
        for unique_label, value in row_data.items():
            field_meta = self.layout.unique_label_to_field_meta[unique_label]

            if field_meta.key is None or field_meta.parent_key is None:
                raise ConfigError(f'{type(field_meta).__name__} 未配置 key/parent_key')

            if value_is_nan(value):
                if self.import_mode in {ImportMode.UPDATE, ImportMode.CREATE_OR_UPDATE}:
                    value = None
                else:
                    continue

            if field_meta.parent_key == field_meta.key:
                aggregated[field_meta.key] = value
            else:
                aggregated.setdefault(field_meta.parent_key, {})
                aggregated[field_meta.parent_key][field_meta.key] = value
        return aggregated

    def _serialize(self, aggregated: dict[Key, Any]) -> dict[Key, Any]:
        serialized: dict[Key, Any] = {}
        for parent_key, value in aggregated.items():
            field_metas = self.layout.parent_key_to_field_metas[parent_key]
            validator = field_metas[0]
            if value is None:
                serialized[parent_key] = None
            else:
                serialized[parent_key] = validator.value_type.serialize(value, validator)
        return serialized


class ImportIssueTracker:
    """Keep row and cell level import issues in workbook coordinates."""

    def __init__(self, layout: ExcelSchemaLayout, import_result_field_meta: list[FieldMetaInfo]):
        self.layout = layout
        self.import_result_field_meta = import_result_field_meta
        self.cell_errors: dict[RowIndex, dict[ColumnIndex, list[ExcelCellError]]] = {}
        self.row_errors: dict[RowIndex, list[ExcelRowError | ExcelCellError]] = defaultdict(list)

    def register_row_error(
        self,
        row_index: RowIndex,
        error: ExcelRowError | ExcelCellError | list[ExcelRowError | ExcelCellError] | list[ExcelCellError],
    ) -> None:
        """Record one row-level issue or a batch of issues for the same row."""
        if isinstance(error, list):
            self.row_errors[row_index].extend(error)
        else:
            self.row_errors[row_index].append(error)

    def register_cell_errors(self, row_index: RowIndex, errors: list[ExcelCellError], df: WorksheetTable) -> None:
        """Map cell errors from schema labels to rendered workbook coordinates."""
        for error in errors:
            for index in self._column_indices(df, error.unique_label):
                column_index = cast(ColumnIndex, index + len(self.import_result_field_meta))
                self.cell_errors.setdefault(row_index, {}).setdefault(column_index, []).append(error)

    def add_result_columns(
        self,
        df: WorksheetTable,
        *,
        result_unique_label: UniqueLabel,
        reason_unique_label: UniqueLabel,
        extra_header_count_on_import: int,
    ) -> None:
        """Insert result and reason columns into the rendered import result workbook."""
        result: list[str] = []
        reason: list[str] = []

        for index in df.index[extra_header_count_on_import:]:
            row_errors = self.row_errors.get(index)
            if not row_errors:
                result.append(str(ValidateRowResult.SUCCESS))
                reason.append('')
                continue

            result.append(str(ValidateRowResult.FAIL))
            numbered_reasons = [
                f'{idx}、{str(error)}' for idx, error in enumerate(self.layout.order_errors(row_errors), start=1)
            ]
            reason.append('\n'.join(numbered_reasons))

        if extra_header_count_on_import == 1:
            result = [str(result_unique_label)] + result
            reason = [str(reason_unique_label)] + reason

        df.insert(loc=0, column=reason_unique_label, value=reason)
        df.insert(loc=0, column=result_unique_label, value=result)

    def _column_indices(self, df: WorksheetTable, unique_label: UniqueLabel):
        if unique_label not in self.layout.unique_label_to_field_meta:
            if unique_label not in self.layout.parent_label_to_field_metas:
                raise ValueError(f'找不到 {unique_label} 对应的字段')

            for field_meta in self.layout.parent_label_to_field_metas[unique_label]:
                yield from self._single_column_index(df, field_meta.unique_label)
            return

        yield from self._single_column_index(df, unique_label)

    @staticmethod
    def _single_column_index(df: WorksheetTable, unique_label: UniqueLabel):
        index = df.columns.get_loc(unique_label)
        if isinstance(index, int):
            yield ColumnIndex(index)
            return
        raise ValueError(f'找不到 {unique_label} 对应的列, 推测是 value_type 定义不正确')
