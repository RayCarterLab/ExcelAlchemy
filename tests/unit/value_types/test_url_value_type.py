from typing import cast

from excelalchemy import FieldMeta, Url
from pydantic import BaseModel

from tests.support import BaseTestCase


class TestUrlValueType(BaseTestCase):
    async def test_comment_describes_url_input(self):
        class Importer(BaseModel):
            url: Url = FieldMeta(label='url', order=1)

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(Url, field.value_type)

        assert (
            field.value_type.comment(field)
            == '唯一性：非唯一\n必填性：必填\n最大长度：无限制\n可输入内容:中文、数字、大写字母、小写字母、符号\n'
        )

    async def test_serialize_strips_url_input(self):
        class Importer(BaseModel):
            url: Url = FieldMeta(label='url', order=1)

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(Url, field.value_type)

        assert field.value_type.serialize('http://www.baidu.com', field) == 'http://www.baidu.com'

    async def test_deserialize_returns_user_visible_url_values(self):
        class Importer(BaseModel):
            url: Url = FieldMeta(label='url', order=1)

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(Url, field.value_type)

        assert field.value_type.deserialize('http://www.baidu.com', field) == 'http://www.baidu.com'
        assert field.value_type.deserialize('1', field) == '1'

    async def test_validate_accepts_well_formed_urls(self):
        class Importer(BaseModel):
            url: Url = FieldMeta(label='url', order=1)

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(Url, field.value_type)

        assert field.value_type.__validate__('http://www.baidu.com', field) == 'http://www.baidu.com'
        self.assertRaises(ValueError, field.value_type.__validate__, '1', field)
