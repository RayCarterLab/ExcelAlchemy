from typing import cast

from excelalchemy import ExcelAlchemy, ExporterConfig
from minio import Minio

from tests.support import BaseTestCase, decode_prefixed_excel_to_workbook
from tests.support.contract_models import (
    MergedContractImporter,
    SimpleContractImporter,
    sample_merged_export_row,
    sample_simple_export_row,
)


class TestExportContracts(BaseTestCase):
    async def test_export_returns_prefixed_base64_payload(self):
        alchemy = ExcelAlchemy(ExporterConfig(SimpleContractImporter, minio=cast(Minio, self.minio)))

        content = alchemy.export([sample_simple_export_row()])

        assert content.startswith('data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,')

    async def test_export_returns_only_selected_columns_when_keys_are_provided(self):
        alchemy = ExcelAlchemy(ExporterConfig(SimpleContractImporter, minio=cast(Minio, self.minio)))

        workbook = decode_prefixed_excel_to_workbook(alchemy.export([sample_simple_export_row()], keys=['name', 'age']))
        worksheet = workbook['Sheet1']

        assert worksheet['A2'].value == '年龄'
        assert worksheet['B2'].value == '姓名'
        assert worksheet.max_column == 2
        assert worksheet['A3'].value == '18'
        assert worksheet['B3'].value == '张三'

    async def test_export_preserves_parent_and_child_headers_for_merged_layout(self):
        alchemy = ExcelAlchemy(ExporterConfig(MergedContractImporter, minio=cast(Minio, self.minio)))

        workbook = decode_prefixed_excel_to_workbook(alchemy.export([sample_merged_export_row()]))
        worksheet = workbook['Sheet1']

        second_row = [worksheet.cell(row=2, column=index).value for index in range(1, worksheet.max_column + 1)]
        third_row = [worksheet.cell(row=3, column=index).value for index in range(1, worksheet.max_column + 1)]

        assert '最大停留日期' in second_row
        assert '工资' in second_row
        assert '开始日期' in third_row
        assert '结束日期' in third_row
        assert '最小值' in third_row
        assert '最大值' in third_row

    async def test_export_returns_user_visible_values_for_complex_value_types(self):
        alchemy = ExcelAlchemy(ExporterConfig(MergedContractImporter, minio=cast(Minio, self.minio)))

        workbook = decode_prefixed_excel_to_workbook(alchemy.export([sample_merged_export_row()]))
        worksheet = workbook['Sheet1']

        assert worksheet['D4'].value == '是'
        assert worksheet['O4'].value == '选项1'
        assert worksheet['R4'].value == '2020-01-01'
        assert worksheet['S4'].value == '2021-01-02'
