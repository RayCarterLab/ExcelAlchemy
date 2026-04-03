from pydantic import HttpUrl, TypeAdapter

from excelalchemy.codecs.base import WorkbookInputValue
from excelalchemy.codecs.string import String
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo


class Url(String):
    _validator = TypeAdapter(HttpUrl)

    @classmethod
    def normalize_import_value(cls, value: WorkbookInputValue, field_meta: FieldMetaInfo) -> str:
        parsed = str(value)
        errors: list[str] = []

        try:
            cls._validator.validate_python(parsed)
        except Exception:
            errors.append(msg(MessageKey.VALID_URL_REQUIRED))

        if errors:
            raise ValueError(*errors)
        else:
            return parsed


UrlCodec = Url
