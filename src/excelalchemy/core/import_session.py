"""One-shot import workflow session used by the ExcelAlchemy facade."""

from __future__ import annotations

from functools import cached_property
from typing import cast

from pydantic import BaseModel

from excelalchemy._primitives.constants import REASON_COLUMN_KEY, RESULT_COLUMN_KEY
from excelalchemy._primitives.header_models import ExcelHeader
from excelalchemy._primitives.identity import DataUrlStr, RowIndex, UniqueLabel, UrlStr
from excelalchemy._primitives.payloads import FlatRowPayload, ModelRowPayload
from excelalchemy.codecs.base import SystemReserved
from excelalchemy.config import ImporterConfig
from excelalchemy.core.executor import ImportExecutor
from excelalchemy.core.headers import ExcelHeaderParser, ExcelHeaderValidator
from excelalchemy.core.rendering import ExcelRenderer
from excelalchemy.core.rows import ImportIssueTracker, RowAggregator
from excelalchemy.core.schema import ExcelSchemaLayout
from excelalchemy.core.storage_protocol import ExcelStorage
from excelalchemy.core.table import WorksheetTable
from excelalchemy.exceptions import ConfigError
from excelalchemy.i18n.messages import MessageKey, use_display_locale
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.i18n.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo
from excelalchemy.results import ImportResult, ValidateHeaderResult, ValidateResult

HEADER_HINT_LINE_COUNT = 1


