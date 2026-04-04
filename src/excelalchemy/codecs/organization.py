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
    def selection_entity_singular(cls) -> str | None:
        return 'organization'

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        extra_hint = presentation.hint or dmsg(MessageKey.SINGLE_ORGANIZATION_HINT)
        value_key = (
            MessageKey.COMMENT_REQUIRED_VALUE_REQUIRED
            if declared.effective_required
            else MessageKey.COMMENT_REQUIRED_VALUE_OPTIONAL
        )
        return '\n'.join(
            [dmsg(MessageKey.COMMENT_REQUIRED, value=dmsg(value_key)), dmsg(MessageKey.COMMENT_HINT, value=extra_hint)]
        )

    @classmethod
    def parse_input(cls, value: object, field_meta: FieldMetaInfo) -> str:
        return super().parse_input(value, field_meta)

    @classmethod
    def format_display_value(cls, value: object, field_meta: FieldMetaInfo) -> str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        if not isinstance(value, str):
            return '' if value is None else str(value)
        try:
            return presentation.options_id_map(field_label=declared.label)[OptionId(value.strip())].name
        except KeyError:
            logging.warning('Could not resolve organization option %s; returning the original value', value)

        return value


class MultiOrganization(MultiCheckbox):
    __name__ = 'MultiOrganization'

    @classmethod
    def selection_entity_plural(cls) -> str | None:
        return 'organizations'

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        return '\n'.join(
            [
                declared.comment_required,
                dmsg(MessageKey.COMMENT_HINT, value=presentation.hint or dmsg(MessageKey.MULTI_ORGANIZATION_HINT)),
            ]
        )

    @classmethod
    def parse_input(cls, value: object, field_meta: FieldMetaInfo) -> object:
        return super().parse_input(value, field_meta)

    @classmethod
    def format_display_value(cls, value: object | None, field_meta: FieldMetaInfo) -> str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        if value is None or value == '':
            return ''

        if isinstance(value, str):
            return value

        if isinstance(value, list):
            items = MultiOrganization._coerce_items(cast(object, value))
            assert items is not None
            option_ids = [OptionId(option_id) for option_id in items]
            option_names = presentation.exchange_option_ids_to_names(option_ids, field_label=declared.label)
            return MULTI_CHECKBOX_SEPARATOR.join(map(str, option_names))

        logging.warning('%s could not be deserialized; returning the original value', cls.__name__)
        return str(value)

    @classmethod
    def normalize_import_value(cls, value: object, field_meta: FieldMetaInfo) -> list[str]:
        return super().normalize_import_value(value, field_meta)


SingleOrganizationCodec = SingleOrganization
MultiOrganizationCodec = MultiOrganization
