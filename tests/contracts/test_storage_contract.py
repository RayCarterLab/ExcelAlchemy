import io
from typing import cast

from minio import Minio
from openpyxl import Workbook

from excelalchemy import ExcelAlchemy, ExporterConfig, ImporterConfig
from excelalchemy.core.storage import MinioStorageGateway
from excelalchemy.core.table import WorksheetTable
from tests.support import BaseTestCase, FileRegistry
from tests.support.contract_models import SimpleContractImporter, creator, sample_simple_export_row


class TestStorageContracts(BaseTestCase):
    def _build_storage_gateway(self) -> MinioStorageGateway:
        config = ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio))
        return MinioStorageGateway(config)

    async def test_export_upload_stores_generated_workbook_in_minio(self):
        output_name = 'contract-export-upload.xlsx'
        self.minio.storage.pop(output_name, None)
        alchemy = ExcelAlchemy(ExporterConfig(SimpleContractImporter, minio=cast(Minio, self.minio)))

        url = alchemy.export_upload(output_name, [sample_simple_export_row()])

        assert url == f'excel/{output_name}'
        assert output_name in self.minio.storage
        assert self.minio.storage[output_name]['bucket_name'] == 'excel'
        assert self.minio.storage[output_name]['data'].getvalue().startswith(b'PK')

    async def test_import_failure_upload_uses_requested_output_excel_name(self):
        output_name = 'contract-import-upload.xlsx'
        self.minio.storage.pop(output_name, None)
        alchemy = ExcelAlchemy(ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio)))

        await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_SIMPLE_IMPORT_WITH_ERROR,
            output_excel_name=output_name,
        )

        assert output_name in self.minio.storage
        assert self.minio.storage[output_name]['filename'] == output_name

    async def test_uploaded_payload_remains_binary_excel_content_without_prefix(self):
        output_name = 'contract-upload-bytes.xlsx'
        self.minio.storage.pop(output_name, None)
        alchemy = ExcelAlchemy(ExporterConfig(SimpleContractImporter, minio=cast(Minio, self.minio)))

        alchemy.export_upload(output_name, [sample_simple_export_row()])
        payload = self.minio.storage[output_name]['data'].getvalue()

        assert payload.startswith(b'PK')
        assert not payload.startswith(b'data:application')

    async def test_storage_reader_returns_worksheet_table_for_simple_import_workbook(self):
        gateway = self._build_storage_gateway()

        table = gateway.read_excel_dataframe(FileRegistry.TEST_SIMPLE_IMPORT, skiprows=1, sheet_name='Sheet1')

        assert isinstance(table, WorksheetTable)
        assert table.shape == (2, 17)
        assert table.iloc[0].tolist()[:3] == ['年龄', '姓名', '地址']
        assert table.iloc[1].tolist()[:3] == ['18', '张三', '北京市']

    async def test_storage_reader_preserves_empty_cells_from_merged_headers(self):
        gateway = self._build_storage_gateway()
        workbook = Workbook()
        worksheet = workbook.active
        assert worksheet is not None
        worksheet.title = 'Sheet1'
        worksheet.append(['HEADER_HINT', None])
        worksheet.append(['日期范围', None])
        worksheet.append(['开始日期', '结束日期'])
        worksheet.append(['2024-01-01', '2024-01-31'])
        worksheet.merge_cells('A2:B2')

        file_object = io.BytesIO()
        workbook.save(file_object)
        payload = file_object.getvalue()
        input_name = 'contract-merged-reader.xlsx'
        self.minio.put_object(self.minio.bucket_name, input_name, io.BytesIO(payload), len(payload))

        table = gateway.read_excel_dataframe(input_name, skiprows=1, sheet_name='Sheet1')

        assert table.iloc[0].tolist() == ['日期范围', None]
        assert table.iloc[1].tolist() == ['开始日期', '结束日期']
