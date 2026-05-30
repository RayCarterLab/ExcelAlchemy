from typing import Annotated, cast

from pydantic import BaseModel

from excelalchemy import (
    ExcelColumn,
    MoneyCodec,
)
from excelalchemy.codecs.money import Money
from tests.support import BaseTestCase


class TestMoneyValueType(BaseTestCase):
    async def test_validate_normalizes_money_inputs_and_rejects_invalid_values(self):
        class Importer(BaseModel):
            money: Annotated[float, ExcelColumn(codec=MoneyCodec(), label='金额', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        field.excel_codec = cast(Money, field.excel_codec)
        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, 'ddd', field)

        assert field.excel_codec.normalize_import_value(1.23, field) == 1.23
        assert field.excel_codec.normalize_import_value(1.234, field) == 1.23
        assert field.fraction_digits is None

    async def test_money_comment_uses_fixed_two_fraction_digits_without_mutating_field_metadata(self):
        class Importer(BaseModel):
            money: Annotated[float, ExcelColumn(codec=MoneyCodec(), label='金额', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        assert (
            field.excel_codec.build_comment(field)
            == '必填性：必填\n格式：数值\n小数位数：2\n可输入范围：无限制\n单位：无'
        )
        assert field.fraction_digits is None
