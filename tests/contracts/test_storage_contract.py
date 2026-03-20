from typing import cast

from minio import Minio

from excelalchemy import ExcelAlchemy
from excelalchemy import ExporterConfig
from excelalchemy import ImporterConfig
from tests.support import BaseTestCase
from tests.support import FileRegistry
from tests.support.contract_models import SimpleContractImporter
from tests.support.contract_models import creator
from tests.support.contract_models import sample_simple_export_row


class TestStorageContracts(BaseTestCase):
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
        alchemy = ExcelAlchemy(
            ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio))
        )

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
