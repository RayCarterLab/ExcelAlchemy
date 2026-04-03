"""End-to-end export example with artifact generation and upload."""

from base64 import b64decode

from pydantic import BaseModel

from excelalchemy import ExcelAlchemy, ExcelStorage, ExporterConfig, FieldMeta, Number, String, UrlStr
from excelalchemy.core.table import WorksheetTable


class InMemoryExportStorage(ExcelStorage):
    def __init__(self) -> None:
        self.uploaded: dict[str, bytes] = {}

    def read_excel_table(self, input_excel_name: str, *, skiprows: int, sheet_name: str) -> WorksheetTable:
        raise NotImplementedError('This example focuses on export workflows only')

    def upload_excel(self, output_name: str, content_with_prefix: str) -> UrlStr:
        _, payload = content_with_prefix.split(',', 1)
        self.uploaded[output_name] = b64decode(payload)
        return UrlStr(f'memory://{output_name}')


class EmployeeExporter(BaseModel):
    full_name: String = FieldMeta(label='Full name', order=1)
    team: String = FieldMeta(label='Team', order=2)
    age: Number = FieldMeta(label='Age', order=3)


def main() -> None:
    rows = [
        {'full_name': 'TaylorChen', 'team': 'Finance', 'age': 32},
        {'full_name': 'AveryStone', 'team': 'Operations', 'age': 29},
    ]

    storage = InMemoryExportStorage()
    alchemy = ExcelAlchemy(ExporterConfig.for_storage(EmployeeExporter, storage=storage, locale='en'))

    artifact = alchemy.export_artifact(rows, filename='employees-export.xlsx')
    uploaded_url = alchemy.export_upload('employees-export-upload.xlsx', rows)

    print('Export workflow completed')
    print(f'Artifact filename: {artifact.filename}')
    print(f'Artifact bytes: {len(artifact.as_bytes())}')
    print(f'Upload URL: {uploaded_url}')
    print(f'Uploaded objects: {sorted(storage.uploaded)}')


if __name__ == '__main__':
    main()
