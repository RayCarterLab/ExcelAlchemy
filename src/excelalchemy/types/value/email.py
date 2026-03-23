from typing import Any

from pydantic import EmailStr

from excelalchemy.types.field import FieldMetaInfo
from excelalchemy.types.value.string import String


class Email(String):
    @classmethod
    def __validate__(cls, value: Any, field_meta: FieldMetaInfo) -> str:
        # Try to parse the value as a string
        try:
            parsed = str(value)
        except Exception as exc:
            raise ValueError('请输入正确的邮箱') from exc

        # Validate the parsed string as an email address
        try:
            EmailStr.validate(parsed)
        except Exception as exc:
            raise ValueError('请输入正确的邮箱') from exc

        # Return the parsed string if validation succeeds
        return parsed
