import re

from excelalchemy.codecs.field_codec import ExcelFieldCodecSpec, WorkbookInputValue
from excelalchemy.codecs.text import TextFieldCodec
from excelalchemy.messages import MessageKey
from excelalchemy.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo

PHONE_NUMBER_PATTERN = re.compile(r'^((0\d{2,3}-\d{7,8})|(1[3456789]\d{9}))$')


class PhoneNumberFieldCodec(TextFieldCodec):
    @classmethod
    def expected_input_message(cls, field_meta: FieldMetaInfo) -> str | None:
        return msg(MessageKey.VALID_PHONE_NUMBER_REQUIRED)

    @classmethod
    def normalize_import_value(cls, value: WorkbookInputValue, field_meta: FieldMetaInfo) -> str:
        parsed = str(value)

        if not PHONE_NUMBER_PATTERN.match(parsed):
            raise ValueError(msg(MessageKey.VALID_PHONE_NUMBER_REQUIRED))

        return parsed


class PhoneNumberCodec:
    """Factory for explicit phone-number codec configuration."""

    def __new__(cls) -> ExcelFieldCodecSpec:
        return ExcelFieldCodecSpec.create(PhoneNumberFieldCodec)
