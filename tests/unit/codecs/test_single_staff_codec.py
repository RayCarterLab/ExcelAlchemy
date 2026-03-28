from typing import cast

from pydantic import BaseModel

from excelalchemy import FieldMeta, Option, OptionId, SingleStaff
from tests.support import BaseTestCase


class TestSingleStaffValueType(BaseTestCase):
    async def test_comment_describes_single_staff_input(self):
        class Importer(BaseModel):
            staff: SingleStaff = FieldMeta(label='员工', comment='员工')

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(SingleStaff, field.value_type)

        assert field.value_type.comment(field) == '必填性：必填 \n提示：请输入人员姓名和工号，如“张三/001”'

    async def test_serialize_strips_single_staff_input(self):
        class Importer(BaseModel):
            staff: SingleStaff = FieldMeta(
                label='员工',
                comment='员工',
                options=[
                    Option(id=OptionId(1), name='张三/001'),
                ],
            )

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(SingleStaff, field.value_type)

        assert field.value_type.serialize('张三/001', field) == '张三/001'
        assert field.value_type.serialize(OptionId(1), field) == '1'

    async def test_deserialize_maps_single_staff_id_to_display_name(self):
        class Importer(BaseModel):
            staff: SingleStaff = FieldMeta(
                label='员工',
                comment='员工',
                options=[
                    Option(id=OptionId(1), name='张三/001'),
                ],
            )

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(SingleStaff, field.value_type)

        assert field.value_type.deserialize('张三/001', field) == '张三/001'
        assert field.value_type.deserialize('1', field) == '张三/001'

    async def test_validate_accepts_known_staff_options_and_rejects_invalid_inputs(self):
        class Importer(BaseModel):
            staff: SingleStaff = FieldMeta(
                label='员工',
                comment='员工',
                options=[
                    Option(id=OptionId(1), name='张三/001'),
                ],
            )

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(SingleStaff, field.value_type)

        assert field.value_type.__validate__('张三/001', field) == '1'
        assert field.value_type.__validate__('1', field) == '1'
