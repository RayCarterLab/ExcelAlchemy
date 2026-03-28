import logging
from typing import cast

from excelalchemy._primitives.constants import MULTI_CHECKBOX_SEPARATOR
from excelalchemy._primitives.identity import OptionId
from excelalchemy.codecs.base import ExcelFieldCodec
from excelalchemy.exceptions import ProgrammaticError
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.i18n.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo


class MultiCheckbox(ExcelFieldCodec, list[str]):
    __name__ = 'MultiChoice'

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        return '\n'.join(
            [
                field_meta.comment_required,
                field_meta.comment_options,
                dmsg(MessageKey.COMMENT_SELECTION_MODE, value=dmsg(MessageKey.COMMENT_SELECTION_VALUE_MULTI)),
                field_meta.comment_hint,
            ]
        )

    @classmethod
    def parse_input(cls, value: object, field_meta: FieldMetaInfo) -> list[str] | object:
        if isinstance(value, list):
            items = cast(list[object], value)
            return [str(item).strip() for item in items]

        if isinstance(value, str):
            return [item.strip() for item in value.split(MULTI_CHECKBOX_SEPARATOR)]

        logging.warning(
            'ValueType <%s> could not parse Excel input %s; returning the original value', cls.__name__, value
        )
        return value

    @classmethod
    def normalize_import_value(cls, value: object, field_meta: FieldMetaInfo) -> list[str]:  # OptionId
        if not isinstance(value, list):
            raise ValueError(msg(MessageKey.OPTION_NOT_FOUND_HEADER_COMMENT))

        items = cast(list[object], value)
        parsed = [str(item).strip() for item in items]

        if field_meta.options is None:
            raise ProgrammaticError(msg(MessageKey.OPTIONS_CANNOT_BE_NONE_FOR_VALUE_TYPE, value_type=cls.__name__))

        if not field_meta.options:  # empty
            logging.warning(
                'Field %s of type %s has no options; returning the original value', field_meta.label, cls.__name__
            )
            return parsed

        if len(parsed) != len(set(parsed)):
            raise ValueError(msg(MessageKey.OPTIONS_CONTAIN_DUPLICATES))

        result, errors = field_meta.exchange_names_to_option_ids_with_errors(parsed)

        if errors:
            raise ValueError(*errors)
        else:
            return result

    @classmethod
    def format_display_value(cls, value: str | list[OptionId] | None, field_meta: FieldMetaInfo) -> str:
        match value:
            case None | '':
                return ''
            case str():
                return value
            case list():
                option_ids = [OptionId(option_id) for option_id in value]
                option_names = field_meta.exchange_option_ids_to_names(option_ids)
                return f'{MULTI_CHECKBOX_SEPARATOR}'.join(option_names)


MultiChoiceCodec = MultiCheckbox
