"""Presentation helpers for the FastAPI reference project."""

from examples.fastapi_reference.schemas import (
    ApiErrorDetail,
    EmployeeImportErrorEnvelope,
    EmployeeImportResponse,
    EmployeeImportSuccessEnvelope,
)


def build_import_success_envelope(response: EmployeeImportResponse) -> EmployeeImportSuccessEnvelope:
    """Wrap a successful import payload in a stable HTTP response envelope."""

    return EmployeeImportSuccessEnvelope(data=response)


def build_import_error_envelope(
    *,
    code: str,
    message: str,
    detail: dict[str, object] | None = None,
) -> EmployeeImportErrorEnvelope:
    """Wrap an API-layer error in a stable HTTP response envelope."""

    return EmployeeImportErrorEnvelope(
        error=ApiErrorDetail(
            code=code,
            message=message,
            detail=detail or {},
        )
    )


def build_missing_file_error_envelope() -> EmployeeImportErrorEnvelope:
    """Return the reference error payload for missing upload files."""

    return build_import_error_envelope(
        code='file_required',
        message='An Excel file is required.',
        detail={'field': 'file'},
    )


__all__ = [
    'build_import_error_envelope',
    'build_import_success_envelope',
    'build_missing_file_error_envelope',
]
