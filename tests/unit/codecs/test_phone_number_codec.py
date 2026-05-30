from typing import Annotated, cast

from pydantic import BaseModel

from excelalchemy import (
    ExcelColumn,
    PhoneNumberCodec,
)
from excelalchemy.codecs.phone_number import PhoneNumber
from tests.support import BaseTestCase


class TestPhoneNumberValueType(BaseTestCase):
    async def test_validate_accepts_mobile_numbers_only(self):
        class Importer(BaseModel):
            phone_number: Annotated[str, ExcelColumn(codec=PhoneNumberCodec(), label='手机号', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(PhoneNumber, field.excel_codec)

        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, 'ddd', field)
        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, '1234567890', field)
        assert field.excel_codec.normalize_import_value('13216762386', field) == '13216762386'
        with self.assertRaises(ValueError) as context:
            field.excel_codec.normalize_import_value('ddd', field)
        assert str(context.exception) == 'Enter a valid phone number, such as 13800138000'
