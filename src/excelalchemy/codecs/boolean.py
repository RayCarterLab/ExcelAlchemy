import logging
from typing import Any

from excelalchemy.codecs import excel_choice_codec
from excelalchemy.codecs.base import ExcelFieldCodec
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.i18n.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo


@excel_choice_codec
class Boolean(ExcelFieldCodec):
    __name__ = 'Boolean'

    @staticmethod
    def _true_display() -> str:
        return dmsg(MessageKey.BOOLEAN_TRUE_DISPLAY)

    @staticmethod
    def _false_display() -> str:
        return dmsg(MessageKey.BOOLEAN_FALSE_DISPLAY)

    @classmethod
    def _true_values(cls) -> set[str]:
        return {cls._true_display(), '是'}

    @classmethod
    def _false_values(cls) -> set[str]:
        return {cls._false_display(), '否'}

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        return '\n'.join(
            [
                field_meta.comment_required,
                field_meta.comment_hint,
            ]
        )

    @classmethod
    def parse_input(cls, value: Any, field_meta: FieldMetaInfo) -> str:
        return str(value).strip()

    @classmethod
    def format_display_value(cls, value: bool | str | None | Any, field_meta: FieldMetaInfo) -> str:
        if value is None or value == '':
            return cls._false_display()

        if isinstance(value, bool):
            return cls._true_display() if value else cls._false_display()

        elif isinstance(value, str):
            value = value.strip()
            if value in cls._true_values():
                return cls._true_display()
            if value in cls._false_values():
                return cls._false_display()
            if value not in cls._true_values() | cls._false_values():
                logging.warning('Could not recognize boolean value %s; returning the original value', value)
                return value
        else:
            logging.warning(
                'Type %s could not deserialize %s for field %s; returning the default value %s',
                cls.__name__,
                value,
                field_meta.label,
                cls._false_display(),
            )

        return cls._true_display() if str(value) in cls._true_values() else cls._false_display()

    @classmethod
    def normalize_import_value(cls, value: str | bool | Any, field_meta: FieldMetaInfo) -> bool:
        if isinstance(value, bool):
            return value

        value_str = str(value).strip()

        if value_str in cls._true_values():
            return True
        if value_str in cls._false_values():
            return False

        raise ValueError(
            msg(
                MessageKey.BOOLEAN_ENTER_YES_OR_NO,
                true_value=cls._true_display(),
                false_value=cls._false_display(),
            )
        )


BooleanCodec = Boolean
