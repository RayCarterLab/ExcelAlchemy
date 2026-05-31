from excelalchemy import ExcelAlchemy, ExporterConfig
from excelalchemy.rendering.writer import render_merged_header_excel, render_simple_header_excel
from tests.support import decode_prefixed_excel_to_workbook, list_merge_ranges
from tests.support.contract_models import (
    MergedContractImporter,
    SimpleContractImporter,
    sample_merged_export_row,
    sample_simple_export_row,
)


def test_simple_header_column_write_offset_shifts_output_without_dropping_columns() -> None:
    alchemy = ExcelAlchemy(ExporterConfig(SimpleContractImporter))
    worksheet_table, has_merged_header = alchemy._gen_export_df([sample_simple_export_row()], keys=['age', 'name'])

    workbook = decode_prefixed_excel_to_workbook(
        render_simple_header_excel(
            worksheet_table,
            alchemy.unique_label_to_field_meta,
            column_write_offset=1,
        )
    )
    worksheet = workbook['Sheet1']

    assert has_merged_header is False
    assert worksheet['A2'].value is None
    assert worksheet['B2'].value == '年龄'
    assert worksheet['C2'].value == '姓名'
    assert worksheet['B3'].value == '18'
    assert worksheet['C3'].value == '张三'
    assert 'A1:C1' in list_merge_ranges(worksheet)


def test_merged_header_span_uses_only_rendered_columns() -> None:
    alchemy = ExcelAlchemy(ExporterConfig(MergedContractImporter))
    selected_keys = alchemy._select_output_excel_keys(['max_stay_date·start'])
    worksheet_table = alchemy._export_with_merged_header([sample_merged_export_row()], selected_keys)

    workbook = decode_prefixed_excel_to_workbook(
        render_merged_header_excel(worksheet_table, alchemy.unique_label_to_field_meta)
    )
    worksheet = workbook['Sheet1']

    assert worksheet.max_column == 1
    assert worksheet['A2'].value == '最大停留日期'
    assert worksheet['A3'].value == '开始日期'
    assert worksheet['A4'].value == '2020-01-01'
    assert 'A2:B2' not in list_merge_ranges(worksheet)


def test_merged_header_parent_label_is_written_for_selected_nonzero_child_offset() -> None:
    alchemy = ExcelAlchemy(ExporterConfig(MergedContractImporter))
    selected_keys = alchemy._select_output_excel_keys(['max_stay_date·end'])
    worksheet_table = alchemy._export_with_merged_header([sample_merged_export_row()], selected_keys)

    workbook = decode_prefixed_excel_to_workbook(
        render_merged_header_excel(worksheet_table, alchemy.unique_label_to_field_meta)
    )
    worksheet = workbook['Sheet1']

    assert worksheet.max_column == 1
    assert worksheet['A2'].value == '最大停留日期'
    assert worksheet['A3'].value == '结束日期'
    assert worksheet['A4'].value == '2021-01-02'
