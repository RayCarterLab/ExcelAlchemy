from typing import ClassVar

from pydantic import EmailStr, TypeAdapter

from excelalchemy.codecs.string import String
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo


class Email(String):
    _validator: ClassVar[TypeAdapter[EmailStr]] = TypeAdapter(EmailStr)

    @classmethod
    def expected_input_message(cls, field_meta: FieldMetaInfo) -> str | None:
        return msg(MessageKey.VALID_EMAIL_REQUIRED)

    @classmethod
    def normalize_import_value(cls, value: object, field_meta: FieldMetaInfo) -> str:
        # Try to parse the value as a string
        try:
            parsed = str(value)
        except Exception as exc:
            raise ValueError(msg(MessageKey.VALID_EMAIL_REQUIRED)) from exc

        # Validate the parsed string as an email address
        try:
            cls._validator.validate_python(parsed)
        except Exception as exc:
            raise ValueError(msg(MessageKey.VALID_EMAIL_REQUIRED)) from exc

        # Return the parsed string if validation succeeds
        return parsed


EmailCodec = Email
