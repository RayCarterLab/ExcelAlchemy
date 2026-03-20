from typing import cast

from pydantic import BaseModel

from excelalchemy import FieldMeta
from excelalchemy import PhoneNumber
from tests.support import BaseTestCase


class TestPhoneNumberValueType(BaseTestCase):
    async def test_validate_accepts_mobile_numbers_only(self):
        class Importer(BaseModel):
            phone_number: PhoneNumber = FieldMeta(label='手机号', order=1)

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.value_type = cast(PhoneNumber, field.value_type)

        self.assertRaises(ValueError, field.value_type.__validate__, 'ddd', field)
        self.assertRaises(ValueError, field.value_type.__validate__, '1234567890', field)
        assert field.value_type.__validate__('13216762386', field) == '13216762386'
