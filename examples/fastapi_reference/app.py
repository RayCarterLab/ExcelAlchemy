"""Minimal reference FastAPI project with route, service, and storage layers."""

from __future__ import annotations

import importlib.util
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI, UploadFile
    from fastapi.responses import StreamingResponse

from io import BytesIO

from examples.fastapi_reference.services import EmployeeImportService, run_reference_demo
from examples.fastapi_reference.storage import RequestScopedStorage


def create_app(service: EmployeeImportService | None = None) -> FastAPI:
    from fastapi import FastAPI, HTTPException
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

    @app.post('/employee-imports')
    async def import_employees(file: UploadFile) -> dict[str, object]:
        if not file.filename:
            raise HTTPException(status_code=400, detail='An Excel file is required')
        return await import_service.import_workbook(file.filename, await file.read())

    return app


def main() -> None:
    result, created_rows, uploaded_artifacts = run_reference_demo()
    route_paths = ['/employee-imports', '/employee-template.xlsx']

    print('FastAPI reference project completed')
    print(f'Result: {result.result}')
    print(f'Success rows: {result.success_count}')
    print(f'Failed rows: {result.fail_count}')
    print(f'Created rows: {created_rows}')
    print(f'Uploaded artifacts: {uploaded_artifacts}')
    print(f'Routes: {route_paths}')


app = create_app() if importlib.util.find_spec('fastapi') is not None else None


__all__ = ['app', 'create_app', 'main']


if __name__ == '__main__':
    main()
