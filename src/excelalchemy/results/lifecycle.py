"""Typed import lifecycle event payloads."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from excelalchemy.messages import MessageKey
from excelalchemy.messages import display_message as dmsg
from excelalchemy.results.import_result import ImportResult, ValidateResult
from excelalchemy.results.preflight import ValidateHeaderResult


class ValidateRowResult(StrEnum):
    """Per-row validation status."""

    SUCCESS = 'SUCCESS'
    FAIL = 'FAIL'

    def __str__(self) -> str:
        if self is ValidateRowResult.SUCCESS:
            return dmsg(MessageKey.VALIDATE_ROW_SUCCESS)
        return dmsg(MessageKey.VALIDATE_ROW_FAIL)


class ImportLifecycleEventName(StrEnum):
    """Typed import lifecycle event names."""

    STARTED = 'started'
    HEADER_VALIDATED = 'header_validated'
    ROW_PROCESSED = 'row_processed'
    COMPLETED = 'completed'
    FAILED = 'failed'


class ImportLifecycleEvent(BaseModel):
    """Base class for typed import lifecycle event payloads."""

    model_config = ConfigDict(frozen=True)

    event: ImportLifecycleEventName


class ImportStartedEvent(ImportLifecycleEvent):
    """Import runtime started processing a workbook."""

    event: ImportLifecycleEventName = ImportLifecycleEventName.STARTED


class ImportHeaderValidatedEvent(ImportLifecycleEvent):
    """Import runtime finished validating workbook headers."""

    event: ImportLifecycleEventName = ImportLifecycleEventName.HEADER_VALIDATED
    is_valid: bool
    missing_required: list[str] | None = None
    missing_primary: list[str] | None = None
    unrecognized: list[str] | None = None
    duplicated: list[str] | None = None

    @classmethod
    def from_validate_header_result(cls, result: ValidateHeaderResult) -> 'ImportHeaderValidatedEvent':
        if result.is_valid:
            return cls(is_valid=True)
        return cls(
            is_valid=False,
            missing_required=[str(label) for label in result.missing_required],
            missing_primary=[str(label) for label in result.missing_primary],
            unrecognized=[str(label) for label in result.unrecognized],
            duplicated=[str(label) for label in result.duplicated],
        )


class ImportRowProcessedEvent(ImportLifecycleEvent):
    """Import runtime finished processing one workbook data row."""

    event: ImportLifecycleEventName = ImportLifecycleEventName.ROW_PROCESSED
    processed_row_count: int
    total_row_count: int
    success_count: int
    fail_count: int


class ImportCompletedEvent(ImportLifecycleEvent):
    """Import runtime completed with a structured result."""

    event: ImportLifecycleEventName = ImportLifecycleEventName.COMPLETED
    result: ValidateResult
    success_count: int
    fail_count: int
    url: str | None = None

    @classmethod
    def from_import_result(cls, result: 'ImportResult') -> 'ImportCompletedEvent':
        return cls(
            result=result.result,
            success_count=result.success_count,
            fail_count=result.fail_count,
            url=result.url,
        )


class ImportFailedEvent(ImportLifecycleEvent):
    """Import runtime failed before returning an ImportResult."""

    event: ImportLifecycleEventName = ImportLifecycleEventName.FAILED
    error_type: str
    error_message: str
