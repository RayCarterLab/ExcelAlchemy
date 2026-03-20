from typing import cast

from pydantic import BaseModel

from excelalchemy import FieldMeta
from excelalchemy import MultiStaff
from excelalchemy import Option
from excelalchemy import OptionId
from tests.support import BaseTestCase


class TestMultiStaffValueType(BaseTestCase):
    async def test_comment_describes_multi_staff_input(self):
        class Importer(BaseModel):
            staff: MultiStaff = FieldMeta(
                label='员工',
            )

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(MultiStaff, field.value_type)

        assert field.value_type.comment(field) == '必填性：必填\n提示：请输入人员姓名和工号，如“张三/001”，多选时，选项之间用“、”连接'

    async def test_serialize_splits_multi_staff_input_into_values(self):
        class Importer(BaseModel):
            staff: MultiStaff = FieldMeta(
                label='员工',
                options=[
                    Option(id=OptionId(1), name='张三/001'),
                    Option(id=OptionId(2), name='李四/002'),
                ],
            )

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(MultiStaff, field.value_type)

        assert field.value_type.serialize('张三/001、李四/002', field) == ['张三/001、李四/002']
        assert field.value_type.serialize('1,2', field) == ['1,2']

    async def test_deserialize_maps_staff_ids_to_display_names(self):
        class Importer(BaseModel):
            staff: MultiStaff = FieldMeta(
                label='员工',
                options=[
                    Option(id=OptionId(1), name='张三/001'),
                    Option(id=OptionId(2), name='李四/002'),
                ],
            )

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(MultiStaff, field.value_type)

        assert field.value_type.deserialize('张三/001、李四/002', field) == '张三/001、李四/002'
        assert field.value_type.deserialize([1, 2], field) == '张三/001，李四/002'
