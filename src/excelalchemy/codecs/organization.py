import logging
from typing import Any

from excelalchemy._internal.constants import MULTI_CHECKBOX_SEPARATOR
from excelalchemy.codecs.multi_checkbox import MultiCheckbox
from excelalchemy.codecs.radio import Radio
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.metadata import FieldMetaInfo


class SingleOrganization(Radio):
    __name__ = '组织单选'

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        extra_hint = field_meta.hint or dmsg(MessageKey.SINGLE_ORGANIZATION_HINT)
        value_key = MessageKey.COMMENT_REQUIRED_VALUE_REQUIRED if field_meta.required else MessageKey.COMMENT_REQUIRED_VALUE_OPTIONAL
        return '\n'.join([dmsg(MessageKey.COMMENT_REQUIRED, value=dmsg(value_key)), dmsg(MessageKey.COMMENT_HINT, value=extra_hint)])

    @classmethod
    def parse_input(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    @classmethod
    def format_display_value(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        try:
            return field_meta.options_id_map[value.strip()].name
        except KeyError:
            logging.warning('无法找到组织 %s 的选项, 返回原值', value)

        return value if value is not None else ''


class MultiOrganization(MultiCheckbox):
    __name__ = '组织多选'

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        return '\n'.join(
            [
                field_meta.comment_required,
                dmsg(MessageKey.COMMENT_HINT, value=field_meta.hint or dmsg(MessageKey.MULTI_ORGANIZATION_HINT)),
            ]
        )

    @classmethod
    def parse_input(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        return super().parse_input(value, field_meta)

    @classmethod
    def format_display_value(cls, value: str | list[str] | None | Any, field_meta: FieldMetaInfo) -> str | Any:
        if value is None or value == '':
            return ''

        if isinstance(value, str):
            return value

        if isinstance(value, list):
            option_names = field_meta.exchange_option_ids_to_names(value)
            return MULTI_CHECKBOX_SEPARATOR.join(map(str, option_names))

        logging.warning('%s 反序列化失败', cls.__name__)
        return value

    @classmethod
    def normalize_import_value(cls, value: Any, field_meta: FieldMetaInfo) -> list[str]:
        return super().normalize_import_value(value, field_meta)


SingleOrganizationCodec = SingleOrganization
MultiOrganizationCodec = MultiOrganization
