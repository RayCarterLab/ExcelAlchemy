"""Custom storage example that keeps uploaded workbooks in memory."""

from __future__ import annotations

from base64 import b64decode

from pydantic import BaseModel

from excelalchemy import ExcelAlchemy, ExcelStorage, ExporterConfig, FieldMeta, Number, String, UrlStr
from excelalchemy.core.table import WorksheetTable


class InMemoryStorage(ExcelStorage):
    def __init__(self) -> None:
        self.uploaded: dict[str, bytes] = {}

    def read_excel_table(self, input_excel_name: str, *, skiprows: int, sheet_name: str) -> WorksheetTable:
        raise NotImplementedError('This example only demonstrates export uploads')

    def upload_excel(self, output_name: str, content_with_prefix: str) -> UrlStr:
        _, payload = content_with_prefix.split(',', 1)
        self.uploaded[output_name] = b64decode(payload)
        return UrlStr(f'memory://{output_name}')


class EmployeeExporter(BaseModel):
    full_name: String = FieldMeta(label='Full name', order=1)
    age: Number = FieldMeta(label='Age', order=2)


def main() -> None:
    storage = InMemoryStorage()
    alchemy = ExcelAlchemy(ExporterConfig.for_storage(EmployeeExporter, storage=storage, locale='en'))
    uploaded_url = alchemy.export_upload(
        'employees.xlsx',
        data=[{'full_name': 'Taylor Chen', 'age': 32}],
    )
    print(uploaded_url)
    print(f'Uploaded bytes: {len(storage.uploaded["employees.xlsx"])}')


if __name__ == '__main__':
    main()
