from typing import Annotated, cast

from pydantic import BaseModel

from excelalchemy import (
    ExcelColumn,
    MultiOrganizationCodec,
    Option,
    OptionId,
)
from excelalchemy.codecs.organization import MultiOrganization
from tests.support import BaseTestCase


class TestMultiOrganizationValueType(BaseTestCase):
    async def test_comment_describes_multi_organization_input(self):
        class Importer(BaseModel):
            multi_organization: Annotated[
                list[str], ExcelColumn(codec=MultiOrganizationCodec(), label='多选组织', order=1)
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(MultiOrganization, field.excel_codec)

        assert (
            field.excel_codec.build_comment(field)
            == '必填性：必填\n提示：需按照组织架构树填写组织完整路径，如“XX公司/一级部门/二级部门”，多选时，选项之间用“、”连接'
        )

    async def test_deserialize_maps_organization_ids_to_display_names(self):
        class Importer(BaseModel):
            multi_organization: Annotated[
                list[str],
                ExcelColumn(
                    codec=MultiOrganizationCodec(),
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
        field.excel_codec = cast(MultiOrganization, field.excel_codec)

        assert (
            field.excel_codec.format_display_value('XX公司/一级部门/二级部门、XX公司/一级部门/三级部门', field)
            == 'XX公司/一级部门/二级部门、XX公司/一级部门/三级部门'
        )
        assert field.excel_codec.format_display_value([1, 2], field) == '一级部门，三级部门'
        assert field.excel_codec.format_display_value([1, 2, 3], field) == '一级部门，三级部门，3'
