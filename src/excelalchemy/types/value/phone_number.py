import re
from typing import Any

from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import message as msg
from excelalchemy.types.field import FieldMetaInfo
from excelalchemy.types.value.string import String

PHONE_NUMBER_PATTERN = re.compile(r'^((0\d{2,3}-\d{7,8})|(1[3456789]\d{9}))$')


class PhoneNumber(String):
    @classmethod
    def __validate__(cls, value: Any, field_meta: FieldMetaInfo) -> str:
        parsed = str(value)

        if not PHONE_NUMBER_PATTERN.match(parsed):
            raise ValueError(msg(MessageKey.VALID_PHONE_NUMBER_REQUIRED))

        return parsed
