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

MULTI_ORGANIZATION_CODEC = MultiChoiceCodec(
    entity_name_plural='organizations',
    hint=dmsg(MessageKey.MULTI_ORGANIZATION_HINT),
    include_options_in_comment=False,
    include_mode_in_comment=False,
    separator='、',
)


class TestMultiChoiceOrganizationConfig(BaseTestCase):
    async def test_comment_describes_multi_organization_input(self):
        class Importer(BaseModel):
            multi_organization: Annotated[
                list[str], ExcelColumn(codec=MULTI_ORGANIZATION_CODEC, label='多选组织', order=1)
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(MultiChoiceFieldCodec, field.excel_codec)

        assert (
            field.excel_codec.build_comment(field)
            == '必填性：必填\n提示：需按照组织架构树填写组织完整路径，如“XX公司/一级部门/二级部门”，多选时，选项之间用“、”连接'
        )

    async def test_deserialize_maps_organization_ids_to_display_names(self):
        class Importer(BaseModel):
            multi_organization: Annotated[
                list[str],
                ExcelColumn(
                    codec=MULTI_ORGANIZATION_CODEC,
                    label='多选组织',
                    order=1,
                    options=[
                        Option(id=OptionId(1), name='一级部门'),
                        Option(id=OptionId(2), name='三级部门'),
                    ],
                ),
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(MultiChoiceFieldCodec, field.excel_codec)

        assert (
            field.excel_codec.format_display_value('XX公司/一级部门/二级部门、XX公司/一级部门/三级部门', field)
            == 'XX公司/一级部门/二级部门、XX公司/一级部门/三级部门'
        )
        assert field.excel_codec.format_display_value([1, 2], field) == '一级部门、三级部门'
        assert field.excel_codec.format_display_value([1, 2, 3], field) == '一级部门、三级部门、3'
