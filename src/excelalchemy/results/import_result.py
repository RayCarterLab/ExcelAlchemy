"""High-level import result models."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from excelalchemy.errors import ProgrammaticError
from excelalchemy.messages import MessageKey
from excelalchemy.messages import message as msg
from excelalchemy.primitives.identity import Label
from excelalchemy.results.preflight import ValidateHeaderResult, empty_labels


class ValidateResult(StrEnum):
    """High-level import result type."""

    HEADER_INVALID = 'HEADER_INVALID'
    DATA_INVALID = 'DATA_INVALID'
    SUCCESS = 'SUCCESS'


class ImportResult(BaseModel):
    """Structured result returned from an import run."""

    # fmt: off
    model_config = ConfigDict(extra='forbid')

    result: ValidateResult = Field(description='Overall import result.')

    is_required_missing: bool = Field(default=False, description='Whether required headers are missing.')
    missing_required: list[Label] = Field(default_factory=empty_labels, description='Required headers missing from the workbook.')
    missing_primary: list[Label] = Field(default_factory=empty_labels, description='Primary-key headers missing from the workbook.')
    unrecognized: list[Label] = Field(default_factory=empty_labels, description='Headers present in the workbook but unknown to the schema.')
    duplicated: list[Label] = Field(default_factory=empty_labels, description='Headers that appear more than once in the workbook.')

    url: str | None = Field(default=None, description='Download URL for the import result workbook when one is produced.')
    success_count: int = Field(default=0, description='Number of rows imported successfully.')
    fail_count: int = Field(default=0, description='Number of rows that failed to import.')
    # fmt: on

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
