from decimal import Decimal
from typing import Annotated, cast

from pydantic import BaseModel

from excelalchemy import ExcelColumn
from excelalchemy.codecs.number import Number
from tests.support import BaseTestCase


class TestNumberValueType(BaseTestCase):
    async def test_comment_reflects_fraction_digits_and_range_constraints(self):
        class Importer(BaseModel):
            number: Annotated[float, ExcelColumn(label='数字', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        assert (
            field.excel_codec.build_comment(field)
            == '必填性：必填\n格式：数值\n小数位数：0\n可输入范围：无限制\n单位：无'
        )
        field.fraction_digits = 2
        assert (
            field.excel_codec.build_comment(field)
            == '必填性：必填\n格式：数值\n小数位数：2\n可输入范围：无限制\n单位：无'
        )

        field.importer_ge = 1
        field.importer_le = 10
        assert (
            field.excel_codec.build_comment(field)
            == '必填性：必填\n格式：数值\n小数位数：2\n可输入范围：1～10\n单位：无'
        )

        field.importer_ge = None
        assert (
            field.excel_codec.build_comment(field)
            == '必填性：必填\n格式：数值\n小数位数：2\n可输入范围：≤ 10\n单位：无'
        )

        field.importer_le = None
        field.importer_ge = 1
        assert (
            field.excel_codec.build_comment(field) == '必填性：必填\n格式：数值\n小数位数：2\n可输入范围：≥ 1\n单位：无'
        )

    async def test_serialize_preserves_numeric_inputs_before_validation(self):
        class Importer(BaseModel):
            number: Annotated[float, ExcelColumn(label='数字', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(Number, field.excel_codec)

        assert field.excel_codec.parse_input(1.23, field) == 1.23
        assert field.excel_codec.parse_input(1.234, field) == 1.234

        field.fraction_digits = 2
        assert field.excel_codec.parse_input(1.234, field) == 1.234
        assert field.excel_codec.parse_input(1.235, field) == 1.235
        assert field.excel_codec.parse_input(1.236, field) == 1.236
        assert field.excel_codec.parse_input(1.2345, field) == 1.2345

    async def test_deserialize_stringifies_numeric_inputs_for_excel_display(self):
        class Importer(BaseModel):
            number: Annotated[float, ExcelColumn(label='数字', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(Number, field.excel_codec)

        assert field.excel_codec.format_display_value(1.23, field) == '1.23'
        assert field.excel_codec.format_display_value(1.234, field) == '1.234'
        assert field.excel_codec.format_display_value(Decimal('1.234'), field) == '1.234'

        field.fraction_digits = 2
        assert field.excel_codec.format_display_value(1.234, field) == '1.234'
        assert field.excel_codec.format_display_value(1.235, field) == '1.235'
        assert field.excel_codec.format_display_value(1.236, field) == '1.236'
        assert field.excel_codec.format_display_value(1.2345, field) == '1.2345'

    async def test_validate_enforces_numeric_ranges_and_precision(self):
        class Importer(BaseModel):
            number: Annotated[float, ExcelColumn(label='数字', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(Number, field.excel_codec)

        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, 'ddd', field)
        assert field.excel_codec.normalize_import_value(1.23, field) == 1.23
        assert field.excel_codec.normalize_import_value(1.234, field) == 1.234
        assert field.excel_codec.normalize_import_value(Decimal('1.234'), field) == 1.234

        field.fraction_digits = 2
        assert field.excel_codec.normalize_import_value(1.234, field) == 1.23
        assert field.excel_codec.normalize_import_value(1.235, field) == 1.23
        assert field.excel_codec.normalize_import_value(1.236, field) == 1.23
        assert field.excel_codec.normalize_import_value(1.2345, field) == 1.23

        field.importer_ge = 1
        field.importer_le = 2
        assert field.excel_codec.normalize_import_value(1, field) == 1
        assert field.excel_codec.normalize_import_value(2, field) == 2
        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, 0, field)
        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, 3, field)

        field.importer_ge = None
        field.importer_le = 2
        assert field.excel_codec.normalize_import_value(1, field) == 1
        assert field.excel_codec.normalize_import_value(2, field) == 2
        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, 3, field)

        field.importer_ge = 1
        field.importer_le = None
        assert field.excel_codec.normalize_import_value(1, field) == 1
        assert field.excel_codec.normalize_import_value(2, field) == 2
        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, 0, field)
