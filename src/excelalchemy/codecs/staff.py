from typing import cast

from excelalchemy._primitives.constants import MULTI_CHECKBOX_SEPARATOR
from excelalchemy._primitives.identity import OptionId
from excelalchemy.codecs.base import log_codec_option_resolution_fallback, log_codec_render_fallback
from excelalchemy.codecs.multi_checkbox import MultiCheckbox
from excelalchemy.codecs.radio import Radio
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.i18n.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo


class SingleStaff(Radio):
    __name__ = 'SingleStaff'

    @classmethod
    def selection_entity_singular(cls) -> str | None:
        return 'staff member'

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        extra_hint = presentation.hint or dmsg(MessageKey.SINGLE_STAFF_HINT)
        value_key = (
            MessageKey.COMMENT_REQUIRED_VALUE_REQUIRED
            if declared.effective_required
            else MessageKey.COMMENT_REQUIRED_VALUE_OPTIONAL
        )
        return f'{dmsg(MessageKey.COMMENT_REQUIRED, value=dmsg(value_key))} \n{dmsg(MessageKey.COMMENT_HINT, value=extra_hint)}'

    @classmethod
    def parse_input(cls, value: object, field_meta: FieldMetaInfo) -> str:
        return super().parse_input(value, field_meta)

    @classmethod
    def format_display_value(cls, value: object | None, field_meta: FieldMetaInfo) -> str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        if value is None or value == '':
            return ''
        if not isinstance(value, str):
            return str(value)
        try:
            return presentation.options_id_map(field_label=declared.label)[OptionId(value.strip())].name
        except KeyError:
            log_codec_option_resolution_fallback(cls.__name__, value, field_label=declared.label)
        return value


class MultiStaff(MultiCheckbox):
    __name__ = 'MultiStaff'

    @classmethod
    def selection_entity_plural(cls) -> str | None:
        return 'staff members'

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        return '\n'.join(
            [
                declared.comment_required,
                dmsg(MessageKey.COMMENT_HINT, value=presentation.hint or dmsg(MessageKey.MULTI_STAFF_HINT)),
            ]
        )

    @classmethod
    def parse_input(cls, value: object, field_meta: FieldMetaInfo) -> object:
        return super().parse_input(value, field_meta)

    @classmethod
    def normalize_import_value(cls, value: object, field_meta: FieldMetaInfo) -> list[str]:
        return super().normalize_import_value(value, field_meta)

    @classmethod
    def format_display_value(cls, value: object, field_meta: FieldMetaInfo) -> str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        if isinstance(value, str):
            return value

        if isinstance(value, list):
            items = MultiStaff._coerce_items(cast(object, value))
            assert items is not None
            option_ids = [OptionId(option_id) for option_id in items]
            if len(option_ids) != len(set(option_ids)):
                raise ValueError(msg(MessageKey.OPTIONS_CONTAIN_DUPLICATES))

            option_names = presentation.exchange_option_ids_to_names(option_ids, field_label=declared.label)
            return f'{MULTI_CHECKBOX_SEPARATOR}'.join(option_names)

        log_codec_render_fallback(
            cls.__name__,
            value,
            field_label=declared.label,
            reason='The workbook value is not a string or a list of option ids',
        )
        return str(value)


SingleStaffCodec = SingleStaff
MultiStaffCodec = MultiStaff
