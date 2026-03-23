from typing import cast

from minio import Minio

from excelalchemy import ExcelAlchemy, ImporterConfig, ValidateResult
from excelalchemy.const import BACKGROUND_ERROR_COLOR, REASON_COLUMN_LABEL, RESULT_COLUMN_LABEL
from tests.support import BaseTestCase, FileRegistry, get_fill_color, load_binary_excel_to_workbook
from tests.support.contract_models import SimpleContractImporter, creator


class TestImportContracts(BaseTestCase):
    async def test_import_data_returns_success_result_for_valid_workbook(self):
        alchemy = ExcelAlchemy(ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio)))

        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_SIMPLE_IMPORT,
            output_excel_name='contract-success.xlsx',
        )

        assert result.result == ValidateResult.SUCCESS
        assert result.success_count == 1
        assert result.fail_count == 0
        assert result.url is None

    async def test_import_data_returns_header_invalid_result_for_invalid_header(self):
        output_name = 'contract-header-invalid.xlsx'
        self.minio.storage.pop(output_name, None)
        alchemy = ExcelAlchemy(ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio)))

        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_HEADER_INVALID_INPUT,
            output_excel_name=output_name,
        )

        assert result.result == ValidateResult.HEADER_INVALID
        assert set(result.unrecognized) == {'不存在的表头'}
        assert '年龄' in set(result.missing_required)
        assert output_name not in self.minio.storage

    async def test_import_data_uploads_result_workbook_for_invalid_rows(self):
        output_name = 'contract-data-invalid.xlsx'
        self.minio.storage.pop(output_name, None)
        alchemy = ExcelAlchemy(ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio)))

        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_SIMPLE_IMPORT_WITH_ERROR,
            output_excel_name=output_name,
        )

        assert result.result == ValidateResult.DATA_INVALID
        assert result.success_count == 0
        assert result.fail_count == 1
        assert result.url == f'excel/{output_name}'
        assert output_name in self.minio.storage

    async def test_import_result_workbook_returns_result_and_reason_columns(self):
        output_name = 'contract-data-invalid-columns.xlsx'
        self.minio.storage.pop(output_name, None)
        alchemy = ExcelAlchemy(ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio)))

        await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_SIMPLE_IMPORT_WITH_ERROR,
            output_excel_name=output_name,
        )
        workbook = load_binary_excel_to_workbook(self.minio.storage[output_name]['data'].getvalue())
        worksheet = workbook['Sheet1']

        assert worksheet['A2'].value == RESULT_COLUMN_LABEL
        assert worksheet['B2'].value == REASON_COLUMN_LABEL
        assert worksheet['A3'].value == '校验不通过'
        assert isinstance(worksheet['B3'].value, str)
        assert worksheet['B3'].value.startswith('1、')
        assert '【出生日期】' in worksheet['B3'].value

    async def test_import_result_workbook_marks_failed_cells_in_red(self):
        output_name = 'contract-data-invalid-colors.xlsx'
        self.minio.storage.pop(output_name, None)
        alchemy = ExcelAlchemy(ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio)))

        await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_SIMPLE_IMPORT_WITH_ERROR,
            output_excel_name=output_name,
        )
        workbook = load_binary_excel_to_workbook(self.minio.storage[output_name]['data'].getvalue())
        worksheet = workbook['Sheet1']
        row_colors = [get_fill_color(cell) for cell in worksheet[3]]

        assert BACKGROUND_ERROR_COLOR in row_colors
