from typing import cast

from excelalchemy import FieldMeta, MultiCheckbox, OptionId, ProgrammaticError
from excelalchemy.const import MULTI_CHECKBOX_SEPARATOR, Option
from pydantic import BaseModel

from tests.support import BaseTestCase


class TestMultiCheckboxValueType(BaseTestCase):
    async def test_comment_describes_multi_select_behavior(self):
        class Importer(BaseModel):
            multi_checkbox: MultiCheckbox = FieldMeta(label='多选框', order=1)

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(MultiCheckbox, field.value_type)

        assert field.value_type.comment(field) == '必填性：必填\n\n单/多选：多选\n'

    async def test_serialize_splits_multi_select_inputs_into_lists(self):
        class Importer(BaseModel):
            multi_checkbox: MultiCheckbox = FieldMeta(label='多选框', order=1)

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(MultiCheckbox, field.value_type)

        assert field.value_type.serialize(['a', 'b'], field) == ['a', 'b']
        assert field.value_type.serialize(f'a{MULTI_CHECKBOX_SEPARATOR}b', field) == ['a', 'b']
        assert field.value_type.serialize('a', field) == ['a']
        assert field.value_type.serialize(None, field) is None
        assert field.value_type.serialize('', field) == ['']

    async def test_validate_rejects_unknown_or_duplicate_multi_select_options(self):
        class Importer(BaseModel):
            multi_checkbox: MultiCheckbox = FieldMeta(
                label='多选框',
                order=1,
                options=[
                    Option(id=OptionId('a'), name='a'),
                    Option(id=OptionId('b'), name='b'),
                ],
            )

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(MultiCheckbox, field.value_type)

        self.assertRaises(ValueError, field.value_type.__validate__, None, field)
        self.assertRaises(ValueError, field.value_type.__validate__, 'ddd', field)
        assert field.value_type.__validate__(['a', 'b'], field) == ['a', 'b']
        self.assertRaises(ValueError, field.value_type.__validate__, ['a', 'b', 'c'], field)
        self.assertRaises(ValueError, field.value_type.__validate__, ['a', 'b', 'c', 'c'], field)
        self.assertRaises(ValueError, field.value_type.__validate__, ['a', 'b', 'c', ''], field)

        field.options = None
        self.assertRaises(ProgrammaticError, field.value_type.__validate__, ['a', 'b'], field)

    async def test_deserialize_maps_multi_select_option_ids_to_display_names(self):
        class Importer(BaseModel):
            multi_checkbox: MultiCheckbox = FieldMeta(
                label='多选框',
                order=1,
                options=[
                    Option(id=OptionId('age'), name='年龄'),
                    Option(id=OptionId('sex'), name='性别'),
                ],
            )

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(MultiCheckbox, field.value_type)

        assert field.value_type.deserialize([OptionId('age'), OptionId('性别')], field) == '年龄，性别'
        assert field.value_type.deserialize(f'a{MULTI_CHECKBOX_SEPARATOR}b', field) == 'a，b'
        assert field.value_type.deserialize('a', field) == 'a'
        assert field.value_type.deserialize(None, field) == ''
        assert field.value_type.deserialize('', field) == ''
