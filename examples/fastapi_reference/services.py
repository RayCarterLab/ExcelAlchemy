"""Service layer for the FastAPI reference project."""

from __future__ import annotations

import asyncio
import io

from openpyxl import load_workbook

from examples.fastapi_reference.models import EmployeeImporter
from examples.fastapi_reference.storage import RequestScopedStorage
from excelalchemy import ExcelAlchemy, ImporterConfig, ImportResult


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

    def build_alchemy(self) -> ExcelAlchemy[dict[str, object], EmployeeImporter, EmployeeImporter]:
        alchemy = ExcelAlchemy(
            ImporterConfig.for_create(
                EmployeeImporter,
                creator=create_employee,
                storage=self.storage,
                locale='en',
            )
        )
        alchemy.add_context({'tenant_id': self.tenant_id, 'created_rows': []})
        return alchemy

    def generate_template_bytes(self) -> bytes:
        alchemy = ExcelAlchemy(ImporterConfig.for_create(EmployeeImporter, locale='en'))
        artifact = alchemy.download_template_artifact(filename='employee-template.xlsx')
        return artifact.as_bytes()

    async def import_workbook(self, filename: str, content: bytes) -> dict[str, object]:
        self.storage.register_upload(filename, content)
        alchemy = self.build_alchemy()
        result = await alchemy.import_data(filename, 'employee-import-result.xlsx')
        created_rows = alchemy.context['created_rows']
        assert isinstance(created_rows, list)
        return {
            'result': result.model_dump(),
            'created_rows': len(created_rows),
            'uploaded_artifacts': sorted(self.storage.uploaded),
        }


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


def summarize_result(payload: dict[str, object]) -> tuple[ImportResult, int, list[str]]:
    result = ImportResult.model_validate(payload['result'])
    created_rows = payload['created_rows']
    uploaded_artifacts = payload['uploaded_artifacts']
    assert isinstance(created_rows, int)
    assert isinstance(uploaded_artifacts, list)
    assert all(isinstance(item, str) for item in uploaded_artifacts)
    return result, created_rows, uploaded_artifacts


def run_reference_demo() -> tuple[ImportResult, int, list[str]]:
    storage = RequestScopedStorage()
    service = EmployeeImportService(storage)
    template_bytes = service.generate_template_bytes()
    upload_bytes = build_demo_upload(template_bytes)
    payload = asyncio.run(service.import_workbook('employee-import.xlsx', upload_bytes))
    return summarize_result(payload)


__all__ = [
    'EmployeeImportService',
    'build_demo_upload',
    'create_employee',
    'run_reference_demo',
    'summarize_result',
]
