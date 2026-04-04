"""Minimal reference FastAPI project with route, service, and storage layers."""

# pyright: reportMissingImports=false

from __future__ import annotations

import importlib.util
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING or importlib.util.find_spec('fastapi') is not None:
    from fastapi import FastAPI, UploadFile
    from fastapi.responses import StreamingResponse
else:
    FastAPI = Any
    UploadFile = Any
    StreamingResponse = Any

from io import BytesIO

from examples.fastapi_reference.schemas import EmployeeImportRequest, EmployeeImportResponse
from examples.fastapi_reference.services import EmployeeImportService, run_reference_demo
from examples.fastapi_reference.storage import RequestScopedStorage


def create_app(service: EmployeeImportService | None = None) -> FastAPI:
    from fastapi import FastAPI, Form, HTTPException
    from fastapi.responses import StreamingResponse

    app = FastAPI(title='ExcelAlchemy Reference FastAPI App')
    import_service = service or EmployeeImportService(RequestScopedStorage())

    @app.get('/employee-template.xlsx')
    async def download_template() -> StreamingResponse:
        return StreamingResponse(
            BytesIO(import_service.generate_template_bytes()),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename=employee-template.xlsx'},
        )

    @app.post('/employee-imports', response_model=EmployeeImportResponse)
    async def import_employees(
        file: UploadFile,
        tenant_id: str = Form(default='tenant-001'),
    ) -> EmployeeImportResponse:
        if not file.filename:
            raise HTTPException(status_code=400, detail='An Excel file is required')
        return await import_service.import_workbook(
            file.filename,
            await file.read(),
            request=EmployeeImportRequest(tenant_id=tenant_id),
        )

    return app


def main() -> None:
    response_payload = run_reference_demo()
    route_paths = ['/employee-imports', '/employee-template.xlsx']

    print('FastAPI reference project completed')
    print(f'Result: {response_payload.result_status}')
    print(f'Success rows: {response_payload.result_success_count}')
    print(f'Failed rows: {response_payload.result_fail_count}')
    print(f'Created rows: {response_payload.created_rows}')
    print(f'Uploaded artifacts: {response_payload.uploaded_artifacts}')
    print(f'Routes: {route_paths}')
    print(f'Response sections: {sorted(response_payload.model_dump().keys())}')
    print(f'Request tenant: {response_payload.request.tenant_id}')
    print(f"Cell error summary keys: {sorted(response_payload.cell_errors['summary'].keys())}")
    print(f"Row error summary keys: {sorted(response_payload.row_errors['summary'].keys())}")


app = create_app() if importlib.util.find_spec('fastapi') is not None else None


__all__ = ['app', 'create_app', 'main']


if __name__ == '__main__':
    main()
