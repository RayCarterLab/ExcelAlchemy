import io
from typing import cast

from minio import Minio
from openpyxl import Workbook

from excelalchemy import ConfigError, ExcelAlchemy, ExporterConfig, ImporterConfig, ValidateResult
from excelalchemy.core.storage import MissingStorageGateway, build_storage_gateway
from excelalchemy.core.storage_minio import MinioStorageGateway
from excelalchemy.core.storage_protocol import ExcelStorage
from excelalchemy.core.table import WorksheetTable
from tests.support import BaseTestCase, FileRegistry, InMemoryExcelStorage
from tests.support.contract_models import SimpleContractImporter, creator, sample_simple_export_row


class TestStorageContracts(BaseTestCase):
    def _build_storage_gateway(self) -> ExcelStorage:
        config = ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio))
        return build_storage_gateway(config)

    async def test_default_storage_gateway_conforms_to_excel_storage_protocol(self):
        gateway = self._build_storage_gateway()

        assert isinstance(gateway, ExcelStorage)
        assert isinstance(gateway, MinioStorageGateway)

    async def test_missing_storage_gateway_is_used_when_no_backend_is_configured(self):
        config = ImporterConfig(SimpleContractImporter, creator=creator)
        gateway = build_storage_gateway(config)

        assert isinstance(gateway, MissingStorageGateway)

    async def test_template_generation_does_not_require_storage_backend(self):
        alchemy = ExcelAlchemy(ImporterConfig(SimpleContractImporter, creator=creator))

        template = alchemy.download_template([sample_simple_export_row()])

        assert template.startswith('data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,')

    async def test_export_upload_without_storage_backend_raises_clear_error(self):
        alchemy = ExcelAlchemy(ExporterConfig(SimpleContractImporter))

        with self.assertRaises(ConfigError) as cm:
            alchemy.export_upload('missing-storage.xlsx', [sample_simple_export_row()])

        self.assertEqual(
            str(cm.exception),
            'No storage backend is configured; pass storage=... or install and configure ExcelAlchemy[minio]',
        )

    async def test_explicit_storage_is_preferred_over_legacy_minio_settings(self):
        input_name = FileRegistry.TEST_SIMPLE_IMPORT
        input_bytes = self.minio.storage[input_name]['data'].getvalue()
        storage = InMemoryExcelStorage({input_name: input_bytes})
        config = ImporterConfig(
            SimpleContractImporter,
            creator=creator,
            storage=storage,
            minio=cast(Minio, self.minio),
        )
        gateway = build_storage_gateway(config)

        assert gateway is storage

        alchemy = ExcelAlchemy(config)
        result = await alchemy.import_data(
            input_excel_name=input_name,
            output_excel_name='storage-preferred.xlsx',
        )

        assert result.result == ValidateResult.SUCCESS
        assert 'storage-preferred.xlsx' not in self.minio.storage

    async def test_export_upload_supports_explicit_custom_storage(self):
        storage = InMemoryExcelStorage()
        output_name = 'contract-export-memory.xlsx'
        alchemy = ExcelAlchemy(ExporterConfig(SimpleContractImporter, storage=storage))

        url = alchemy.export_upload(output_name, [sample_simple_export_row()])

        assert url == f'memory://{output_name}'
        assert output_name in storage.uploaded
        assert storage.uploaded[output_name].startswith(b'PK')

    async def test_import_failure_upload_supports_explicit_custom_storage(self):
        input_name = FileRegistry.TEST_SIMPLE_IMPORT_WITH_ERROR
        input_bytes = self.minio.storage[input_name]['data'].getvalue()
        output_name = 'contract-import-memory.xlsx'
        storage = InMemoryExcelStorage({input_name: input_bytes})
        alchemy = ExcelAlchemy(ImporterConfig(SimpleContractImporter, creator=creator, storage=storage))

        result = await alchemy.import_data(input_excel_name=input_name, output_excel_name=output_name)

        assert result.result == ValidateResult.DATA_INVALID
        assert result.url == f'memory://{output_name}'
        assert output_name in storage.uploaded
        assert storage.uploaded[output_name].startswith(b'PK')

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

        table = gateway.read_excel_table(FileRegistry.TEST_SIMPLE_IMPORT, skiprows=1, sheet_name='Sheet1')

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

        table = gateway.read_excel_table(input_name, skiprows=1, sheet_name='Sheet1')

        assert table.iloc[0].tolist() == ['日期范围', None]
        assert table.iloc[1].tolist() == ['开始日期', '结束日期']
