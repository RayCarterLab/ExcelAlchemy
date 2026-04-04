"""Response builders for the FastAPI reference project."""

from examples.fastapi_reference.schemas import EmployeeImportRequest, EmployeeImportResponse
from excelalchemy import CellErrorMap, ImportResult, RowIssueMap


def build_import_response(
    *,
    result: ImportResult,
    cell_error_map: CellErrorMap,
    row_error_map: RowIssueMap,
    created_rows: int,
    uploaded_artifacts: list[str],
    request: EmployeeImportRequest,
) -> EmployeeImportResponse:
    """Build a stable API response for workbook-import endpoints."""

    return EmployeeImportResponse(
        result=result.to_api_payload(),
        cell_errors=cell_error_map.to_api_payload(),
        row_errors=row_error_map.to_api_payload(),
        created_rows=created_rows,
        uploaded_artifacts=uploaded_artifacts,
        request=request,
    )


__all__ = ['build_import_response']
