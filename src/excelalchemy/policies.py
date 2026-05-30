"""Named runtime policies shared across ExcelAlchemy internals."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from excelalchemy.messages import MessageKey
from excelalchemy.primitives.identity import Key

if TYPE_CHECKING:
    from excelalchemy.config import ImportMode


class MissingValueImportAction(StrEnum):
    """How an empty workbook cell is represented in the importer payload."""

    OMIT_FIELD = 'omit_field'
    USE_NONE = 'use_none'


@dataclass(frozen=True, slots=True)
class WorkbookIdentityPolicy:
    """Separators used when ExcelAlchemy builds stable workbook identities."""

    unique_label_separator: str = '·'
    unique_key_separator: str = '·'


@dataclass(frozen=True, slots=True)
class PayloadPathPolicy:
    """Separator used when flattening nested Python payload keys."""

    nested_key_separator: str = '·'


@dataclass(frozen=True, slots=True)
class WorkbookLayoutPolicy:
    """Workbook row and coordinate policies used by render and import code."""

    openpyxl_index_start: int = 1
    header_hint_row_index: int = 1
    header_hint_column_index: int = 1
    header_hint_line_count: int = 1
    simple_header_row_count: int = 1
    merged_header_row_count: int = 2


@dataclass(frozen=True, slots=True)
class ResultColumnSpec:
    """Workbook result-column identity and label policy."""

    key: Key
    label_message_key: MessageKey


@dataclass(frozen=True, slots=True)
class ResultWorkbookPolicy:
    """Policies for import result workbook creation and column order."""

    result_column: ResultColumnSpec = field(
        default_factory=lambda: ResultColumnSpec(Key('__result__'), MessageKey.RESULT_COLUMN_LABEL)
    )
    reason_column: ResultColumnSpec = field(
        default_factory=lambda: ResultColumnSpec(Key('__reason__'), MessageKey.REASON_COLUMN_LABEL)
    )
    header_invalid_uploads_result_workbook: bool = False
    data_invalid_uploads_result_workbook: bool = True

    @property
    def column_order(self) -> tuple[ResultColumnSpec, ResultColumnSpec]:
        return (self.result_column, self.reason_column)


class EventCallbackFailurePolicy(StrEnum):
    """Import lifecycle callback failure handling policies."""

    LOG_AND_CONTINUE = 'log_and_continue'


@dataclass(frozen=True, slots=True)
class MissingValueImportPolicy:
    """Import-mode-specific handling of empty worksheet cells."""

    create: MissingValueImportAction = MissingValueImportAction.OMIT_FIELD
    update: MissingValueImportAction = MissingValueImportAction.USE_NONE
    create_or_update: MissingValueImportAction = MissingValueImportAction.USE_NONE

    def action_for_import_mode(self, import_mode: ImportMode) -> MissingValueImportAction:
        from excelalchemy.config import ImportMode

        match import_mode:
            case ImportMode.CREATE:
                return self.create
            case ImportMode.UPDATE:
                return self.update
            case ImportMode.CREATE_OR_UPDATE:
                return self.create_or_update


WORKBOOK_IDENTITY_POLICY = WorkbookIdentityPolicy()
PAYLOAD_PATH_POLICY = PayloadPathPolicy()
WORKBOOK_LAYOUT_POLICY = WorkbookLayoutPolicy()
RESULT_WORKBOOK_POLICY = ResultWorkbookPolicy()
EVENT_CALLBACK_FAILURE_POLICY = EventCallbackFailurePolicy.LOG_AND_CONTINUE
MISSING_VALUE_IMPORT_POLICY = MissingValueImportPolicy()

WORKBOOK_UNIQUE_LABEL_SEPARATOR = WORKBOOK_IDENTITY_POLICY.unique_label_separator
WORKBOOK_UNIQUE_KEY_SEPARATOR = WORKBOOK_IDENTITY_POLICY.unique_key_separator
PAYLOAD_PATH_SEPARATOR = PAYLOAD_PATH_POLICY.nested_key_separator
OPENPYXL_EXCEL_INDEX_START_AT = WORKBOOK_LAYOUT_POLICY.openpyxl_index_start
HEADER_HINT_ROW_INDEX = WORKBOOK_LAYOUT_POLICY.header_hint_row_index
HEADER_HINT_COL_INDEX = WORKBOOK_LAYOUT_POLICY.header_hint_column_index
HEADER_HINT_LINE_COUNT = WORKBOOK_LAYOUT_POLICY.header_hint_line_count
SIMPLE_HEADER_ROW_COUNT = WORKBOOK_LAYOUT_POLICY.simple_header_row_count
MERGED_HEADER_ROW_COUNT = WORKBOOK_LAYOUT_POLICY.merged_header_row_count

__all__ = [
    'EVENT_CALLBACK_FAILURE_POLICY',
    'HEADER_HINT_COL_INDEX',
    'HEADER_HINT_LINE_COUNT',
    'HEADER_HINT_ROW_INDEX',
    'MERGED_HEADER_ROW_COUNT',
    'MISSING_VALUE_IMPORT_POLICY',
    'OPENPYXL_EXCEL_INDEX_START_AT',
    'PAYLOAD_PATH_POLICY',
    'PAYLOAD_PATH_SEPARATOR',
    'RESULT_WORKBOOK_POLICY',
    'SIMPLE_HEADER_ROW_COUNT',
    'WORKBOOK_IDENTITY_POLICY',
    'WORKBOOK_LAYOUT_POLICY',
    'WORKBOOK_UNIQUE_KEY_SEPARATOR',
    'WORKBOOK_UNIQUE_LABEL_SEPARATOR',
    'EventCallbackFailurePolicy',
    'MissingValueImportAction',
    'MissingValueImportPolicy',
    'PayloadPathPolicy',
    'ResultColumnSpec',
    'ResultWorkbookPolicy',
    'WorkbookIdentityPolicy',
    'WorkbookLayoutPolicy',
]
