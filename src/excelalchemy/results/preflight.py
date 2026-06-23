"""Import header validation and lightweight preflight results."""

from enum import StrEnum

from pydantic import BaseModel, Field

from excelalchemy.primitives.identity import Label


def empty_labels() -> list[Label]:
    return []


class ValidateHeaderResult(BaseModel):
    """Header validation result."""

    # fmt: off
    missing_required: list[Label] = Field(description='Required headers missing from the workbook.')
    missing_primary: list[Label] = Field(description='Primary-key headers missing from the workbook.')
    unrecognized: list[Label] = Field(description='Headers present in the workbook but unknown to the schema.')
    duplicated: list[Label] = Field(description='Headers that appear more than once in the workbook.')
    is_valid: bool = Field(default=True, description='Whether header validation succeeded.')
    # fmt: on

    @property
    def is_required_missing(self) -> bool:
        """Return whether any required headers are missing."""
        return bool(self.missing_required)


class ImportPreflightStatus(StrEnum):
    """High-level preflight result type."""

    VALID = 'VALID'
    HEADER_INVALID = 'HEADER_INVALID'
    SHEET_MISSING = 'SHEET_MISSING'
    STRUCTURE_INVALID = 'STRUCTURE_INVALID'


class ImportPreflightResult(BaseModel):
    """Structured result returned from lightweight import preflight."""

    # fmt: off
    status: ImportPreflightStatus = Field(description='Overall preflight result.')
    sheet_name: str = Field(description='Configured worksheet name used for preflight.')
    sheet_exists: bool = Field(description='Whether the configured worksheet was found.')
    has_merged_header: bool | None = Field(default=None, description='Whether the workbook uses a merged two-row header when the header block was readable.')
    estimated_row_count: int = Field(default=0, description='Estimated number of data rows for a later import run.')
    structural_issue_codes: list[str] = Field(default_factory=list, description='Stable structural issue codes emitted for non-header preflight failures.')

    is_required_missing: bool = Field(default=False, description='Whether required headers are missing.')
    missing_required: list[Label] = Field(default_factory=empty_labels, description='Required headers missing from the workbook.')
    missing_primary: list[Label] = Field(default_factory=empty_labels, description='Primary-key headers missing from the workbook.')
    unrecognized: list[Label] = Field(default_factory=empty_labels, description='Headers present in the workbook but unknown to the schema.')
    duplicated: list[Label] = Field(default_factory=empty_labels, description='Headers that appear more than once in the workbook.')
    # fmt: on

    @property
    def is_valid(self) -> bool:
        return self.status == ImportPreflightStatus.VALID

    @property
    def is_header_invalid(self) -> bool:
        return self.status == ImportPreflightStatus.HEADER_INVALID

    @property
    def is_sheet_missing(self) -> bool:
        return self.status == ImportPreflightStatus.SHEET_MISSING

    @property
    def is_structure_invalid(self) -> bool:
        return self.status == ImportPreflightStatus.STRUCTURE_INVALID

    def to_api_payload(self) -> dict[str, object]:
        return {
            'status': self.status.value,
            'is_valid': self.is_valid,
            'is_header_invalid': self.is_header_invalid,
            'is_sheet_missing': self.is_sheet_missing,
            'is_structure_invalid': self.is_structure_invalid,
            'sheet': {
                'name': self.sheet_name,
                'exists': self.sheet_exists,
                'has_merged_header': self.has_merged_header,
            },
            'summary': {
                'estimated_row_count': self.estimated_row_count,
                'structural_issue_codes': list(self.structural_issue_codes),
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
    def from_validate_header_result(
        cls,
        result: ValidateHeaderResult,
        *,
        sheet_name: str,
        sheet_exists: bool = True,
        has_merged_header: bool | None = None,
        estimated_row_count: int = 0,
    ) -> 'ImportPreflightResult':
        """Build a preflight result from a header-validation result."""
        if result.is_valid:
            return cls(
                status=ImportPreflightStatus.VALID,
                sheet_name=sheet_name,
                sheet_exists=sheet_exists,
                has_merged_header=has_merged_header,
                estimated_row_count=estimated_row_count,
            )
        return cls(
            status=ImportPreflightStatus.HEADER_INVALID,
            sheet_name=sheet_name,
            sheet_exists=sheet_exists,
            has_merged_header=has_merged_header,
            estimated_row_count=estimated_row_count,
            is_required_missing=result.is_required_missing,
            missing_required=result.missing_required,
            missing_primary=result.missing_primary,
            unrecognized=result.unrecognized,
            duplicated=result.duplicated,
        )
