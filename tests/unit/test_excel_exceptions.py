from excelalchemy import ExcelCellError, Label
from excelalchemy.exc import ExcelRowError
from tests.support import BaseTestCase


class TestExcelExceptions(BaseTestCase):
    async def test_excel_cell_errors_compare_equal_when_message_and_label_match(self):
        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        exc2 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        assert exc1 == exc2

        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        exc2 = ExcelCellError(label=Label('邮箱1'), message='Enter a valid email address')

        assert exc1 != exc2

    async def test_excel_cell_error_repr_includes_label_and_message(self):
        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        assert repr(exc1) == "ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')"

    async def test_excel_cell_error_str_prefixes_label(self):
        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        assert str(exc1) == '【邮箱】Enter a valid email address'

    async def test_excel_cell_error_requires_non_empty_label(self):
        self.assertRaises(ValueError, ExcelCellError, label=Label(''), message='Enter a valid email address')

    async def test_excel_cell_error_builds_unique_label_from_parent_when_present(self):
        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        assert exc1.unique_label == '邮箱'

        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address', parent_label=Label('父'))
        assert exc1.unique_label == '父·邮箱'

    async def test_excel_cell_error_supports_equality_and_inequality_operations(self):
        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        exc2 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        assert exc1 == exc2

        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        exc2 = ExcelCellError(label=Label('邮箱1'), message='Enter a valid email address')
        assert exc1 != exc2

        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        other = 'other'

        assert exc1 != other
        assert other != exc1

    async def test_excel_row_error_preserves_message_in_string_representations(self):
        exc1 = ExcelRowError(message='Excel row import error')
        assert exc1.message == 'Excel row import error'

        exc1 = ExcelRowError(message='Enter a valid email address')
        assert exc1.message == 'Enter a valid email address'

        exc1 = ExcelRowError(message='Enter a valid email address')
        assert str(exc1) == 'Enter a valid email address'

        exc1 = ExcelRowError(message='Enter a valid email address')
        assert repr(exc1) == "ExcelRowError(message='Enter a valid email address')"
