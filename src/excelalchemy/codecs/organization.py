import logging
from typing import cast

from excelalchemy._primitives.constants import MULTI_CHECKBOX_SEPARATOR
from excelalchemy._primitives.identity import OptionId
from excelalchemy.codecs.multi_checkbox import MultiCheckbox
from excelalchemy.codecs.radio import Radio
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.metadata import FieldMetaInfo


class SingleOrganization(Radio):
    __name__ = 'SingleOrganization'

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        extra_hint = field_meta.hint or dmsg(MessageKey.SINGLE_ORGANIZATION_HINT)
        value_key = MessageKey.COMMENT_REQUIRED_VALUE_REQUIRED if field_meta.required else MessageKey.COMMENT_REQUIRED_VALUE_OPTIONAL
        return '\n'.join([dmsg(MessageKey.COMMENT_REQUIRED, value=dmsg(value_key)), dmsg(MessageKey.COMMENT_HINT, value=extra_hint)])

    @classmethod
    def parse_input(cls, value: object, field_meta: FieldMetaInfo) -> str:
        return super().parse_input(value, field_meta)

    @classmethod
    def format_display_value(cls, value: object, field_meta: FieldMetaInfo) -> str:
        if not isinstance(value, str):
            return '' if value is None else str(value)
        try:
            return field_meta.options_id_map[OptionId(value.strip())].name
        except KeyError:
            logging.warning('Could not resolve organization option %s; returning the original value', value)

        return value


class MultiOrganization(MultiCheckbox):
    __name__ = 'MultiOrganization'

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        return '\n'.join(
            [
                field_meta.comment_required,
                dmsg(MessageKey.COMMENT_HINT, value=field_meta.hint or dmsg(MessageKey.MULTI_ORGANIZATION_HINT)),
            ]
        )

    @classmethod
    def parse_input(cls, value: object, field_meta: FieldMetaInfo) -> object:
        return super().parse_input(value, field_meta)

    @classmethod
    def format_display_value(cls, value: object | None, field_meta: FieldMetaInfo) -> str:
        if value is None or value == '':
            return ''

        if isinstance(value, str):
            return value

        if isinstance(value, list):
            items = cast(list[object], value)
            option_ids = [OptionId(option_id) for option_id in items]
            option_names = field_meta.exchange_option_ids_to_names(option_ids)
            return MULTI_CHECKBOX_SEPARATOR.join(map(str, option_names))

        logging.warning('%s could not be deserialized; returning the original value', cls.__name__)
        return str(value)

    @classmethod
    def normalize_import_value(cls, value: object, field_meta: FieldMetaInfo) -> list[str]:
        return super().normalize_import_value(value, field_meta)


SingleOrganizationCodec = SingleOrganization
MultiOrganizationCodec = MultiOrganization
