import pytest

from excelalchemy import ImportPreflightStatus, Label, ProgrammaticError, ValidateResult
from excelalchemy.results import (
    CellErrorMap,
    ImportPreflightResult,
    ImportResult,
    RowIssueMap,
    ValidateHeaderResult,
    build_frontend_remediation_payload,
)


class TestResultContracts:
    def test_validate_header_result_returns_true_when_required_fields_are_missing(self):
        result = ValidateHeaderResult(
            missing_required=[Label('年龄')],
            missing_primary=[],
            unrecognized=[],
            duplicated=[],
            is_valid=False,
        )

        assert result.is_required_missing is True

    def test_import_result_from_validate_header_result_maps_all_header_fields(self):
        validate_header = ValidateHeaderResult(
            missing_required=[Label('年龄')],
            missing_primary=[Label('邮箱')],
            unrecognized=[Label('未知列')],
            duplicated=[Label('姓名')],
            is_valid=False,
        )

        result = ImportResult.from_validate_header_result(validate_header)

        assert result.result == ValidateResult.HEADER_INVALID
        assert result.is_required_missing is True
        assert result.missing_required == [Label('年龄')]
        assert result.missing_primary == [Label('邮箱')]
        assert result.unrecognized == [Label('未知列')]
        assert result.duplicated == [Label('姓名')]
        assert result.url is None

    def test_import_result_returns_success_defaults_for_success_case(self):
        result = ImportResult(result=ValidateResult.SUCCESS, success_count=1)

        assert result.result == ValidateResult.SUCCESS
        assert result.success_count == 1
        assert result.fail_count == 0
        assert result.url is None
        assert result.missing_required == []
        assert result.missing_primary == []
        assert result.unrecognized == []
        assert result.duplicated == []
        assert result.is_success is True
        assert result.is_header_invalid is False
        assert result.is_data_invalid is False

    def test_import_result_to_api_payload_for_success_case(self):
        result = ImportResult(result=ValidateResult.SUCCESS, success_count=1, fail_count=0, url='memory://result.xlsx')

        assert result.to_api_payload() == {
            'result': 'SUCCESS',
            'is_success': True,
            'is_header_invalid': False,
            'is_data_invalid': False,
            'summary': {
                'success_count': 1,
                'fail_count': 0,
                'result_workbook_url': 'memory://result.xlsx',
            },
            'header_issues': {
                'is_required_missing': False,
                'missing_required': [],
                'missing_primary': [],
                'unrecognized': [],
                'duplicated': [],
            },
        }

    def test_import_result_status_helpers_remain_consistent(self):
        success = ImportResult(result=ValidateResult.SUCCESS)
        header_invalid = ImportResult(result=ValidateResult.HEADER_INVALID)
        data_invalid = ImportResult(result=ValidateResult.DATA_INVALID)

        assert success.is_success is True
        assert success.is_header_invalid is False
        assert success.is_data_invalid is False

        assert header_invalid.is_success is False
        assert header_invalid.is_header_invalid is True
        assert header_invalid.is_data_invalid is False

        assert data_invalid.is_success is False
        assert data_invalid.is_header_invalid is False
        assert data_invalid.is_data_invalid is True

    def test_import_result_to_api_payload_for_header_invalid_case(self):
        result = ImportResult(
            result=ValidateResult.HEADER_INVALID,
            is_required_missing=True,
            missing_required=[Label('年龄')],
            missing_primary=[Label('邮箱')],
            unrecognized=[Label('未知列')],
            duplicated=[Label('姓名')],
        )

        assert result.to_api_payload() == {
            'result': 'HEADER_INVALID',
            'is_success': False,
            'is_header_invalid': True,
            'is_data_invalid': False,
            'summary': {
                'success_count': 0,
                'fail_count': 0,
                'result_workbook_url': None,
            },
            'header_issues': {
                'is_required_missing': True,
                'missing_required': ['年龄'],
                'missing_primary': ['邮箱'],
                'unrecognized': ['未知列'],
                'duplicated': ['姓名'],
            },
        }

    def test_import_result_from_validate_header_result_rejects_valid_input(self):
        validate_header = ValidateHeaderResult(
            missing_required=[],
            missing_primary=[],
            unrecognized=[],
            duplicated=[],
            is_valid=True,
        )

        with pytest.raises(ProgrammaticError) as context:
            ImportResult.from_validate_header_result(validate_header)

        assert str(context.value) == 'ImportResult can only be built from an invalid header validation result'

    def test_import_preflight_result_from_validate_header_result_maps_invalid_header_fields(self):
        validate_header = ValidateHeaderResult(
            missing_required=[Label('年龄')],
            missing_primary=[Label('邮箱')],
            unrecognized=[Label('未知列')],
            duplicated=[Label('姓名')],
            is_valid=False,
        )

        result = ImportPreflightResult.from_validate_header_result(
            validate_header,
            sheet_name='Sheet1',
            sheet_exists=True,
            has_merged_header=False,
            estimated_row_count=3,
        )

        assert result.status == ImportPreflightStatus.HEADER_INVALID
        assert result.sheet_name == 'Sheet1'
        assert result.sheet_exists is True
        assert result.has_merged_header is False
        assert result.estimated_row_count == 3
        assert result.is_required_missing is True
        assert result.missing_required == [Label('年龄')]
        assert result.missing_primary == [Label('邮箱')]
        assert result.unrecognized == [Label('未知列')]
        assert result.duplicated == [Label('姓名')]

    def test_import_preflight_result_to_api_payload_for_valid_case(self):
        result = ImportPreflightResult(
            status=ImportPreflightStatus.VALID,
            sheet_name='Sheet1',
            sheet_exists=True,
            has_merged_header=False,
            estimated_row_count=1,
        )

        assert result.to_api_payload() == {
            'status': 'VALID',
            'is_valid': True,
            'is_header_invalid': False,
            'is_sheet_missing': False,
            'is_structure_invalid': False,
            'sheet': {
                'name': 'Sheet1',
                'exists': True,
                'has_merged_header': False,
            },
            'summary': {
                'estimated_row_count': 1,
                'structural_issue_codes': [],
            },
            'header_issues': {
                'is_required_missing': False,
                'missing_required': [],
                'missing_primary': [],
                'unrecognized': [],
                'duplicated': [],
            },
        }

    def test_import_preflight_result_status_helpers_remain_consistent(self):
        valid = ImportPreflightResult(status=ImportPreflightStatus.VALID, sheet_name='Sheet1', sheet_exists=True)
        header_invalid = ImportPreflightResult(
            status=ImportPreflightStatus.HEADER_INVALID,
            sheet_name='Sheet1',
            sheet_exists=True,
        )
        sheet_missing = ImportPreflightResult(
            status=ImportPreflightStatus.SHEET_MISSING,
            sheet_name='Sheet1',
            sheet_exists=False,
        )
        structure_invalid = ImportPreflightResult(
            status=ImportPreflightStatus.STRUCTURE_INVALID,
            sheet_name='Sheet1',
            sheet_exists=False,
        )

        assert valid.is_valid is True
        assert valid.is_header_invalid is False
        assert valid.is_sheet_missing is False
        assert valid.is_structure_invalid is False

        assert header_invalid.is_valid is False
        assert header_invalid.is_header_invalid is True
        assert header_invalid.is_sheet_missing is False
        assert header_invalid.is_structure_invalid is False

        assert sheet_missing.is_valid is False
        assert sheet_missing.is_header_invalid is False
        assert sheet_missing.is_sheet_missing is True
        assert sheet_missing.is_structure_invalid is False

        assert structure_invalid.is_valid is False
        assert structure_invalid.is_header_invalid is False
        assert structure_invalid.is_sheet_missing is False
        assert structure_invalid.is_structure_invalid is True

    def test_build_frontend_remediation_payload_for_success_case(self):
        result = ImportResult(result=ValidateResult.SUCCESS, success_count=1)

        payload = build_frontend_remediation_payload(
            result=result,
            cell_error_map=CellErrorMap(),
            row_error_map=RowIssueMap(),
        )

        assert payload == {
            'result': result.to_api_payload(),
            'remediation': {
                'needs_remediation': False,
                'affected_row_count': 0,
                'affected_field_count': 0,
                'affected_code_count': 0,
                'header_issue_count': 0,
                'result_workbook_available': False,
            },
            'by_field': [],
            'by_code': [],
            'items': [],
        }

    def test_build_frontend_remediation_payload_for_header_invalid_case(self):
        result = ImportResult(
            result=ValidateResult.HEADER_INVALID,
            is_required_missing=True,
            missing_required=[Label('年龄')],
            missing_primary=[Label('邮箱')],
            unrecognized=[Label('未知列')],
            duplicated=[Label('姓名')],
        )

        payload = build_frontend_remediation_payload(
            result=result,
            cell_error_map=CellErrorMap(),
            row_error_map=RowIssueMap(),
        )

        assert payload['result'] == result.to_api_payload()
        assert payload['remediation'] == {
            'needs_remediation': True,
            'affected_row_count': 0,
            'affected_field_count': 0,
            'affected_code_count': 0,
            'header_issue_count': 4,
            'result_workbook_available': False,
            'suggested_action': 'Correct the workbook headers to match the template and retry the import.',
            'fix_hint': 'Use a fresh template or align missing, duplicated, and unrecognized headers before retrying.',
        }
        assert payload['by_field'] == []
        assert payload['by_code'] == []
        assert payload['items'] == []

    def test_build_frontend_remediation_payload_does_not_change_existing_result_payloads(self):
        result = ImportResult(
            result=ValidateResult.DATA_INVALID,
            success_count=2,
            fail_count=1,
            url='memory://result.xlsx',
        )
        expected_result_payload = result.to_api_payload()
        cell_error_map = CellErrorMap()
        row_error_map = RowIssueMap()

        payload = build_frontend_remediation_payload(
            result=result,
            cell_error_map=cell_error_map,
            row_error_map=row_error_map,
        )

        assert result.to_api_payload() == expected_result_payload
        assert payload['result'] == expected_result_payload
        assert cell_error_map.to_api_payload() == {
            'error_count': 0,
            'items': [],
            'by_row': {},
            'facets': {
                'field_labels': [],
                'parent_labels': [],
                'unique_labels': [],
                'codes': [],
                'row_numbers_for_humans': [],
                'column_numbers_for_humans': [],
            },
            'grouped': {
                'messages_by_field': {},
                'messages_by_row': {},
                'messages_by_code': {},
            },
            'summary': {
                'by_field': [],
                'by_row': [],
                'by_code': [],
            },
        }
        assert row_error_map.to_api_payload() == {
            'error_count': 0,
            'items': [],
            'by_row': {},
            'facets': {
                'field_labels': [],
                'parent_labels': [],
                'unique_labels': [],
                'codes': [],
                'row_numbers_for_humans': [],
            },
            'grouped': {
                'messages_by_row': {},
                'messages_by_code': {},
            },
            'summary': {
                'by_row': [],
                'by_code': [],
            },
        }
