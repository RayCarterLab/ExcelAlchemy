"""Service layer for the FastAPI reference project."""

from __future__ import annotations

import asyncio
import io

from openpyxl import load_workbook

from examples.fastapi_reference.models import EmployeeImporter
from examples.fastapi_reference.responses import build_import_response
from examples.fastapi_reference.schemas import EmployeeImportRequest, EmployeeImportResponse
from examples.fastapi_reference.storage import RequestScopedStorage
from excelalchemy import ExcelAlchemy, ImporterConfig


async def create_employee(row: dict[str, object], context: dict[str, object] | None) -> dict[str, object]:
    if context is not None:
        created_rows = context.setdefault('created_rows', [])
        assert isinstance(created_rows, list)
        created_rows.append(row.copy())
        row['tenant_id'] = context['tenant_id']
    return row


class EmployeeImportService:
    """Minimal service layer that a web app can inject into routes."""

    def __init__(self, storage: RequestScopedStorage, *, tenant_id: str = 'tenant-001') -> None:
        self.storage = storage
        self.tenant_id = tenant_id

    def build_alchemy(
        self, *, tenant_id: str | None = None
    ) -> ExcelAlchemy[dict[str, object], EmployeeImporter, EmployeeImporter, EmployeeImporter]:
        alchemy = ExcelAlchemy(
            ImporterConfig.for_create(
                EmployeeImporter,
                creator=create_employee,
                storage=self.storage,
                locale='en',
            )
        )
        alchemy.add_context({'tenant_id': tenant_id or self.tenant_id, 'created_rows': []})
        return alchemy

    def generate_template_bytes(self) -> bytes:
        alchemy = ExcelAlchemy(ImporterConfig.for_create(EmployeeImporter, locale='en'))
        artifact = alchemy.download_template_artifact(filename='employee-template.xlsx')
        return artifact.as_bytes()

    async def import_workbook(
        self,
        filename: str,
        content: bytes,
        *,
        request: EmployeeImportRequest | None = None,
    ) -> EmployeeImportResponse:
        request_model = request or EmployeeImportRequest(tenant_id=self.tenant_id)
        self.storage.register_upload(filename, content)
        alchemy = self.build_alchemy(tenant_id=request_model.tenant_id)
        result = await alchemy.import_data(filename, 'employee-import-result.xlsx')
        context = alchemy.context
        assert context is not None
        created_rows = context['created_rows']
        assert isinstance(created_rows, list)
        return build_import_response(
            result=result,
            cell_error_map=alchemy.cell_error_map,
            row_error_map=alchemy.row_error_map,
            created_rows=len(created_rows),
            uploaded_artifacts=sorted(self.storage.uploaded),
            request=request_model,
        )


def build_demo_upload(template_bytes: bytes) -> bytes:
    workbook = load_workbook(io.BytesIO(template_bytes))
    try:
        worksheet = workbook['Sheet1']
        worksheet['A3'] = 'TaylorChen'
        worksheet['B3'] = '32'
        buffer = io.BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()
    finally:
        workbook.close()


def run_reference_demo() -> EmployeeImportResponse:
    storage = RequestScopedStorage()
    service = EmployeeImportService(storage)
    template_bytes = service.generate_template_bytes()
    upload_bytes = build_demo_upload(template_bytes)
    return asyncio.run(
        service.import_workbook(
            'employee-import.xlsx',
            upload_bytes,
            request=EmployeeImportRequest(tenant_id='tenant-001'),
        )
    )


__all__ = [
    'EmployeeImportService',
    'build_demo_upload',
    'create_employee',
    'run_reference_demo',
]
