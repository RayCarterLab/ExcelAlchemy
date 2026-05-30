from typing import Annotated, cast

from pydantic import BaseModel

from excelalchemy import (
    ExcelColumn,
    MultiChoiceCodec,
    Option,
    OptionId,
)
from excelalchemy.codecs.choice import MultiChoiceFieldCodec
from excelalchemy.messages import MessageKey
from excelalchemy.messages import display_message as dmsg
from tests.support import BaseTestCase

MULTI_STAFF_CODEC = MultiChoiceCodec(
    entity_name_plural='staff members',
    hint=dmsg(MessageKey.MULTI_STAFF_HINT),
    include_options_in_comment=False,
    include_mode_in_comment=False,
    separator='、',
)


class TestMultiChoiceStaffConfig(BaseTestCase):
    async def test_comment_describes_multi_staff_input(self):
        class Importer(BaseModel):
            staff: Annotated[list[str], ExcelColumn(codec=MULTI_STAFF_CODEC, label='员工')]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(MultiChoiceFieldCodec, field.excel_codec)

        assert (
            field.excel_codec.build_comment(field)
            == '必填性：必填\n提示：请输入人员姓名和工号，如“张三/001”，多选时，选项之间用“、”连接'
        )

    async def test_serialize_splits_multi_staff_input_into_values(self):
        class Importer(BaseModel):
            staff: Annotated[
                list[str],
                ExcelColumn(
                    codec=MULTI_STAFF_CODEC,
                    label='员工',
                    options=[
                        Option(id=OptionId(1), name='张三/001'),
                        Option(id=OptionId(2), name='李四/002'),
                    ],
                ),
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(MultiChoiceFieldCodec, field.excel_codec)

        assert field.excel_codec.parse_input('张三/001、李四/002', field) == ['张三/001', '李四/002']
        assert field.excel_codec.parse_input('1,2', field) == ['1,2']

    async def test_deserialize_maps_staff_ids_to_display_names(self):
        class Importer(BaseModel):
            staff: Annotated[
                list[str],
                ExcelColumn(
                    codec=MULTI_STAFF_CODEC,
                    label='员工',
                    options=[
                        Option(id=OptionId(1), name='张三/001'),
                        Option(id=OptionId(2), name='李四/002'),
                    ],
                ),
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(MultiChoiceFieldCodec, field.excel_codec)

        assert field.excel_codec.format_display_value('张三/001、李四/002', field) == '张三/001、李四/002'
        assert field.excel_codec.format_display_value([1, 2], field) == '张三/001、李四/002'

    async def test_validate_rejects_unknown_staff_with_business_message(self):
        class Importer(BaseModel):
            staff: Annotated[
                list[str],
                ExcelColumn(
                    codec=MULTI_STAFF_CODEC,
                    label='员工',
                    options=[
                        Option(id=OptionId(1), name='张三/001'),
                        Option(id=OptionId(2), name='李四/002'),
                    ],
                ),
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(MultiChoiceFieldCodec, field.excel_codec)

        with self.assertRaises(ValueError) as context:
            field.excel_codec.normalize_import_value(['张三/001', '王五/003'], field)
        assert (
            str(context.exception)
            == 'Select staff members from the configured options. Valid values include: 张三/001、李四/002'
        )
