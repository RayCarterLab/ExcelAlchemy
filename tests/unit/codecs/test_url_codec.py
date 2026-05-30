from typing import Annotated, cast

from pydantic import BaseModel

from excelalchemy import (
    ExcelColumn,
    UrlCodec,
)
from excelalchemy.codecs.url import Url
from tests.support import BaseTestCase


class TestUrlValueType(BaseTestCase):
    async def test_comment_describes_url_input(self):
        class Importer(BaseModel):
            url: Annotated[str, ExcelColumn(codec=UrlCodec(), label='url', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(Url, field.excel_codec)

        assert (
            field.excel_codec.build_comment(field)
            == '唯一性：非唯一\n必填性：必填\n最大长度：无限制\n可输入内容:中文、数字、大写字母、小写字母、符号\n'
        )

    async def test_serialize_strips_url_input(self):
        class Importer(BaseModel):
            url: Annotated[str, ExcelColumn(codec=UrlCodec(), label='url', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(Url, field.excel_codec)

        assert field.excel_codec.parse_input('http://www.baidu.com', field) == 'http://www.baidu.com'

    async def test_deserialize_returns_user_visible_url_values(self):
        class Importer(BaseModel):
            url: Annotated[str, ExcelColumn(codec=UrlCodec(), label='url', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(Url, field.excel_codec)

        assert field.excel_codec.format_display_value('http://www.baidu.com', field) == 'http://www.baidu.com'
        assert field.excel_codec.format_display_value('1', field) == '1'

    async def test_validate_accepts_well_formed_urls(self):
        class Importer(BaseModel):
            url: Annotated[str, ExcelColumn(codec=UrlCodec(), label='url', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(Url, field.excel_codec)

        assert field.excel_codec.normalize_import_value('http://www.baidu.com', field) == 'http://www.baidu.com'
        with self.assertRaises(ValueError) as context:
            field.excel_codec.normalize_import_value('1', field)
        assert str(context.exception) == 'Enter a valid URL, such as https://example.com'
