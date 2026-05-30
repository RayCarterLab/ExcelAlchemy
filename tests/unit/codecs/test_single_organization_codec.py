from typing import Annotated, cast

from pydantic import BaseModel

from excelalchemy import (
    ExcelColumn,
    Option,
    OptionId,
    SingleOrganizationCodec,
)
from excelalchemy.codecs.organization import SingleOrganization
from tests.support import BaseTestCase


class TestSingleOrganizationValueType(BaseTestCase):
    async def test_comment_describes_single_organization_input(self):
        class Importer(BaseModel):
            single_organization: Annotated[str, ExcelColumn(codec=SingleOrganizationCodec(), label='单选组织', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(SingleOrganization, field.excel_codec)

        assert (
            field.excel_codec.build_comment(field)
            == "必填性：必填\n提示：需按照组织架构树填写组织完整路径，例如 'XX公司/一级部门/二级部门'."
        )

    async def test_serialize_strips_single_organization_input(self):
        class Importer(BaseModel):
            single_organization: Annotated[str, ExcelColumn(codec=SingleOrganizationCodec(), label='单选组织', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(SingleOrganization, field.excel_codec)

        assert field.excel_codec.parse_input('XX公司/一级部门/二级部门', field) == 'XX公司/一级部门/二级部门'

    async def test_deserialize_maps_single_organization_id_to_display_name(self):
        class Importer(BaseModel):
            single_organization: Annotated[
                str,
                ExcelColumn(
                    codec=SingleOrganizationCodec(),
                    label='单选组织',
                    order=1,
                    options=[
                        Option(id=OptionId(1), name='XX公司/一级部门/二级部门'),
                    ],
                ),
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(SingleOrganization, field.excel_codec)

        assert field.excel_codec.format_display_value('XX公司/一级部门/二级部门', field) == 'XX公司/一级部门/二级部门'
        assert field.excel_codec.format_display_value('1', field) == 'XX公司/一级部门/二级部门'

    async def test_validate_rejects_unknown_organizations_with_business_message(self):
        class Importer(BaseModel):
            single_organization: Annotated[
                str,
                ExcelColumn(
                    codec=SingleOrganizationCodec(),
                    label='单选组织',
                    order=1,
                    options=[
                        Option(id=OptionId(1), name='XX公司/一级部门/二级部门'),
                    ],
                ),
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(SingleOrganization, field.excel_codec)

        with self.assertRaises(ValueError) as context:
            field.excel_codec.normalize_import_value('未知组织', field)
        assert str(context.exception) == (
            'Select one organization from the configured options. Valid values include: XX公司/一级部门/二级部门'
        )
