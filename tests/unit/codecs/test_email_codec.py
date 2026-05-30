from typing import Annotated

from pydantic import BaseModel

from excelalchemy import (
    ColumnIndex,
    EmailCodec,
    ExcelCellError,
    ExcelColumn,
    Label,
    RowIndex,
    ValidateResult,
)
from tests.support import BaseTestCase, FileRegistry


class TestEmailValueType(BaseTestCase):
    async def test_import_rejects_invalid_email_value(self):
        class Importer(BaseModel):
            email: Annotated[str, ExcelColumn(codec=EmailCodec(), label='邮箱', order=1)]

        alchemy = self.build_alchemy(Importer)
        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_EMAIL_WRONG_FORMAT, output_excel_name='result.xlsx'
        )
        assert result.result == ValidateResult.DATA_INVALID, '导入失败'
        assert result.fail_count == 1
        row, col, first_error = RowIndex(0), ColumnIndex(2), 0
        assert alchemy.cell_error_map[row][col][first_error] == ExcelCellError(
            label=Label('邮箱'), message='Enter a valid email address, such as name@example.com'
        )

    async def test_import_accepts_valid_email_value(self):
        class Importer(BaseModel):
            email: Annotated[str, ExcelColumn(codec=EmailCodec(), label='邮箱', order=1)]

        alchemy = self.build_alchemy(Importer)
        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_EMAIL_CORRECT_FORMAT, output_excel_name='result.xlsx'
        )
        assert result.result == ValidateResult.SUCCESS, '导入失败'
        assert result.fail_count == 0
        assert result.success_count == 1

    async def test_validate_accepts_well_formed_email_addresses(self):
        class Importer(BaseModel):
            email: Annotated[str, ExcelColumn(codec=EmailCodec(), label='邮箱', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, 'ddd', field)
