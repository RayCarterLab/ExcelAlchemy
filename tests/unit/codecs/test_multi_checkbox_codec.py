from typing import Annotated, cast

from pydantic import BaseModel

from excelalchemy import (
    ExcelColumn,
    MultiChoiceCodec,
    Option,
    OptionId,
    ProgrammaticError,
)
from excelalchemy.codecs.multi_checkbox import MultiCheckbox
from excelalchemy.primitives.constants import MULTI_CHECKBOX_SEPARATOR
from tests.support import BaseTestCase


class TestMultiCheckboxValueType(BaseTestCase):
    async def test_comment_describes_multi_select_behavior(self):
        class Importer(BaseModel):
            multi_checkbox: Annotated[list[str], ExcelColumn(codec=MultiChoiceCodec(), label='多选框', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(MultiCheckbox, field.excel_codec)

        assert field.excel_codec.build_comment(field) == '必填性：必填\n\n单/多选：多选\n'

    async def test_serialize_splits_multi_select_inputs_into_lists(self):
        class Importer(BaseModel):
            multi_checkbox: Annotated[list[str], ExcelColumn(codec=MultiChoiceCodec(), label='多选框', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(MultiCheckbox, field.excel_codec)

        assert field.excel_codec.parse_input(['a', 'b'], field) == ['a', 'b']
        assert field.excel_codec.parse_input(f'a{MULTI_CHECKBOX_SEPARATOR}b', field) == ['a', 'b']
        assert field.excel_codec.parse_input('a', field) == ['a']
        assert field.excel_codec.parse_input(None, field) is None
        assert field.excel_codec.parse_input('', field) == ['']

    async def test_validate_rejects_unknown_or_duplicate_multi_select_options(self):
        class Importer(BaseModel):
            multi_checkbox: Annotated[
                list[str],
                ExcelColumn(
                    codec=MultiChoiceCodec(),
                    label='多选框',
                    order=1,
                    options=[
                        Option(id=OptionId('a'), name='a'),
                        Option(id=OptionId('b'), name='b'),
                    ],
                ),
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(MultiCheckbox, field.excel_codec)

        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, None, field)
        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, 'ddd', field)
        assert field.excel_codec.normalize_import_value(['a', 'b'], field) == ['a', 'b']
        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, ['a', 'b', 'c'], field)
        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, ['a', 'b', 'c', 'c'], field)
        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, ['a', 'b', 'c', ''], field)

        field.options = None
        self.assertRaises(ProgrammaticError, field.excel_codec.normalize_import_value, ['a', 'b'], field)

    async def test_deserialize_maps_multi_select_option_ids_to_display_names(self):
        class Importer(BaseModel):
            multi_checkbox: Annotated[
                list[str],
                ExcelColumn(
                    codec=MultiChoiceCodec(),
                    label='多选框',
                    order=1,
                    options=[
                        Option(id=OptionId('age'), name='年龄'),
                        Option(id=OptionId('sex'), name='性别'),
                    ],
                ),
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(MultiCheckbox, field.excel_codec)

        assert field.excel_codec.format_display_value([OptionId('age'), OptionId('性别')], field) == '年龄，性别'
        assert field.excel_codec.format_display_value(f'a{MULTI_CHECKBOX_SEPARATOR}b', field) == 'a，b'
        assert field.excel_codec.format_display_value('a', field) == 'a'
        assert field.excel_codec.format_display_value(None, field) == ''
        assert field.excel_codec.format_display_value('', field) == ''
