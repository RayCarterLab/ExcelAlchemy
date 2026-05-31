from pydantic import HttpUrl, TypeAdapter

from excelalchemy.codecs.field_codec import ExcelFieldCodecSpec, WorkbookInputValue
from excelalchemy.codecs.text import TextFieldCodec
from excelalchemy.field_metadata import FieldMetaInfo
from excelalchemy.messages import MessageKey
from excelalchemy.messages import user_message as umsg


class UrlFieldCodec(TextFieldCodec):
    _validator = TypeAdapter(HttpUrl)

    @classmethod
    def expected_input_message(cls, field_meta: FieldMetaInfo) -> str | None:
        return umsg(MessageKey.VALID_URL_REQUIRED)

    @classmethod
    def normalize_import_value(cls, value: WorkbookInputValue, field_meta: FieldMetaInfo) -> str:
        parsed = str(value)
        errors: list[str] = []

        try:
            cls._validator.validate_python(parsed)
        except Exception:
            errors.append(umsg(MessageKey.VALID_URL_REQUIRED))

        if errors:
            raise ValueError(*errors)
        else:
            return parsed


class UrlCodec:
    """Factory for explicit URL codec configuration."""

    def __new__(cls) -> ExcelFieldCodecSpec:
        return ExcelFieldCodecSpec.create(UrlFieldCodec)
