from excelalchemy.core.alchemy import REASON_COLUMN, RESULT_COLUMN
from excelalchemy.core.headers import ExcelHeaderParser, ExcelHeaderValidator
from excelalchemy.core.rows import ImportIssueTracker, RowAggregator
from excelalchemy.core.schema import ExcelSchemaLayout
from excelalchemy.core.table import WorksheetTable
from excelalchemy.exc import ExcelCellError
from excelalchemy.types.alchemy import ImportMode
from excelalchemy.types.identity import Key, Label, RowIndex
from tests.support.contract_models import MergedContractImporter, SimpleContractImporter


class TestCoreComponentContracts:
    def test_schema_layout_expands_composite_parent_keys_in_layout_order(self):
        layout = ExcelSchemaLayout.from_model(MergedContractImporter)

        selected = layout.select_output_excel_keys([Key('salary')])

        assert selected == ['salary·start', 'salary·end']
        assert layout.get_output_parent_excel_headers(selected) == ['工资·最小值', '工资·最大值']
        assert layout.get_output_child_excel_headers(selected) == ['最小值', '最大值']
        assert layout.has_merged_header(selected) is True

    def test_header_parser_and_validator_accept_generated_simple_headers_as_contract(self):
        layout = ExcelSchemaLayout.from_model(SimpleContractImporter)
        header_df = WorksheetTable(rows=[layout.get_output_parent_excel_headers()])
        parser = ExcelHeaderParser()
        validator = ExcelHeaderValidator()

        headers = parser.extract(header_df)
        result = validator.validate(headers, layout, ImportMode.CREATE)

        assert [header.unique_label for header in headers] == layout.get_output_parent_excel_headers()
        assert result.is_valid is True

    def test_row_aggregator_groups_composite_cells_back_into_parent_payload(self):
        layout = ExcelSchemaLayout.from_model(MergedContractImporter)
        aggregator = RowAggregator(layout, ImportMode.CREATE)

        row_data = {
            '工资·最小值': '1000',
            '工资·最大值': '2000',
        }

        assert aggregator.aggregate(row_data) == {
            'salary': {'start': 1000, 'end': 2000},
        }

    def test_issue_tracker_offsets_cell_errors_after_result_columns(self):
        layout = ExcelSchemaLayout.from_model(SimpleContractImporter)
        tracker = ImportIssueTracker(layout, [RESULT_COLUMN, REASON_COLUMN])
        df = WorksheetTable(columns=['姓名'], rows=[['张三']])
        error = ExcelCellError(label=Label('姓名'), message='Simulated failure')

        tracker.register_cell_errors(RowIndex(0), [error], df)

        assert tracker.cell_errors == {
            RowIndex(0): {
                2: [error],
            }
        }