class ImportSession[
    ContextT,
    ImportCreateModelT: BaseModel,
    ImportUpdateModelT: BaseModel,
]:
    """Keep all single-run import state outside of the long-lived facade."""

    def __init__(
        self,
        *,
        config: ImporterConfig[ContextT, ImportCreateModelT, ImportUpdateModelT],
        layout: ExcelSchemaLayout,
        storage_gateway: ExcelStorage,
        header_parser: ExcelHeaderParser,
        header_validator: ExcelHeaderValidator,
        renderer: ExcelRenderer,
        import_result_field_meta: list[FieldMetaInfo],
        import_result_label_to_field_meta: dict[UniqueLabel, FieldMetaInfo],
        locale: str,
        context: ContextT | None,
    ) -> None:
        self.config = config
        self.layout = layout
        self.storage_gateway = storage_gateway
        self.header_parser = header_parser
        self.header_validator = header_validator
        self.renderer = renderer
        self.import_result_field_meta = import_result_field_meta
        self.import_result_label_to_field_meta = import_result_label_to_field_meta
        self.locale = locale
        self.context = context
        self.schema_options = config.schema_options
        self.behavior = config.behavior

        self.worksheet_table = WorksheetTable()
        self.header_table = WorksheetTable()
        self._state_df_has_been_loaded = False

        self.issue_tracker = ImportIssueTracker(self.layout, self.import_result_field_meta)
        self.row_aggregator = RowAggregator(self.layout, self.behavior.import_mode)
        self.executor = ImportExecutor(self.config, self.issue_tracker, lambda: self.context)

    @property
    def cell_errors(self):
        return self.issue_tracker.cell_errors

    @property
    def row_errors(self):
        return self.issue_tracker.row_errors

    @cached_property
    def input_excel_has_merged_header(self) -> bool:
        if not self._state_df_has_been_loaded:
            raise ConfigError(msg(MessageKey.WORKSHEET_TABLE_NOT_LOADED))
        return self.header_parser.has_merged_header(self.header_table)

    @cached_property
    def input_excel_headers(self) -> list[ExcelHeader]:
        if not self._state_df_has_been_loaded:
            raise ConfigError(msg(MessageKey.WORKSHEET_TABLE_NOT_LOADED))
        return self.header_parser.extract(self.header_table)

    @property
    def extra_header_count_on_import(self) -> int:
        for input_excel_label in self.input_excel_headers:
            if input_excel_label.label != input_excel_label.parent_label:
                return 1
        return 0

    async def run(self, input_excel_name: str, output_excel_name: str) -> ImportResult:
        with use_display_locale(self.locale):
            validate_header = self._validate_header(input_excel_name)
            if not validate_header.is_valid:
                return ImportResult.from_validate_header_result(validate_header)

            self.worksheet_table = self.worksheet_table.iloc[1:]
            self._set_columns(self.worksheet_table)
            self.worksheet_table = self.worksheet_table.reset_index(drop=True)

            all_success, success_count, fail_count = True, 0, 0
            for table_row_index in range(self.extra_header_count_on_import, len(self.worksheet_table)):
                row = self.worksheet_table.row_at(table_row_index)
                aggregate_data = self._aggregate_data(cast(FlatRowPayload, row.to_dict()))
                success = await self.executor.execute(RowIndex(table_row_index), aggregate_data, self.worksheet_table)
                all_success = all_success and success
                success_count, fail_count = (
                    (success_count + 1, fail_count) if success else (success_count, fail_count + 1)
                )

            url = None
            if not all_success:
                self._add_result_column()
                content_with_prefix = self._render_import_result_excel()
                url = self._upload_file(output_excel_name, content_with_prefix)

            return ImportResult(
                result=(ValidateResult.DATA_INVALID, ValidateResult.SUCCESS)[int(all_success)],
                url=url,
                success_count=success_count,
                fail_count=fail_count,
            )

    def _validate_header(self, input_excel_name: str) -> ValidateHeaderResult:
        self._read_dataframe(input_excel_name)
        return self.header_validator.validate(self.input_excel_headers, self.layout, self.behavior.import_mode)

    def _read_dataframe(self, input_excel_name: str) -> WorksheetTable:
        if not self._state_df_has_been_loaded:
            worksheet_table = self.storage_gateway.read_excel_table(
                input_excel_name,
                skiprows=HEADER_HINT_LINE_COUNT,
                sheet_name=self.schema_options.sheet_name,
            )
            self.worksheet_table = worksheet_table
            self.header_table = worksheet_table.head(2)
            self._state_df_has_been_loaded = True
        return self.worksheet_table

    def _set_columns(self, worksheet_table: WorksheetTable) -> WorksheetTable:
        return self.header_parser.apply_columns(
            worksheet_table,
            self.input_excel_headers,
            self.layout.get_output_parent_excel_headers(),
        )

    def _aggregate_data(self, row_data: FlatRowPayload) -> ModelRowPayload:
        return self.row_aggregator.aggregate(row_data)

    def _render_import_result_excel(self) -> DataUrlStr:
        return self.renderer.render_data(
            self.worksheet_table,
            field_meta_mapping=self.import_result_label_to_field_meta | self.layout.unique_label_to_field_meta,
            has_merged_header=self.input_excel_has_merged_header,
            errors=self.cell_errors,
        )

    def _upload_file(self, output_name: str, content_with_prefix: DataUrlStr) -> UrlStr:
        return self.storage_gateway.upload_excel(output_name, content_with_prefix)

    def _add_result_column(self) -> None:
        self.issue_tracker.add_result_columns(
            self.worksheet_table,
            result_unique_label=self.import_result_field_meta[0].unique_label,
            reason_unique_label=self.import_result_field_meta[1].unique_label,
            extra_header_count_on_import=self.extra_header_count_on_import,
        )

    @property
    def df(self) -> WorksheetTable:
        """Backward-compatible alias for worksheet_table."""
        return self.worksheet_table

    @df.setter
    def df(self, value: WorksheetTable) -> None:
        self.worksheet_table = value

    @property
    def header_df(self) -> WorksheetTable:
        """Backward-compatible alias for header_table."""
        return self.header_table

    @header_df.setter
    def header_df(self, value: WorksheetTable) -> None:
        self.header_table = value


def build_import_result_field_meta(*, locale: str) -> list[FieldMetaInfo]:
    result_column = FieldMetaInfo(label=dmsg(MessageKey.RESULT_COLUMN_LABEL, locale=locale))
    result_column.parent_label = result_column.label
    result_column.key = result_column.parent_key = RESULT_COLUMN_KEY
    result_column.excel_codec = SystemReserved

    reason_column = FieldMetaInfo(label=dmsg(MessageKey.REASON_COLUMN_LABEL, locale=locale))
    reason_column.parent_label = reason_column.label
    reason_column.key = reason_column.parent_key = REASON_COLUMN_KEY
    reason_column.excel_codec = SystemReserved

    return [result_column, reason_column]
