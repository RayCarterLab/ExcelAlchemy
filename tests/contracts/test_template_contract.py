from typing import cast

from minio import Minio

from excelalchemy import ExcelAlchemy, ImporterConfig
from excelalchemy.const import BACKGROUND_REQUIRED_COLOR, HEADER_HINT
from tests.support import (
    BaseTestCase,
    decode_prefixed_excel_to_workbook,
    get_fill_color,
    list_data_validations,
    list_merge_ranges,
)
from tests.support.contract_models import MergedContractImporter, SimpleContractImporter, creator


class TestTemplateContracts(BaseTestCase):
    async def test_download_template_returns_prefixed_base64_payload(self):
        alchemy = ExcelAlchemy(ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio)))

        content = alchemy.download_template()

        assert content.startswith('data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,')

    async def test_download_template_returns_sample_rows_with_user_visible_values(self):
        alchemy = ExcelAlchemy(ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio)))

        workbook = decode_prefixed_excel_to_workbook(
            alchemy.download_template([{'age': 18, 'name': '张三', 'radio': '选项1'}])
        )
        worksheet = workbook['Sheet1']

        assert worksheet['A1'].value == HEADER_HINT
        assert worksheet['A3'].value == '18'
        assert worksheet['B3'].value == '张三'
        assert worksheet['O3'].value == '选项1'

    async def test_download_template_returns_simple_header_with_required_fill_and_comment(self):
        alchemy = ExcelAlchemy(ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio)))

        workbook = decode_prefixed_excel_to_workbook(alchemy.download_template())
        worksheet = workbook['Sheet1']

        assert worksheet['A2'].value == '年龄'
        assert get_fill_color(worksheet['A2']) == BACKGROUND_REQUIRED_COLOR
        assert worksheet['A2'].comment is not None
        assert '必填性：必填' in worksheet['A2'].comment.text

    async def test_download_template_returns_merged_header_with_expected_merge_ranges(self):
        alchemy = ExcelAlchemy(ImporterConfig(MergedContractImporter, creator=creator, minio=cast(Minio, self.minio)))

        workbook = decode_prefixed_excel_to_workbook(alchemy.download_template())
        worksheet = workbook['Sheet1']
        merge_ranges = list_merge_ranges(worksheet)
        second_row = [worksheet.cell(row=2, column=index).value for index in range(1, worksheet.max_column + 1)]
        third_row = [worksheet.cell(row=3, column=index).value for index in range(1, worksheet.max_column + 1)]

        assert worksheet['A1'].value == HEADER_HINT
        assert '最大停留日期' in second_row
        assert '工资' in second_row
        assert '开始日期' in third_row
        assert '结束日期' in third_row
        assert '最小值' in third_row
        assert '最大值' in third_row
        assert 'A2:A3' in merge_ranges
        assert 'R2:S2' in merge_ranges
        assert 'T2:U2' in merge_ranges

    async def test_download_template_returns_workbook_without_excel_data_validation(self):
        alchemy = ExcelAlchemy(ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio)))

        workbook = decode_prefixed_excel_to_workbook(alchemy.download_template())
        worksheet = workbook['Sheet1']
        validations = list_data_validations(worksheet)

        assert validations == []
