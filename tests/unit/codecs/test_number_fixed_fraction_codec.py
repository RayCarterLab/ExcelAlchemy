from typing import Annotated, cast

from pydantic import BaseModel

from excelalchemy import ExcelColumn, NumberCodec
from excelalchemy.codecs.number import NumberFieldCodec
from tests.support import BaseTestCase


class TestNumberFixedFractionCodec(BaseTestCase):
    async def test_validate_normalizes_fixed_fraction_inputs_and_rejects_invalid_values(self):
        class Importer(BaseModel):
            money: Annotated[float, ExcelColumn(codec=NumberCodec(fraction_digits=2), label='金额', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        field.excel_codec = cast(NumberFieldCodec, field.excel_codec)
        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, 'ddd', field)

        assert field.excel_codec.normalize_import_value(1.23, field) == 1.23
        assert field.excel_codec.normalize_import_value(1.234, field) == 1.23
        assert field.fraction_digits == 2

    async def test_number_comment_uses_configured_fraction_digits(self):
        class Importer(BaseModel):
            money: Annotated[float, ExcelColumn(codec=NumberCodec(fraction_digits=2), label='金额', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        assert (
            field.excel_codec.build_comment(field)
            == '必填性：必填\n格式：数值\n小数位数：2\n可输入范围：无限制\n单位：无'
        )
        assert field.fraction_digits == 2
