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


def _row_number_for_humans(row_index: RowIndex) -> int:
    return int(row_index) + 1


def _column_number_for_humans(column_index: ColumnIndex) -> int:
    return int(column_index) + 1


@dataclass(slots=True, frozen=True)
class FieldIssueSummary:
    """Field-level issue summary suitable for frontends and dashboards."""

    field_label: Label
    parent_label: Label | None
    unique_label: str
    error_count: int
    row_indices: tuple[RowIndex, ...]
    row_numbers_for_humans: tuple[int, ...]
    codes: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            'field_label': str(self.field_label),
            'parent_label': None if self.parent_label is None else str(self.parent_label),
            'unique_label': self.unique_label,
            'error_count': self.error_count,
            'row_indices': [int(index) for index in self.row_indices],
            'row_numbers_for_humans': list(self.row_numbers_for_humans),
            'codes': list(self.codes),
        }


@dataclass(slots=True, frozen=True)
class RowIssueSummary:
    """Row-level issue summary suitable for frontends and dashboards."""

    row_index: RowIndex
    row_number_for_humans: int
    error_count: int
    codes: tuple[str, ...]
    field_labels: tuple[str, ...]
    unique_labels: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            'row_index': int(self.row_index),
            'row_number_for_humans': self.row_number_for_humans,
            'error_count': self.error_count,
            'codes': list(self.codes),
            'field_labels': list(self.field_labels),
            'unique_labels': list(self.unique_labels),
        }


@dataclass(slots=True, frozen=True)
class CodeIssueSummary:
    """Code-level issue summary suitable for frontends and dashboards."""

    code: str
    error_count: int
    row_indices: tuple[RowIndex, ...]
    row_numbers_for_humans: tuple[int, ...]
    unique_labels: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            'code': self.code,
            'error_count': self.error_count,
            'row_indices': [int(index) for index in self.row_indices],
            'row_numbers_for_humans': list(self.row_numbers_for_humans),
            'unique_labels': list(self.unique_labels),
        }


@dataclass(slots=True, frozen=True)
class CellIssueRecord:
    """Flat cell issue record suitable for API responses and UI rendering."""

    row_index: RowIndex
    column_index: ColumnIndex
    error: ExcelCellError

    def to_dict(self) -> dict[str, object]:
        payload = self.error.to_dict()
        payload['row_index'] = int(self.row_index)
        payload['row_number_for_humans'] = _row_number_for_humans(self.row_index)
        payload['column_index'] = int(self.column_index)
        payload['column_number_for_humans'] = _column_number_for_humans(self.column_index)
        payload['display_message'] = self.error.display_message
        return payload


