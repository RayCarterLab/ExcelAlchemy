from pydantic import BaseModel

from excelalchemy import ColumnIndex
from excelalchemy import Email
from excelalchemy import ExcelCellError
from excelalchemy import FieldMeta
from excelalchemy import Label
from excelalchemy import RowIndex
from excelalchemy import ValidateResult
from tests.support import BaseTestCase
from tests.support import FileRegistry


class TestEmailValueType(BaseTestCase):
    async def test_import_rejects_invalid_email_value(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(label='邮箱', order=1)

        alchemy = self.build_alchemy(Importer)
        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_EMAIL_WRONG_FORMAT, output_excel_name='result.xlsx'
        )
        assert result.result == ValidateResult.DATA_INVALID, '导入失败'
        assert result.fail_count == 1
        row, col, first_error = RowIndex(0), ColumnIndex(2), 0
        assert alchemy.cell_errors[row][col][first_error] == ExcelCellError(label=Label('邮箱'), message='请输入正确的邮箱')

    async def test_import_accepts_valid_email_value(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(label='邮箱', order=1)

        alchemy = self.build_alchemy(Importer)
        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_EMAIL_CORRECT_FORMAT, output_excel_name='result.xlsx'
        )
        assert result.result == ValidateResult.SUCCESS, '导入失败'
        assert result.fail_count == 0
        assert result.success_count == 1

    async def test_validate_accepts_well_formed_email_addresses(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(label='邮箱', order=1)

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        self.assertRaises(ValueError, field.value_type.__validate__, 'ddd', field)
