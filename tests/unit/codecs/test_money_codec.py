from typing import cast

from pydantic import BaseModel

from excelalchemy import FieldMeta, Money
from tests.support import BaseTestCase


class TestMoneyValueType(BaseTestCase):
    async def test_validate_normalizes_money_inputs_and_rejects_invalid_values(self):
        class Importer(BaseModel):
            money: Money = FieldMeta(label='金额', order=1)

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        field.value_type = cast(Money, field.value_type)
        self.assertRaises(ValueError, field.value_type.__validate__, 'ddd', field)

        assert field.value_type.__validate__(1.23, field) == 1.23
        assert field.value_type.__validate__(1.234, field) == 1.23
        assert field.fraction_digits is None

    async def test_money_comment_uses_fixed_two_fraction_digits_without_mutating_field_metadata(self):
        class Importer(BaseModel):
            money: Money = FieldMeta(label='金额', order=1)

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        assert field.value_type.comment(field) == '必填性：必填\n格式：数值\n小数位数：2\n可输入范围：无限制\n单位：无'
        assert field.fraction_digits is None
