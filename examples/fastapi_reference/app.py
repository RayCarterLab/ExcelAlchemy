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

from examples.fastapi_reference.presenters import (
    build_import_success_envelope,
    build_missing_file_error_envelope,
)
from examples.fastapi_reference.schemas import (
    EmployeeImportErrorEnvelope,
    EmployeeImportRequest,
    EmployeeImportSuccessEnvelope,
)
from examples.fastapi_reference.services import EmployeeImportService, run_reference_demo
from examples.fastapi_reference.storage import RequestScopedStorage


def create_app(service: EmployeeImportService | None = None) -> FastAPI:
    from fastapi import FastAPI, Form
    from fastapi.responses import JSONResponse, StreamingResponse

    app = FastAPI(title='ExcelAlchemy Reference FastAPI App')
    import_service = service or EmployeeImportService(RequestScopedStorage())

    @app.get('/employee-template.xlsx')
    async def download_template() -> StreamingResponse:
        return StreamingResponse(
            BytesIO(import_service.generate_template_bytes()),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename=employee-template.xlsx'},
        )

    @app.post('/employee-imports', response_model=EmployeeImportSuccessEnvelope | EmployeeImportErrorEnvelope)
    async def import_employees(
        file: UploadFile | None = None,
        tenant_id: str = Form(default='tenant-001'),
    ) -> EmployeeImportSuccessEnvelope | JSONResponse:
        if file is None or not file.filename:
            return JSONResponse(
                status_code=400,
                content=build_missing_file_error_envelope().model_dump(mode='json'),
            )
        response_payload = await import_service.import_workbook(
            file.filename,
            await file.read(),
            request=EmployeeImportRequest(tenant_id=tenant_id),
        )
        return build_import_success_envelope(response_payload)

    return app


def main() -> None:
    response_payload = run_reference_demo()
    envelope = build_import_success_envelope(response_payload)
    route_paths = ['/employee-imports', '/employee-template.xlsx']

    print('FastAPI reference project completed')
    print(f'Result: {response_payload.result_status}')
    print(f'Success rows: {response_payload.result_success_count}')
    print(f'Failed rows: {response_payload.result_fail_count}')
    print(f'Created rows: {response_payload.created_rows}')
    print(f'Uploaded artifacts: {response_payload.uploaded_artifacts}')
    print(f'Routes: {route_paths}')
    print(f'Envelope sections: {sorted(envelope.model_dump().keys())}')
    print(f'Data sections: {sorted(response_payload.model_dump().keys())}')
    print(f'Request tenant: {response_payload.request.tenant_id}')
    print(f"Cell error summary keys: {sorted(response_payload.cell_errors['summary'].keys())}")
    print(f"Row error summary keys: {sorted(response_payload.row_errors['summary'].keys())}")
    print(f"Remediation keys: {sorted(response_payload.remediation.keys())}")


app = create_app() if importlib.util.find_spec('fastapi') is not None else None


__all__ = ['app', 'create_app', 'main']


if __name__ == '__main__':
    main()