@dataclass(slots=True, frozen=True)
class RowIssueRecord:
    """Flat row issue record suitable for API responses and UI rendering."""

    row_index: RowIndex
    error: RowIssue

    def to_dict(self) -> dict[str, object]:
        payload = self.error.to_dict()
        payload['row_index'] = int(self.row_index)
        payload['row_number_for_humans'] = _row_number_for_humans(self.row_index)
        payload['display_message'] = self.error.display_message
        if isinstance(self.error, ExcelCellError):
            payload['field_label'] = str(self.error.label)
            payload['parent_label'] = None if self.error.parent_label is None else str(self.error.parent_label)
            payload['unique_label'] = str(self.error.unique_label)
        else:
            payload.setdefault('field_label', None)
            payload.setdefault('parent_label', None)
            payload.setdefault('unique_label', None)
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

    def field_labels(self) -> tuple[str, ...]:
        return tuple(sorted({str(error.label) for error in self.flatten()}))

    def parent_labels(self) -> tuple[str, ...]:
        return tuple(sorted({str(error.parent_label) for error in self.flatten() if error.parent_label is not None}))

    def unique_labels(self) -> tuple[str, ...]:
        return tuple(sorted({str(error.unique_label) for error in self.flatten()}))

    def codes(self) -> tuple[str, ...]:
        return tuple(sorted({error.code for error in self.flatten()}))

    def row_indices(self) -> tuple[RowIndex, ...]:
        return tuple(sorted(self.keys()))

    def row_numbers_for_humans(self) -> tuple[int, ...]:
        return tuple(_row_number_for_humans(row_index) for row_index in self.row_indices())

    def column_indices(self) -> tuple[ColumnIndex, ...]:
        return tuple(sorted({column_index for row in self.values() for column_index in row}))

    def column_numbers_for_humans(self) -> tuple[int, ...]:
        return tuple(_column_number_for_humans(column_index) for column_index in self.column_indices())

    def flatten(self) -> tuple[ExcelCellError, ...]:
        return tuple(error for row in self.values() for errors in row.values() for error in errors)

    def records(self) -> tuple[CellIssueRecord, ...]:
        return tuple(
            CellIssueRecord(row_index=row_index, column_index=column_index, error=error)
            for row_index, row in self.items()
            for column_index, errors in row.items()
            for error in errors
        )

    def summary_by_field(self) -> tuple[FieldIssueSummary, ...]:
        grouped: dict[str, list[CellIssueRecord]] = {}
        for record in self.records():
            grouped.setdefault(str(record.error.unique_label), []).append(record)

        summaries: list[FieldIssueSummary] = []
        for unique_label, records in grouped.items():
            first_error = records[0].error
            row_indices = tuple(sorted({record.row_index for record in records}))
            summaries.append(
                FieldIssueSummary(
                    field_label=first_error.label,
                    parent_label=first_error.parent_label,
                    unique_label=unique_label,
                    error_count=len(records),
                    row_indices=row_indices,
                    row_numbers_for_humans=tuple(_row_number_for_humans(index) for index in row_indices),
                    codes=tuple(sorted({record.error.code for record in records})),
                )
            )
        return tuple(sorted(summaries, key=lambda summary: summary.unique_label))

    def summary_by_row(self) -> tuple[RowIssueSummary, ...]:
        grouped: dict[RowIndex, list[CellIssueRecord]] = {}
        for record in self.records():
            grouped.setdefault(record.row_index, []).append(record)

        summaries: list[RowIssueSummary] = []
        for row_index, records in grouped.items():
            summaries.append(
                RowIssueSummary(
                    row_index=row_index,
                    row_number_for_humans=_row_number_for_humans(row_index),
                    error_count=len(records),
                    codes=tuple(sorted({record.error.code for record in records})),
                    field_labels=tuple(sorted({str(record.error.label) for record in records})),
                    unique_labels=tuple(sorted({str(record.error.unique_label) for record in records})),
                )
            )
        return tuple(sorted(summaries, key=lambda summary: summary.row_index))

    def summary_by_code(self) -> tuple[CodeIssueSummary, ...]:
        grouped: dict[str, list[CellIssueRecord]] = {}
        for record in self.records():
            grouped.setdefault(record.error.code, []).append(record)

        summaries: list[CodeIssueSummary] = []
        for code, records in grouped.items():
            row_indices = tuple(sorted({record.row_index for record in records}))
            summaries.append(
                CodeIssueSummary(
                    code=code,
                    error_count=len(records),
                    row_indices=row_indices,
                    row_numbers_for_humans=tuple(_row_number_for_humans(index) for index in row_indices),
                    unique_labels=tuple(sorted({str(record.error.unique_label) for record in records})),
                )
            )
        return tuple(sorted(summaries, key=lambda summary: summary.code))

    def grouped_messages_by_field(self) -> dict[str, tuple[str, ...]]:
        return {
            summary.unique_label: tuple(
                record.error.display_message
                for record in self.records()
                if str(record.error.unique_label) == summary.unique_label
            )
            for summary in self.summary_by_field()
        }

    def grouped_messages_by_row(self) -> dict[int, tuple[str, ...]]:
        return {
            int(summary.row_index): tuple(
                record.error.display_message for record in self.records() if record.row_index == summary.row_index
            )
            for summary in self.summary_by_row()
        }

    def grouped_messages_by_code(self) -> dict[str, tuple[str, ...]]:
        return {
            summary.code: tuple(
                record.error.display_message for record in self.records() if record.error.code == summary.code
            )
            for summary in self.summary_by_code()
        }

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
            'facets': {
                'field_labels': list(self.field_labels()),
                'parent_labels': list(self.parent_labels()),
                'unique_labels': list(self.unique_labels()),
                'codes': list(self.codes()),
                'row_numbers_for_humans': list(self.row_numbers_for_humans()),
                'column_numbers_for_humans': list(self.column_numbers_for_humans()),
            },
            'grouped': {
                'messages_by_field': {
                    key: list(messages) for key, messages in self.grouped_messages_by_field().items()
                },
                'messages_by_row': {
                    str(row_index): list(messages) for row_index, messages in self.grouped_messages_by_row().items()
                },
                'messages_by_code': {key: list(messages) for key, messages in self.grouped_messages_by_code().items()},
            },
            'summary': {
                'by_field': [summary.to_dict() for summary in self.summary_by_field()],
                'by_row': [summary.to_dict() for summary in self.summary_by_row()],
                'by_code': [summary.to_dict() for summary in self.summary_by_code()],
            },
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

    def field_labels(self) -> tuple[str, ...]:
        return tuple(sorted({str(error.label) for error in self.flatten() if isinstance(error, ExcelCellError)}))

    def parent_labels(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    str(error.parent_label)
                    for error in self.flatten()
                    if isinstance(error, ExcelCellError) and error.parent_label is not None
                }
            )
        )

    def unique_labels(self) -> tuple[str, ...]:
        return tuple(sorted({str(error.unique_label) for error in self.flatten() if isinstance(error, ExcelCellError)}))

    def codes(self) -> tuple[str, ...]:
        return tuple(sorted({error.code for error in self.flatten()}))

    def row_indices(self) -> tuple[RowIndex, ...]:
        return tuple(sorted(self.keys()))

    def row_numbers_for_humans(self) -> tuple[int, ...]:
        return tuple(_row_number_for_humans(row_index) for row_index in self.row_indices())

    def numbered_messages_for_row(self, row_index: RowIndex | int) -> tuple[str, ...]:
        return self.numbered_messages(self.at(row_index))

    def flatten(self) -> tuple[RowIssue, ...]:
        return tuple(error for errors in self.values() for error in errors)

    def records(self) -> tuple[RowIssueRecord, ...]:
        return tuple(
            RowIssueRecord(row_index=row_index, error=error) for row_index, errors in self.items() for error in errors
        )

    def summary_by_row(self) -> tuple[RowIssueSummary, ...]:
        summaries: list[RowIssueSummary] = []
        for row_index, errors in self.items():
            cell_errors = [error for error in errors if isinstance(error, ExcelCellError)]
            summaries.append(
                RowIssueSummary(
                    row_index=row_index,
                    row_number_for_humans=_row_number_for_humans(row_index),
                    error_count=len(errors),
                    codes=tuple(sorted({error.code for error in errors})),
                    field_labels=tuple(sorted({str(error.label) for error in cell_errors})),
                    unique_labels=tuple(sorted({str(error.unique_label) for error in cell_errors})),
                )
            )
        return tuple(sorted(summaries, key=lambda summary: summary.row_index))

    def summary_by_code(self) -> tuple[CodeIssueSummary, ...]:
        grouped: dict[str, list[RowIssueRecord]] = {}
        for record in self.records():
            grouped.setdefault(record.error.code, []).append(record)

        summaries: list[CodeIssueSummary] = []
        for code, records in grouped.items():
            row_indices = tuple(sorted({record.row_index for record in records}))
            unique_labels = tuple(
                sorted(
                    {str(record.error.unique_label) for record in records if isinstance(record.error, ExcelCellError)}
                )
            )
            summaries.append(
                CodeIssueSummary(
                    code=code,
                    error_count=len(records),
                    row_indices=row_indices,
                    row_numbers_for_humans=tuple(_row_number_for_humans(index) for index in row_indices),
                    unique_labels=unique_labels,
                )
            )
        return tuple(sorted(summaries, key=lambda summary: summary.code))

    def grouped_messages_by_row(self) -> dict[int, tuple[str, ...]]:
        return {
            int(summary.row_index): tuple(
                record.error.display_message for record in self.records() if record.row_index == summary.row_index
            )
            for summary in self.summary_by_row()
        }

    def grouped_messages_by_code(self) -> dict[str, tuple[str, ...]]:
        return {
            summary.code: tuple(
                record.error.display_message for record in self.records() if record.error.code == summary.code
            )
            for summary in self.summary_by_code()
        }

    def to_dict(self) -> dict[int, list[dict[str, object]]]:
        return {int(row_index): [error.to_dict() for error in errors] for row_index, errors in self.items()}

    def to_api_payload(self) -> dict[str, object]:
        return {
            'error_count': self.error_count,
            'items': [record.to_dict() for record in self.records()],
            'by_row': self.to_dict(),
            'facets': {
                'field_labels': list(self.field_labels()),
                'parent_labels': list(self.parent_labels()),
                'unique_labels': list(self.unique_labels()),
                'codes': list(self.codes()),
                'row_numbers_for_humans': list(self.row_numbers_for_humans()),
            },
            'grouped': {
                'messages_by_row': {
                    str(row_index): list(messages) for row_index, messages in self.grouped_messages_by_row().items()
                },
                'messages_by_code': {key: list(messages) for key, messages in self.grouped_messages_by_code().items()},
            },
            'summary': {
                'by_row': [summary.to_dict() for summary in self.summary_by_row()],
                'by_code': [summary.to_dict() for summary in self.summary_by_code()],
            },
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

    @property
    def is_success(self) -> bool:
        return self.result == ValidateResult.SUCCESS

    @property
    def is_header_invalid(self) -> bool:
        return self.result == ValidateResult.HEADER_INVALID

    @property
    def is_data_invalid(self) -> bool:
        return self.result == ValidateResult.DATA_INVALID

    def to_api_payload(self) -> dict[str, object]:
        return {
            'result': self.result.value,
            'is_success': self.is_success,
            'is_header_invalid': self.is_header_invalid,
            'is_data_invalid': self.is_data_invalid,
            'summary': {
                'success_count': self.success_count,
                'fail_count': self.fail_count,
                'result_workbook_url': self.url,
            },
            'header_issues': {
                'is_required_missing': self.is_required_missing,
                'missing_required': [str(label) for label in self.missing_required],
                'missing_primary': [str(label) for label in self.missing_primary],
                'unrecognized': [str(label) for label in self.unrecognized],
                'duplicated': [str(label) for label in self.duplicated],
            },
        }

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
