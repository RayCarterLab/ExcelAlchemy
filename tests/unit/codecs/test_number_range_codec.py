from typing import Annotated, cast

from pydantic import BaseModel

from excelalchemy import (
    ExcelColumn,
    NumberRangeCodec,
)
from excelalchemy.codecs.number_range import NumberRangeFieldCodec, NumberRangeValue
from tests.support import BaseTestCase


class TestNumberRangeValueType(BaseTestCase):
    def test_comment_reuses_number_comment_contract(self):
        class Importer(BaseModel):
            number: Annotated[dict[str, object], ExcelColumn(codec=NumberRangeCodec(), label='数字', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(NumberRangeFieldCodec, field.excel_codec)

        assert (
            field.excel_codec.build_comment(field)
            == '必填性：必填\n格式：数值\n小数位数：0\n可输入范围：无限制\n单位：无'
        )
        assert len(field.excel_codec.column_items()) == 2

    async def test_serialize_parses_number_range_inputs(self):
        class Importer(BaseModel):
            number: Annotated[dict[str, object], ExcelColumn(codec=NumberRangeCodec(), label='数字', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(NumberRangeFieldCodec, field.excel_codec)

        assert field.excel_codec.parse_input(1.23, field) == 1.23
        assert field.excel_codec.parse_input(
            {
                'start': 1.23,
                'end': 1.23,
            },
            field,
        ) == {
            'start': 1.23,
            'end': 1.23,
        }
        assert field.excel_codec.parse_input(
            NumberRangeValue(start=1.23, end=1.23),
            field,
        ) == {
            'start': 1.23,
            'end': 1.23,
        }

    async def test_deserialize_stringifies_number_range_boundaries(self):
        class Importer(BaseModel):
            number: Annotated[dict[str, object], ExcelColumn(codec=NumberRangeCodec(), label='数字', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(NumberRangeFieldCodec, field.excel_codec)

        assert field.excel_codec.format_display_value(1.23, field) == '1.23'

        field.fraction_digits = 2
        assert field.excel_codec.format_display_value(1.2345, field) == '1.23'

    async def test_validate_enforces_number_range_order_and_constraints(self):
        class Importer(BaseModel):
            number: Annotated[dict[str, object], ExcelColumn(codec=NumberRangeCodec(), label='数字', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(NumberRangeFieldCodec, field.excel_codec)

        assert field.excel_codec.normalize_import_value(
            {
                'start': 1.23,
                'end': 1.23,
            },
            field,
        ) == {'start': 1.23, 'end': 1.23}

        field.fraction_digits = 2
        assert field.excel_codec.normalize_import_value(
            {
                'start': 1.2346,
                'end': 1.23456,
            },
            field,
        ) == {'start': 1.23, 'end': 1.23}

        field.fraction_digits = 0
        assert field.excel_codec.normalize_import_value(
            NumberRangeValue(start=1.23, end=1.23),
            field,
        ) == {'start': 1, 'end': 1}
