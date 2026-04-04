import pytest

from excelalchemy import Label, ProgrammaticError, ValidateResult
from excelalchemy.results import ImportResult, ValidateHeaderResult


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
