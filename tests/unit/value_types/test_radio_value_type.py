from typing import cast

from excelalchemy import FieldMeta, Option, OptionId, ProgrammaticError, Radio
from excelalchemy.const import MULTI_CHECKBOX_SEPARATOR
from pydantic import BaseModel

from tests.support import BaseTestCase


class TestRadioValueType(BaseTestCase):
    async def test_comment_describes_single_select_behavior(self):
        class Importer(BaseModel):
            radio: Radio = FieldMeta(
                label='单选框组',
                order=1,
                options=[
                    Option(id=OptionId(1), name='选项1'),
                    Option(id=OptionId(2), name='选项2'),
                ],
            )

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(Radio, field.value_type)

        assert field.value_type.comment(field) == '必填性：必填\n选项：选项1，选项2\n单/多选：单选\n'

        field.options = None
        assert field.value_type.comment(field) == '必填性：必填\n\n单/多选：单选\n'

    async def test_serialize_stringifies_option_values(self):
        class Importer(BaseModel):
            radio: Radio = FieldMeta(
                label='单选框组',
                order=1,
                options=[
                    Option(id=OptionId(1), name='选项1'),
                    Option(id=OptionId(2), name='选项2'),
                ],
            )

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(Radio, field.value_type)

        assert field.value_type.serialize(1, field) == '1'
        assert field.value_type.serialize(2, field) == '2'

    async def test_deserialize_maps_option_ids_to_display_names(self):
        class Importer(BaseModel):
            radio: Radio = FieldMeta(
                label='单选框组',
                order=1,
                options=[
                    Option(id=OptionId(1), name='选项1'),
                    Option(id=OptionId(2), name='选项2'),
                ],
            )

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(Radio, field.value_type)

        assert field.value_type.deserialize('1', field) == '选项1'
        assert field.value_type.deserialize('2', field) == '选项2'
        assert field.value_type.deserialize('3', field) == '3'

        assert field.value_type.deserialize('选项1', field) == '选项1'
        assert field.value_type.deserialize('选项2', field) == '选项2'
        assert field.value_type.deserialize('选项3', field) == '选项3'

    async def test_validate_accepts_known_options_and_rejects_invalid_inputs(self):
        class Importer(BaseModel):
            radio: Radio = FieldMeta(
                label='单选框组',
                order=1,
                options=[
                    Option(id=OptionId(1), name='选项1'),
                    Option(id=OptionId(2), name='选项2'),
                ],
            )

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(Radio, field.value_type)

        self.assertRaises(ValueError, field.value_type.__validate__, 'ddd', field)
        self.assertRaises(ValueError, field.value_type.__validate__, '3', field)
        self.assertRaises(ValueError, field.value_type.__validate__, '选项3', field)

        assert field.value_type.__validate__('1', field) == '1'
        assert field.value_type.__validate__('2', field) == '2'
        assert field.value_type.__validate__('选项1', field) == '1'
        assert field.value_type.__validate__('选项2', field) == '2'

        self.assertRaises(ValueError, field.value_type.__validate__, '选项3', field)
        self.assertRaises(ValueError, field.value_type.__validate__, f'3{MULTI_CHECKBOX_SEPARATOR}', field)

        field.options = None
        self.assertRaises(ProgrammaticError, field.value_type.__validate__, '1', field)
