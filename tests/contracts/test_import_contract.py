import io
from typing import cast

from minio import Minio
from openpyxl import load_workbook

from excelalchemy import ExcelAlchemy, ImporterConfig, ValidateResult
from excelalchemy.const import BACKGROUND_ERROR_COLOR, REASON_COLUMN_LABEL, RESULT_COLUMN_LABEL
from excelalchemy.core.import_session import ImportSessionPhase
from tests.support import (
    BaseTestCase,
    FileRegistry,
    InMemoryExcelStorage,
    get_fill_color,
    load_binary_excel_to_workbook,
)
from tests.support.contract_models import MergedContractImporter, SimpleContractImporter, creator, failing_creator


class TestImportContracts(BaseTestCase):
    async def test_import_data_emits_expected_success_events(self):
        alchemy = ExcelAlchemy(ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio)))
        events: list[dict[str, object]] = []

        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_SIMPLE_IMPORT,
            output_excel_name='contract-success-events.xlsx',
            on_event=events.append,
        )

        assert result.result == ValidateResult.SUCCESS
        assert [event['event'] for event in events] == [
            'started',
            'header_validated',
            'row_processed',
            'completed',
        ]
        assert events[1] == {
            'event': 'header_validated',
            'is_valid': True,
        }
        assert events[2] == {
            'event': 'row_processed',
            'processed_row_count': 1,
            'total_row_count': 1,
            'success_count': 1,
            'fail_count': 0,
        }
        assert events[3] == {
            'event': 'completed',
            'result': 'SUCCESS',
            'success_count': 1,
            'fail_count': 0,
            'url': None,
        }

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

    async def test_import_data_emits_expected_header_invalid_events(self):
        alchemy = ExcelAlchemy(ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio)))
        events: list[dict[str, object]] = []

        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_HEADER_INVALID_INPUT,
            output_excel_name='contract-header-invalid-events.xlsx',
            on_event=events.append,
        )

        assert result.result == ValidateResult.HEADER_INVALID
        assert [event['event'] for event in events] == [
            'started',
            'header_validated',
            'completed',
        ]
        assert events[1]['event'] == 'header_validated'
        assert events[1]['is_valid'] is False
        missing_required = events[1]['missing_required']
        missing_primary = events[1]['missing_primary']
        unrecognized = events[1]['unrecognized']
        duplicated = events[1]['duplicated']
        assert isinstance(missing_required, list)
        assert isinstance(missing_primary, list)
        assert isinstance(unrecognized, list)
        assert isinstance(duplicated, list)
        assert '年龄' in missing_required
        assert missing_primary == []
        assert unrecognized == ['不存在的表头']
        assert duplicated == []
        assert events[2] == {
            'event': 'completed',
            'result': 'HEADER_INVALID',
            'success_count': 0,
            'fail_count': 0,
            'url': None,
        }

    async def test_import_data_reloads_workbook_state_on_each_run(self):
        alchemy = ExcelAlchemy(ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio)))

        first_result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_HEADER_INVALID_INPUT,
            output_excel_name='contract-first-header-invalid.xlsx',
        )
        second_result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_SIMPLE_IMPORT,
            output_excel_name='contract-second-success.xlsx',
        )

        assert first_result.result == ValidateResult.HEADER_INVALID
        assert second_result.result == ValidateResult.SUCCESS
        assert second_result.success_count == 1
        assert second_result.fail_count == 0
        assert second_result.url is None

    async def test_import_session_snapshot_tracks_completed_successful_run(self):
        alchemy = ExcelAlchemy(
            ImporterConfig.for_create(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio))
        )

        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_SIMPLE_IMPORT,
            output_excel_name='contract-session-success.xlsx',
        )

        snapshot = alchemy.last_import_snapshot

        assert result.result == ValidateResult.SUCCESS
        assert snapshot is not None
        assert snapshot.phase == ImportSessionPhase.COMPLETED
        assert snapshot.result == ValidateResult.SUCCESS
        assert snapshot.data_row_count == 1
        assert snapshot.processed_row_count == 1
        assert snapshot.success_count == 1
        assert snapshot.fail_count == 0
        assert not snapshot.rendered_result_workbook

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

    async def test_import_data_emits_expected_data_invalid_events(self):
        output_name = 'contract-data-invalid-events.xlsx'
        self.minio.storage.pop(output_name, None)
        alchemy = ExcelAlchemy(ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio)))
        events: list[dict[str, object]] = []

        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_SIMPLE_IMPORT_WITH_ERROR,
            output_excel_name=output_name,
            on_event=events.append,
        )

        assert result.result == ValidateResult.DATA_INVALID
        assert [event['event'] for event in events] == [
            'started',
            'header_validated',
            'row_processed',
            'completed',
        ]
        assert events[2] == {
            'event': 'row_processed',
            'processed_row_count': 1,
            'total_row_count': 1,
            'success_count': 0,
            'fail_count': 1,
        }
        assert events[3] == {
            'event': 'completed',
            'result': 'DATA_INVALID',
            'success_count': 0,
            'fail_count': 1,
            'url': f'excel/{output_name}',
        }

    async def test_import_data_emits_failed_event_for_unexpected_exception(self):
        class ExplodingReadStorage(InMemoryExcelStorage):
            def read_excel_table(self, input_excel_name: str, *, skiprows: int, sheet_name: str):
                raise RuntimeError('boom')

        source_bytes = self.minio.storage[FileRegistry.TEST_SIMPLE_IMPORT]['data'].getvalue()
        storage = ExplodingReadStorage(fixtures={FileRegistry.TEST_SIMPLE_IMPORT: source_bytes})
        alchemy = ExcelAlchemy(ImporterConfig.for_create(SimpleContractImporter, creator=creator, storage=storage))
        events: list[dict[str, object]] = []

        with self.assertRaisesRegex(RuntimeError, 'boom'):
            await alchemy.import_data(
                input_excel_name=FileRegistry.TEST_SIMPLE_IMPORT,
                output_excel_name='contract-failed-events.xlsx',
                on_event=events.append,
            )

        assert [event['event'] for event in events] == [
            'started',
            'failed',
        ]
        assert events[1] == {
            'event': 'failed',
            'error_type': 'RuntimeError',
            'error_message': 'boom',
        }

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

    async def test_import_result_workbook_marks_business_cell_errors_in_red(self):
        output_name = 'contract-data-invalid-business-cell.xlsx'
        self.minio.storage.pop(output_name, None)
        alchemy = ExcelAlchemy(
            ImporterConfig(SimpleContractImporter, creator=failing_creator, minio=cast(Minio, self.minio))
        )

        await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_SIMPLE_IMPORT,
            output_excel_name=output_name,
        )
        workbook = load_binary_excel_to_workbook(self.minio.storage[output_name]['data'].getvalue())
        worksheet = workbook['Sheet1']

        assert worksheet['B3'].value == '1、【姓名】Simulated failure'
        assert get_fill_color(worksheet['D3']) == BACKGROUND_ERROR_COLOR

    async def test_import_result_workbook_supports_english_display_locale(self):
        output_name = 'contract-data-invalid-english.xlsx'
        self.minio.storage.pop(output_name, None)
        alchemy = ExcelAlchemy(
            ImporterConfig(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio), locale='en')
        )

        await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_SIMPLE_IMPORT_WITH_ERROR,
            output_excel_name=output_name,
        )
        workbook = load_binary_excel_to_workbook(self.minio.storage[output_name]['data'].getvalue())
        worksheet = workbook['Sheet1']

        assert worksheet['A2'].value == 'Validation result\nDelete this column before re-uploading'
        assert worksheet['B2'].value == 'Failure reason\nDelete this column before re-uploading'
        assert worksheet['A3'].value == 'Validation failed'

    async def test_import_result_workbook_marks_merged_header_failures_on_the_correct_data_row(self):
        input_name = 'contract-merged-invalid-input.xlsx'
        output_name = 'contract-merged-invalid-output.xlsx'
        self.minio.storage.pop(output_name, None)

        source_content = self.minio.storage[FileRegistry.TEST_IMPORT_WITH_MERGE_HEADER]['data'].getvalue()
        workbook = load_workbook(io.BytesIO(source_content))
        worksheet = workbook['Sheet1']
        worksheet['E4'] = 'not-a-date'

        buffer = io.BytesIO()
        workbook.save(buffer)
        workbook.close()
        buffer.seek(0)
        self.minio.put_object(self.minio.bucket_name, input_name, buffer, len(buffer.getvalue()))

        alchemy = ExcelAlchemy(ImporterConfig(MergedContractImporter, creator=creator, minio=cast(Minio, self.minio)))

        result = await alchemy.import_data(
            input_excel_name=input_name,
            output_excel_name=output_name,
        )

        assert result.result == ValidateResult.DATA_INVALID

        result_workbook = load_binary_excel_to_workbook(self.minio.storage[output_name]['data'].getvalue())
        result_worksheet = result_workbook['Sheet1']

        assert result_worksheet['A4'].value == '校验不通过'
        assert isinstance(result_worksheet['B4'].value, str)
        assert '【出生日期】' in result_worksheet['B4'].value
