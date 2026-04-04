"""Import result models for ExcelAlchemy workflows."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from excelalchemy._primitives.identity import ColumnIndex, Label, RowIndex
from excelalchemy.exceptions import ExcelCellError, ExcelRowError, ProgrammaticError
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.i18n.messages import message as msg


def _empty_labels() -> list[Label]:
    return []


type RowIssue = ExcelRowError | ExcelCellError


@dataclass(slots=True, frozen=True)
class CellIssueRecord:
    """Flat cell issue record suitable for API responses and UI rendering."""

    row_index: RowIndex
    column_index: ColumnIndex
    error: ExcelCellError

    def to_dict(self) -> dict[str, object]:
        payload = self.error.to_dict()
        payload['row_index'] = int(self.row_index)
        payload['column_index'] = int(self.column_index)
        payload['display_message'] = str(self.error)
        return payload


@dataclass(slots=True, frozen=True)
class RowIssueRecord:
    """Flat row issue record suitable for API responses and UI rendering."""

    row_index: RowIndex
    error: RowIssue

    def to_dict(self) -> dict[str, object]:
        payload = self.error.to_dict()
        payload['row_index'] = int(self.row_index)
        payload['display_message'] = str(self.error)
        return payload


class CellErrorMap(dict[RowIndex, dict[ColumnIndex, list[ExcelCellError]]]):
    """Workbook-coordinate cell error mapping with convenience accessors."""

    def add(self, row_index: RowIndex | int, column_index: ColumnIndex | int, error: ExcelCellError) -> None:
        self.setdefault(RowIndex(row_index), {}).setdefault(ColumnIndex(column_index), []).append(error)

    def at(self, row_index: RowIndex | int, column_index: ColumnIndex | int) -> tuple[ExcelCellError, ...]:
        row = self.get(RowIndex(row_index), {})
        return tuple(row.get(ColumnIndex(column_index), ()))

    def for_row(self, row_index: RowIndex | int) -> dict[ColumnIndex, tuple[ExcelCellError, ...]]:
        row = self.get(RowIndex(row_index), {})
        return {column_index: tuple(errors) for column_index, errors in row.items()}

    def messages_at(self, row_index: RowIndex | int, column_index: ColumnIndex | int) -> tuple[str, ...]:
        return tuple(str(error) for error in self.at(row_index, column_index))

    def flatten(self) -> tuple[ExcelCellError, ...]:
        return tuple(error for row in self.values() for errors in row.values() for error in errors)

    def records(self) -> tuple[CellIssueRecord, ...]:
        return tuple(
            CellIssueRecord(row_index=row_index, column_index=column_index, error=error)
            for row_index, row in self.items()
            for column_index, errors in row.items()
            for error in errors
        )

    def to_dict(self) -> dict[int, dict[int, list[dict[str, object]]]]:
        return {
            int(row_index): {
                int(column_index): [error.to_dict() for error in errors] for column_index, errors in row.items()
            }
            for row_index, row in self.items()
        }

    def to_api_payload(self) -> dict[str, object]:
        return {
            'error_count': self.error_count,
            'items': [record.to_dict() for record in self.records()],
            'by_row': self.to_dict(),
        }

    @property
    def has_errors(self) -> bool:
        return bool(self)

    @property
    def error_count(self) -> int:
        return len(self.flatten())


class RowIssueMap(dict[RowIndex, list[RowIssue]]):
    """Workbook-coordinate row issue mapping with convenience accessors."""

    def add(self, row_index: RowIndex | int, error: RowIssue) -> None:
        self.setdefault(RowIndex(row_index), []).append(error)

    def add_many(self, row_index: RowIndex | int, errors: Iterable[RowIssue]) -> None:
        self.setdefault(RowIndex(row_index), []).extend(errors)

    def at(self, row_index: RowIndex | int) -> tuple[RowIssue, ...]:
        return tuple(self.get(RowIndex(row_index), ()))

    def messages_for_row(self, row_index: RowIndex | int) -> tuple[str, ...]:
        return tuple(str(error) for error in self.at(row_index))

    def numbered_messages_for_row(self, row_index: RowIndex | int) -> tuple[str, ...]:
        return self.numbered_messages(self.at(row_index))

    def flatten(self) -> tuple[RowIssue, ...]:
        return tuple(error for errors in self.values() for error in errors)

    def records(self) -> tuple[RowIssueRecord, ...]:
        return tuple(
            RowIssueRecord(row_index=row_index, error=error) for row_index, errors in self.items() for error in errors
        )

    def to_dict(self) -> dict[int, list[dict[str, object]]]:
        return {int(row_index): [error.to_dict() for error in errors] for row_index, errors in self.items()}

    def to_api_payload(self) -> dict[str, object]:
        return {
            'error_count': self.error_count,
            'items': [record.to_dict() for record in self.records()],
            'by_row': self.to_dict(),
        }

    @staticmethod
    def numbered_messages(errors: Iterable[RowIssue]) -> tuple[str, ...]:
        return tuple(f'{index}、{error!s}' for index, error in enumerate(errors, start=1))

    @property
    def has_errors(self) -> bool:
        return bool(self)

    @property
    def error_count(self) -> int:
        return len(self.flatten())


class ValidateRowResult(StrEnum):
    """Per-row validation status."""

    SUCCESS = 'SUCCESS'
    FAIL = 'FAIL'

    def __str__(self) -> str:
        if self is ValidateRowResult.SUCCESS:
            return dmsg(MessageKey.VALIDATE_ROW_SUCCESS)
        return dmsg(MessageKey.VALIDATE_ROW_FAIL)


class ValidateHeaderResult(BaseModel):
    """Header validation result."""

    missing_required: list[Label] = Field(description='Required headers missing from the workbook.')
    missing_primary: list[Label] = Field(description='Primary-key headers missing from the workbook.')
    unrecognized: list[Label] = Field(description='Headers present in the workbook but unknown to the schema.')
    duplicated: list[Label] = Field(description='Headers that appear more than once in the workbook.')
    is_valid: bool = Field(default=True, description='Whether header validation succeeded.')

    @property
    def is_required_missing(self) -> bool:
        """Return whether any required headers are missing."""
        return bool(self.missing_required)


class ValidateResult(StrEnum):
    """High-level import result type."""

    HEADER_INVALID = 'HEADER_INVALID'
    DATA_INVALID = 'DATA_INVALID'
    SUCCESS = 'SUCCESS'


class ImportResult(BaseModel):
    """Structured result returned from an import run."""

    model_config = ConfigDict(extra='allow')

    result: ValidateResult = Field(description='Overall import result.')

    is_required_missing: bool = Field(default=False, description='Whether required headers are missing.')
    missing_required: list[Label] = Field(
        default_factory=_empty_labels, description='Required headers missing from the workbook.'
    )
    missing_primary: list[Label] = Field(
        default_factory=_empty_labels, description='Primary-key headers missing from the workbook.'
    )
    unrecognized: list[Label] = Field(
        default_factory=_empty_labels, description='Headers present in the workbook but unknown to the schema.'
    )
    duplicated: list[Label] = Field(
        default_factory=_empty_labels, description='Headers that appear more than once in the workbook.'
    )

    url: str | None = Field(
        default=None, description='Download URL for the import result workbook when one is produced.'
    )
    success_count: int = Field(default=0, description='Number of rows imported successfully.')
    fail_count: int = Field(default=0, description='Number of rows that failed to import.')

    @classmethod
    def from_validate_header_result(cls, result: ValidateHeaderResult) -> 'ImportResult':
        """Build an import result from a failed header-validation result."""
        if result.is_valid:
            raise ProgrammaticError(
                msg(MessageKey.IMPORT_RESULT_ONLY_FOR_INVALID_HEADER_VALIDATION),
                message_key=MessageKey.IMPORT_RESULT_ONLY_FOR_INVALID_HEADER_VALIDATION,
            )
        return cls(
            result=ValidateResult.HEADER_INVALID,
            is_required_missing=result.is_required_missing,
            missing_primary=result.missing_primary,
            unrecognized=result.unrecognized,
            duplicated=result.duplicated,
            missing_required=result.missing_required,
        )
