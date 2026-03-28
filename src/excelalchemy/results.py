"""Import result models for ExcelAlchemy workflows."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from excelalchemy._primitives.identity import Label
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.i18n.messages import message as msg


def _empty_labels() -> list[Label]:
    return []


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
            raise RuntimeError(msg(MessageKey.IMPORT_RESULT_ONLY_FOR_INVALID_HEADER_VALIDATION))
        return cls(
            result=ValidateResult.HEADER_INVALID,
            is_required_missing=result.is_required_missing,
            missing_primary=result.missing_primary,
            unrecognized=result.unrecognized,
            duplicated=result.duplicated,
            missing_required=result.missing_required,
        )
