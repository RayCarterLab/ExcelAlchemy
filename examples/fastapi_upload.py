"""FastAPI integration sketch for template download and workbook import."""

from io import BytesIO

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from excelalchemy import ExcelAlchemy, ExcelStorage, FieldMeta, ImporterConfig, Number, String, UrlStr
from excelalchemy.core.table import WorksheetTable


class EmployeeImporter(BaseModel):
    full_name: String = FieldMeta(label='Full name', order=1)
    age: Number = FieldMeta(label='Age', order=2)


class RequestScopedStorage(ExcelStorage):
    def __init__(self) -> None:
        self.uploaded: dict[str, bytes] = {}

    def read_excel_table(self, input_excel_name: str, *, skiprows: int, sheet_name: str) -> WorksheetTable:
        raise NotImplementedError('Wire this method to your own request-scoped file source')

    def upload_excel(self, output_name: str, content_with_prefix: str) -> UrlStr:
        raise NotImplementedError('Wire this method to your own object storage backend')


async def create_employee(row: dict[str, object], context: dict[str, object] | None) -> dict[str, object]:
    if context is not None:
        row['tenant_id'] = context['tenant_id']
    return row


app = FastAPI()


@app.get('/employee-template.xlsx')
async def download_template() -> StreamingResponse:
    alchemy = ExcelAlchemy(ImporterConfig.for_create(EmployeeImporter, locale='en'))
    artifact = alchemy.download_template_artifact(filename='employee-template.xlsx')
    return StreamingResponse(
        BytesIO(artifact.as_bytes()),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=employee-template.xlsx'},
    )


@app.post('/employee-imports')
async def import_employees(file: UploadFile) -> dict[str, object]:
    if not file.filename:
        raise HTTPException(status_code=400, detail='An Excel file is required')

    storage = RequestScopedStorage()
    alchemy = ExcelAlchemy(
        ImporterConfig.for_create(
            EmployeeImporter,
            creator=create_employee,
            storage=storage,
            locale='en',
        )
    )
    alchemy.add_context({'tenant_id': 'tenant-001'})

    result = await alchemy.import_data(file.filename, 'employee-import-result.xlsx')
    return result.model_dump()
