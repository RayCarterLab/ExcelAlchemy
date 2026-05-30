from typing import Annotated, cast

from pydantic import BaseModel

from excelalchemy import (
    ExcelColumn,
    Option,
    OptionId,
    ProgrammaticError,
    SingleChoiceCodec,
)
from excelalchemy.codecs.choice import SingleChoiceFieldCodec
from excelalchemy.primitives.constants import MULTI_CHECKBOX_SEPARATOR
from tests.support import BaseTestCase


class TestSingleChoiceFieldCodec(BaseTestCase):
    async def test_comment_describes_single_select_behavior(self):
        class Importer(BaseModel):
            radio: Annotated[
                str,
                ExcelColumn(
                    codec=SingleChoiceCodec(),
                    label='单选框组',
                    order=1,
                    options=[
                        Option(id=OptionId(1), name='选项1'),
                        Option(id=OptionId(2), name='选项2'),
                    ],
                ),
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(SingleChoiceFieldCodec, field.excel_codec)

        assert field.excel_codec.build_comment(field) == '必填性：必填\n选项：选项1，选项2\n单/多选：单选\n'

        field.options = None
        assert field.excel_codec.build_comment(field) == '必填性：必填\n\n单/多选：单选\n'

    async def test_serialize_stringifies_option_values(self):
        class Importer(BaseModel):
            radio: Annotated[
                str,
                ExcelColumn(
                    codec=SingleChoiceCodec(),
                    label='单选框组',
                    order=1,
                    options=[
                        Option(id=OptionId(1), name='选项1'),
                        Option(id=OptionId(2), name='选项2'),
                    ],
                ),
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(SingleChoiceFieldCodec, field.excel_codec)

        assert field.excel_codec.parse_input(1, field) == '1'
        assert field.excel_codec.parse_input(2, field) == '2'

    async def test_deserialize_maps_option_ids_to_display_names(self):
        class Importer(BaseModel):
            radio: Annotated[
                str,
                ExcelColumn(
                    codec=SingleChoiceCodec(),
                    label='单选框组',
                    order=1,
                    options=[
                        Option(id=OptionId(1), name='选项1'),
                        Option(id=OptionId(2), name='选项2'),
                    ],
                ),
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(SingleChoiceFieldCodec, field.excel_codec)

        assert field.excel_codec.format_display_value('1', field) == '选项1'
        assert field.excel_codec.format_display_value('2', field) == '选项2'
        assert field.excel_codec.format_display_value('3', field) == '3'

        assert field.excel_codec.format_display_value('选项1', field) == '选项1'
        assert field.excel_codec.format_display_value('选项2', field) == '选项2'
        assert field.excel_codec.format_display_value('选项3', field) == '选项3'

    async def test_validate_accepts_known_options_and_rejects_invalid_inputs(self):
        class Importer(BaseModel):
            radio: Annotated[
                str,
                ExcelColumn(
                    codec=SingleChoiceCodec(),
                    label='单选框组',
                    order=1,
                    options=[
                        Option(id=OptionId(1), name='选项1'),
                        Option(id=OptionId(2), name='选项2'),
                    ],
                ),
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(SingleChoiceFieldCodec, field.excel_codec)

        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, 'ddd', field)
        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, '3', field)
        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, '选项3', field)

        assert field.excel_codec.normalize_import_value('1', field) == '1'
        assert field.excel_codec.normalize_import_value('2', field) == '2'
        assert field.excel_codec.normalize_import_value('选项1', field) == '1'
        assert field.excel_codec.normalize_import_value('选项2', field) == '2'

        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, '选项3', field)
        with self.assertRaises(ValueError) as context:
            field.excel_codec.normalize_import_value(f'3{MULTI_CHECKBOX_SEPARATOR}', field)
        assert str(context.exception) == 'Select one of the configured options. Valid values include: 选项1，选项2'

        field.options = None
        self.assertRaises(ProgrammaticError, field.excel_codec.normalize_import_value, '1', field)
