"""One-shot import workflow session used by the ExcelAlchemy facade."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from enum import StrEnum
from functools import cached_property

from pydantic import BaseModel

from excelalchemy.codecs.field_codec import SystemReservedFieldCodec
from excelalchemy.config import ImporterConfig
from excelalchemy.diagnostics import runtime_logger
from excelalchemy.errors import ConfigError
from excelalchemy.field_metadata import FieldMetaInfo
from excelalchemy.messages import MessageKey, use_display_locale
from excelalchemy.messages import display_message as dmsg
from excelalchemy.messages import message as msg
from excelalchemy.policies import EVENT_CALLBACK_FAILURE_POLICY, HEADER_HINT_LINE_COUNT, RESULT_WORKBOOK_POLICY
from excelalchemy.primitives.identity import DataUrlStr, RowIndex, UniqueLabel, UrlStr
from excelalchemy.primitives.payloads import FlatRowPayload, ModelRowPayload
from excelalchemy.rendering import ExcelRenderer
from excelalchemy.results import (
    CellErrorMap,
    ImportCompletedEvent,
    ImportFailedEvent,
    ImportHeaderValidatedEvent,
    ImportLifecycleEvent,
    ImportResult,
    ImportRowProcessedEvent,
    ImportStartedEvent,
    RowIssueMap,
    ValidateHeaderResult,
    ValidateResult,
)
from excelalchemy.runtime.executor import ImportExecutor
from excelalchemy.runtime.rows import ImportIssueTracker, RowAggregator
from excelalchemy.schema import ExcelSchemaLayout
from excelalchemy.storage import ExcelStorage
from excelalchemy.worksheet.header import ExcelHeader
from excelalchemy.worksheet.header_parser import ExcelHeaderParser
from excelalchemy.worksheet.header_validator import ExcelHeaderValidator
from excelalchemy.worksheet.table import WorksheetRow, WorksheetTable


class ImportSessionPhase(StrEnum):
    """High-level lifecycle phase for a one-shot import session."""

    INITIALIZED = 'INITIALIZED'
    WORKBOOK_LOADED = 'WORKBOOK_LOADED'
    HEADERS_VALIDATED = 'HEADERS_VALIDATED'
    ROWS_PREPARED = 'ROWS_PREPARED'
    ROWS_EXECUTED = 'ROWS_EXECUTED'
    RESULT_RENDERED = 'RESULT_RENDERED'
    COMPLETED = 'COMPLETED'


@dataclass(slots=True, frozen=True)
class ImportSessionSnapshot:
    """Immutable snapshot of the current session lifecycle state."""

    phase: ImportSessionPhase = ImportSessionPhase.INITIALIZED
    input_excel_name: str | None = None
    output_excel_name: str | None = None
    has_merged_header: bool | None = None
    data_row_count: int = 0
    processed_row_count: int = 0
    success_count: int = 0
    fail_count: int = 0
    rendered_result_workbook: bool = False
    result: ValidateResult | None = None


class ImportSession[
    ContextT,
    ImportCreateModelT: BaseModel,
    ImportUpdateModelT: BaseModel,
]:
    """Keep all single-run import state outside of the long-lived facade.

    This class owns the typed runtime event payloads emitted during one import
    run. Platform docs may describe broader stage labels such as "Rows
    Processed", while the runtime events emitted here keep their current
    concrete names such as ``row_processed``.
    """

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
        self._workbook_loaded = False

        self.issue_tracker = ImportIssueTracker(self.layout, self.import_result_field_meta)
        self.row_aggregator = RowAggregator(self.layout, self.behavior.import_mode)
        self.executor = ImportExecutor(self.config, self.issue_tracker, lambda: self.context)
        self._snapshot = ImportSessionSnapshot()
        self._on_event: Callable[[ImportLifecycleEvent], None] | None = None

    @property
    def cell_error_map(self) -> CellErrorMap:
        return self.issue_tracker.cell_errors

    @property
    def row_error_map(self) -> RowIssueMap:
        return self.issue_tracker.row_errors

    @property
    def snapshot(self) -> ImportSessionSnapshot:
        return self._snapshot

    @cached_property
    def input_excel_has_merged_header(self) -> bool:
        if not self._workbook_loaded:
            raise ConfigError(msg(MessageKey.WORKSHEET_TABLE_NOT_LOADED))
        return self.header_parser.has_merged_header(self.header_table)

    @cached_property
    def input_excel_headers(self) -> list[ExcelHeader]:
        if not self._workbook_loaded:
            raise ConfigError(msg(MessageKey.WORKSHEET_TABLE_NOT_LOADED))
        return self.header_parser.extract(self.header_table)

    @property
    def extra_header_count_on_import(self) -> int:
        for input_excel_label in self.input_excel_headers:
            if input_excel_label.label != input_excel_label.parent_label:
                return 1
        return 0

    async def run(
        self,
        input_excel_name: str,
        output_excel_name: str,
        *,
        on_event: Callable[[ImportLifecycleEvent], None] | None = None,
    ) -> ImportResult:
        self._on_event = on_event
        with use_display_locale(self.locale):
            try:
                self._snapshot = replace(
                    self._snapshot,
                    phase=ImportSessionPhase.INITIALIZED,
                    input_excel_name=input_excel_name,
                    output_excel_name=output_excel_name,
                    rendered_result_workbook=False,
                    result=None,
                    data_row_count=0,
                    processed_row_count=0,
                    success_count=0,
                    fail_count=0,
                )
                self._emit_event(ImportStartedEvent())

                validate_header = self._validate_header(input_excel_name)
                self._emit_event(self._header_validated_event(validate_header))
                if not validate_header.is_valid:
                    header_result = ImportResult.from_validate_header_result(validate_header)
                    if RESULT_WORKBOOK_POLICY.header_invalid_uploads_result_workbook:
                        raise ConfigError('Header-invalid imports must not upload a result workbook.')
                    self._snapshot = replace(
                        self._snapshot,
                        phase=ImportSessionPhase.COMPLETED,
                        has_merged_header=self.input_excel_has_merged_header,
                        result=header_result.result,
                    )
                    self._emit_event(self._completed_event(header_result))
                    return header_result

                self._prepare_rows_for_execution()

                all_success, success_count, fail_count = await self._execute_rows()

                url = None
                if not all_success and RESULT_WORKBOOK_POLICY.data_invalid_uploads_result_workbook:
                    self._add_result_column()
                    content_with_prefix = self._render_import_result_excel()
                    url = self._upload_file(output_excel_name, content_with_prefix)
                    self._snapshot = replace(
                        self._snapshot,
                        phase=ImportSessionPhase.RESULT_RENDERED,
                        rendered_result_workbook=True,
                    )

                import_result = ImportResult(
                    result=(ValidateResult.DATA_INVALID, ValidateResult.SUCCESS)[int(all_success)],
                    url=url,
                    success_count=success_count,
                    fail_count=fail_count,
                )
                self._snapshot = replace(
                    self._snapshot,
                    phase=ImportSessionPhase.COMPLETED,
                    success_count=success_count,
                    fail_count=fail_count,
                    result=import_result.result,
                )
                self._emit_event(self._completed_event(import_result))
                return import_result
            except Exception as error:
                self._emit_event(
                    ImportFailedEvent(
                        error_type=type(error).__name__,
                        error_message=str(error),
                    )
                )
                raise

    def _validate_header(self, input_excel_name: str) -> ValidateHeaderResult:
        self._load_workbook(input_excel_name)
        validate_header = self.header_validator.validate(
            self.input_excel_headers, self.layout, self.behavior.import_mode
        )
        self._snapshot = replace(
            self._snapshot,
            phase=ImportSessionPhase.HEADERS_VALIDATED,
            has_merged_header=self.input_excel_has_merged_header,
        )
        return validate_header

    def _load_workbook(self, input_excel_name: str) -> WorksheetTable:
        if not self._workbook_loaded:
            worksheet_table = self.storage_gateway.read_excel_table(
                input_excel_name,
                skiprows=HEADER_HINT_LINE_COUNT,
                sheet_name=self.schema_options.sheet_name,
            )
            self.worksheet_table = worksheet_table
            self.header_table = worksheet_table.head(2)
            self._workbook_loaded = True
            self._snapshot = replace(self._snapshot, phase=ImportSessionPhase.WORKBOOK_LOADED)
        return self.worksheet_table

    def _prepare_rows_for_execution(self) -> None:
        self.worksheet_table = self.worksheet_table.iloc[1:]
        self._set_columns(self.worksheet_table)
        self.worksheet_table = self.worksheet_table.reset_index(drop=True)
        self._snapshot = replace(
            self._snapshot,
            phase=ImportSessionPhase.ROWS_PREPARED,
            data_row_count=max(0, len(self.worksheet_table) - self.extra_header_count_on_import),
        )

    async def _execute_rows(self) -> tuple[bool, int, int]:
        all_success, success_count, fail_count = True, 0, 0
        processed_row_count = 0
        for table_row_index in range(self.extra_header_count_on_import, len(self.worksheet_table)):
            row = self.worksheet_table.row_at(table_row_index)
            aggregate_data = self._aggregate_data(self._row_payload(row))
            success = await self.executor.execute(RowIndex(table_row_index), aggregate_data, self.worksheet_table)
            processed_row_count += 1
            all_success = all_success and success
            success_count, fail_count = (success_count + 1, fail_count) if success else (success_count, fail_count + 1)
            self._emit_event(
                ImportRowProcessedEvent(
                    processed_row_count=processed_row_count,
                    total_row_count=self._snapshot.data_row_count,
                    success_count=success_count,
                    fail_count=fail_count,
                )
            )

        self._snapshot = replace(
            self._snapshot,
            phase=ImportSessionPhase.ROWS_EXECUTED,
            processed_row_count=processed_row_count,
            success_count=success_count,
            fail_count=fail_count,
        )
        return all_success, success_count, fail_count

    def _set_columns(self, worksheet_table: WorksheetTable) -> WorksheetTable:
        return self.header_parser.apply_columns(
            worksheet_table,
            self.input_excel_headers,
            self.layout.get_output_parent_excel_headers(),
        )

    def _aggregate_data(self, row_data: FlatRowPayload) -> ModelRowPayload:
        return self.row_aggregator.aggregate(row_data)

    @staticmethod
    def _row_payload(row: WorksheetRow) -> FlatRowPayload:
        payload: FlatRowPayload = {}
        for key, value in row.items():
            payload[str(key)] = value
        return payload

    def _render_import_result_excel(self) -> DataUrlStr:
        return self.renderer.render_data(
            self.worksheet_table,
            field_meta_mapping=self.import_result_label_to_field_meta | self.layout.unique_label_to_field_meta,
            has_merged_header=self.input_excel_has_merged_header,
            errors=self.cell_error_map,
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

    def _emit_event(self, event: ImportLifecycleEvent) -> None:
        if self._on_event is None:
            return
        try:
            self._on_event(event)
        except Exception:
            runtime_logger.exception(
                'Import lifecycle event handler raised an exception while processing event %s.',
                event.event,
                extra={'event_callback_failure_policy': EVENT_CALLBACK_FAILURE_POLICY.value},
            )

    @staticmethod
    def _header_validated_event(validate_header: ValidateHeaderResult) -> ImportHeaderValidatedEvent:
        return ImportHeaderValidatedEvent.from_validate_header_result(validate_header)

    def _completed_event(self, import_result: ImportResult) -> ImportCompletedEvent:
        return ImportCompletedEvent.from_import_result(import_result)


def build_import_result_field_meta(*, locale: str) -> list[FieldMetaInfo]:
    field_metas: list[FieldMetaInfo] = []
    for column in RESULT_WORKBOOK_POLICY.column_order:
        field_meta = FieldMetaInfo(label=dmsg(column.label_message_key, locale=locale))
        field_meta.parent_label = field_meta.label
        field_meta.key = field_meta.parent_key = column.key
        field_meta.excel_codec = SystemReservedFieldCodec
        field_metas.append(field_meta)
    return field_metas
