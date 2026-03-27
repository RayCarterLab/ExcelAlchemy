import logging
from typing import Any

from excelalchemy.const import MULTI_CHECKBOX_SEPARATOR
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.i18n.messages import message as msg
from excelalchemy.types.field import FieldMetaInfo
from excelalchemy.types.identity import OptionId
from excelalchemy.types.value.multi_checkbox import MultiCheckbox
from excelalchemy.types.value.radio import Radio


class SingleStaff(Radio):
    __name__ = '人员单选'

    @classmethod
    def comment(cls, field_meta: FieldMetaInfo) -> str:
        extra_hint = field_meta.hint or dmsg(MessageKey.SINGLE_STAFF_HINT)
        value_key = MessageKey.COMMENT_REQUIRED_VALUE_REQUIRED if field_meta.required else MessageKey.COMMENT_REQUIRED_VALUE_OPTIONAL
        return f'{dmsg(MessageKey.COMMENT_REQUIRED, value=dmsg(value_key))} \n{dmsg(MessageKey.COMMENT_HINT, value=extra_hint)}'

    @classmethod
    def serialize(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    @classmethod
    def deserialize(cls, value: Any | None, field_meta: FieldMetaInfo) -> str:
        if value is None or value == '':
            return ''
        try:
            return field_meta.options_id_map[value.strip()].name
        except KeyError:
            logging.warning('类型【%s】无法为【%s】找到【%s】的选项, 返回原值', cls.__name__, field_meta.label, value)
        return value if value is not None else ''


class MultiStaff(MultiCheckbox):
    __name__ = '人员多选'

    @classmethod
    def comment(cls, field_meta: FieldMetaInfo) -> str:
        return '\n'.join(
            [
                field_meta.comment_required,
                dmsg(MessageKey.COMMENT_HINT, value=field_meta.hint or dmsg(MessageKey.MULTI_STAFF_HINT)),
            ]
        )

    @classmethod
    def serialize(cls, value: str | list[str] | Any, field_meta: FieldMetaInfo) -> Any:
        return super().serialize(value, field_meta)

    @classmethod
    def __validate__(cls, value: Any, field_meta: FieldMetaInfo) -> list[str]:
        return super().__validate__(value, field_meta)

    @classmethod
    def deserialize(cls, value: str | list[OptionId] | Any, field_meta: FieldMetaInfo) -> Any:
        if isinstance(value, str):
            return value

        if isinstance(value, list):
            if len(value) != len(set(value)):
                raise ValueError(msg(MessageKey.OPTIONS_CONTAIN_DUPLICATES))

            option_names = field_meta.exchange_option_ids_to_names(value)
            return f'{MULTI_CHECKBOX_SEPARATOR}'.join(option_names)

        logging.warning('%s could not be deserialized', cls.__name__)
        return value
