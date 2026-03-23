from typing import Any

from pydantic import HttpUrl, TypeAdapter

from excelalchemy.types.field import FieldMetaInfo
from excelalchemy.types.value.string import String


class Url(String):
    _validator = TypeAdapter(HttpUrl)

    @classmethod
    def __validate__(cls, value: Any, field_meta: FieldMetaInfo) -> str:
        parsed = str(value)
        errors: list[str] = []

        try:
            cls._validator.validate_python(parsed)
        except Exception:
            errors.append('请输入正确的网址')

        if errors:
            raise ValueError(*errors)
        else:
            return parsed
