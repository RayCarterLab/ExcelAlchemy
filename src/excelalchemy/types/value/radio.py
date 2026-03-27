import logging
from typing import Any

from excelalchemy.const import MULTI_CHECKBOX_SEPARATOR
from excelalchemy.exc import ProgrammaticError
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.i18n.messages import message as msg
from excelalchemy.types.abstract import ABCValueType
from excelalchemy.types.field import FieldMetaInfo
from excelalchemy.types.identity import OptionId


class Radio(ABCValueType, str):
    __name__ = '单选框组'

    @classmethod
    def comment(cls, field_meta: FieldMetaInfo) -> str:
        if not field_meta.options:
            logging.error('Field %s of type %s must define options', field_meta.label, cls.__name__)

        return '\n'.join(
            [
                field_meta.comment_required,
                field_meta.comment_options,
                dmsg(MessageKey.COMMENT_SELECTION_MODE, value=dmsg(MessageKey.COMMENT_SELECTION_VALUE_SINGLE)),
                field_meta.comment_hint,
            ]
        )

    @classmethod
    def serialize(cls, value: Any, field_meta: FieldMetaInfo) -> str:
        return str(value).strip()

    @classmethod
    def deserialize(cls, value: Any | None, field_meta: FieldMetaInfo) -> str:
        if value is None or value == '':
            return ''

        try:
            return field_meta.options_id_map[value.strip()].name
        except Exception as exc:
            logging.warning(
                'Type %s could not resolve option %s for field %s; returning the original value. Reason: %s',
                cls.__name__,
                value,
                field_meta.label,
                exc,
            )
        return value if value is not None else ''

    @classmethod
    def __validate__(cls, value: str, field_meta: FieldMetaInfo) -> OptionId | str:  # return Option.id
        if MULTI_CHECKBOX_SEPARATOR in value:
            raise ValueError(msg(MessageKey.MULTIPLE_SELECTIONS_NOT_SUPPORTED))

        parsed = value.strip()

        if field_meta.options is None:
            raise ProgrammaticError(msg(MessageKey.OPTIONS_CANNOT_BE_NONE_FOR_SELECTION_FIELDS))

        if not field_meta.options:  # empty
            logging.warning('Field %s of type %s has no options; returning the original value', field_meta.label, cls.__name__)
            return parsed

        if parsed in field_meta.options_id_map:
            return parsed

        if parsed not in field_meta.options_name_map:
            raise ValueError(msg(MessageKey.OPTION_NOT_FOUND_FIELD_COMMENT))

        return field_meta.options_name_map[parsed].id
