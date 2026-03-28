"""Row aggregation and import issue tracking helpers."""

from collections import defaultdict
from collections.abc import Iterator
from typing import cast

from excelalchemy._primitives.identity import ColumnIndex, Key, RowIndex, UniqueLabel
from excelalchemy._primitives.payloads import AggregatedRowPayload, ModelRowPayload, RowPayloadLike
from excelalchemy.config import ImportMode
from excelalchemy.exceptions import ConfigError, ExcelCellError, ExcelRowError
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo
from excelalchemy.results import ValidateRowResult
from excelalchemy.util.file import value_is_nan

from .schema import ExcelSchemaLayout
from .table import WorksheetTable


class RowAggregator:
    """Group flattened worksheet cells back into model-shaped payloads."""

    def __init__(self, layout: ExcelSchemaLayout, import_mode: ImportMode):
        self.layout = layout
        self.import_mode = import_mode

    def aggregate(self, row_data: RowPayloadLike) -> ModelRowPayload:
        """Aggregate one worksheet row into a serializer-ready payload."""
        return self._serialize(self._aggregate(row_data))

    def _aggregate(self, row_data: RowPayloadLike) -> AggregatedRowPayload:
        aggregated: AggregatedRowPayload = {}
        for unique_label_raw, value in row_data.items():
            unique_label = UniqueLabel(unique_label_raw)
            field_meta = self.layout.unique_label_to_field_meta[unique_label]

            if field_meta.key is None or field_meta.parent_key is None:
                raise ConfigError(
                    msg(MessageKey.FIELD_META_RUNTIME_KEY_MISSING, field_meta_type=type(field_meta).__name__)
                )

            if value_is_nan(value):
                if self.import_mode in {ImportMode.UPDATE, ImportMode.CREATE_OR_UPDATE}:
                    value = None
                else:
                    continue

            if field_meta.parent_key == field_meta.key:
                aggregated[str(field_meta.key)] = value
            else:
                parent_key = str(field_meta.parent_key)
                child_key = str(field_meta.key)
                nested = aggregated.setdefault(parent_key, {})
                if not isinstance(nested, dict):
                    raise TypeError(f'Expected nested payload mapping for {parent_key!r}, got {type(nested)}')
                nested[child_key] = value
        return aggregated

    def _serialize(self, aggregated: AggregatedRowPayload) -> ModelRowPayload:
        serialized: ModelRowPayload = {}
        for parent_key, value in aggregated.items():
            field_metas = self.layout.parent_key_to_field_metas[Key(parent_key)]
            codec_field = field_metas[0]
            if value is None:
                serialized[parent_key] = None
            else:
                serialized[parent_key] = codec_field.excel_codec.parse_input(value, codec_field)
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
            row_errors = self.row_errors.get(RowIndex(index))
            if not row_errors:
                result.append(str(ValidateRowResult.SUCCESS))
                reason.append('')
                continue

            result.append(str(ValidateRowResult.FAIL))
            numbered_reasons = [
                f'{idx}、{error!s}' for idx, error in enumerate(self.layout.order_errors(row_errors), start=1)
            ]
            reason.append('\n'.join(numbered_reasons))

        if extra_header_count_on_import == 1:
            result = [str(result_unique_label), *result]
            reason = [str(reason_unique_label), *reason]

        df.insert(loc=0, column=reason_unique_label, value=reason)
        df.insert(loc=0, column=result_unique_label, value=result)

    def _column_indices(self, df: WorksheetTable, unique_label: UniqueLabel) -> Iterator[ColumnIndex]:
        if unique_label not in self.layout.unique_label_to_field_meta:
            if unique_label not in self.layout.parent_label_to_field_metas:
                raise ValueError(msg(MessageKey.FIELD_NOT_FOUND, unique_label=unique_label))

            for field_meta in self.layout.parent_label_to_field_metas[unique_label]:
                yield from self._single_column_index(df, field_meta.unique_label)
            return

        yield from self._single_column_index(df, unique_label)

    @staticmethod
    def _single_column_index(df: WorksheetTable, unique_label: UniqueLabel) -> Iterator[ColumnIndex]:
        yield ColumnIndex(df.columns.get_loc(unique_label))
