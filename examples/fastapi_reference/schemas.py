"""Request and response schemas for the FastAPI reference project."""

from typing import Literal

from pydantic import BaseModel, Field


class EmployeeImportRequest(BaseModel):
    """Structured request metadata for workbook imports."""

    tenant_id: str = Field(default='tenant-001', description='Tenant or request-scope identifier.')


class EmployeeImportResponse(BaseModel):
    """Structured API response for workbook import endpoints."""

    result: dict[str, object] = Field(description='High-level import result payload.')
    cell_errors: dict[str, object] = Field(description='Structured cell-level error payload.')
    row_errors: dict[str, object] = Field(description='Structured row-level error payload.')
    created_rows: int = Field(description='Number of created rows in the demo service.')
    uploaded_artifacts: list[str] = Field(description='Uploaded workbook artifact names.')
    request: EmployeeImportRequest = Field(description='Structured request metadata.')

    @property
    def result_status(self) -> str:
        value = self.result['result']
        assert isinstance(value, str)
        return value

    @property
    def result_success_count(self) -> int:
        summary = self.result['summary']
        assert isinstance(summary, dict)
        value = summary['success_count']
        assert isinstance(value, int)
        return value

    @property
    def result_fail_count(self) -> int:
        summary = self.result['summary']
        assert isinstance(summary, dict)
        value = summary['fail_count']
        assert isinstance(value, int)
        return value


class ApiErrorDetail(BaseModel):
    """Structured API error payload for the HTTP layer."""

    code: str = Field(description='Machine-readable API error code.')
    message: str = Field(description='Human-readable API error message.')
    detail: dict[str, object] = Field(default_factory=dict, description='Optional structured error detail.')


class EmployeeImportSuccessEnvelope(BaseModel):
    """Success response envelope for workbook import endpoints."""

    ok: Literal[True] = Field(default=True, description='Whether the request succeeded.')
    data: EmployeeImportResponse = Field(description='Structured import payload.')


class EmployeeImportErrorEnvelope(BaseModel):
    """Error response envelope for workbook import endpoints."""

    ok: Literal[False] = Field(default=False, description='Whether the request failed.')
    error: ApiErrorDetail = Field(description='Structured API error payload.')


__all__ = [
    'ApiErrorDetail',
    'EmployeeImportErrorEnvelope',
    'EmployeeImportRequest',
    'EmployeeImportResponse',
    'EmployeeImportSuccessEnvelope',
]
