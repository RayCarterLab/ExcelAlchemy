import logging

from excelalchemy.codecs.base import WorkbookDisplayValue, WorkbookInputValue
from excelalchemy.codecs.multi_checkbox import MultiCheckbox
from excelalchemy.codecs.radio import Radio
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.metadata import FieldMetaInfo


class SingleTreeNode(Radio):
    __name__ = 'SingleTreeNode'

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        return '\n'.join(
            [
                declared.comment_required,
                dmsg(MessageKey.COMMENT_HINT, value=presentation.hint or dmsg(MessageKey.SINGLE_TREE_HINT)),
            ]
        )

    @classmethod
    def parse_input(cls, value: WorkbookInputValue, field_meta: FieldMetaInfo) -> WorkbookInputValue:
        if isinstance(value, str):
            return value.strip()
        return value

    @classmethod
    def format_display_value(
        cls,
        value: WorkbookDisplayValue,
        field_meta: FieldMetaInfo,
    ) -> WorkbookDisplayValue:
        declared = field_meta.declared
        presentation = field_meta.presentation
        try:
            return presentation.options_id_map(field_label=declared.label)[value.strip()].name
        except KeyError:
            logging.warning('Could not resolve tree option %s; returning the original value', value)

        return value if value is not None else ''


class MultiTreeNode(MultiCheckbox):
    __name__ = 'MultiTreeNode'

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        extra_hint = presentation.hint or dmsg(MessageKey.MULTI_TREE_HINT)
        value_key = (
            MessageKey.COMMENT_REQUIRED_VALUE_REQUIRED
            if declared.effective_required
            else MessageKey.COMMENT_REQUIRED_VALUE_OPTIONAL
        )
        return '\n'.join(
            [dmsg(MessageKey.COMMENT_REQUIRED, value=dmsg(value_key)), dmsg(MessageKey.COMMENT_HINT, value=extra_hint)]
        )

    @classmethod
    def parse_input(cls, value: WorkbookInputValue, field_meta: FieldMetaInfo) -> WorkbookInputValue:
        return super().parse_input(value, field_meta)

    @classmethod
    def normalize_import_value(cls, value: WorkbookInputValue, field_meta: FieldMetaInfo) -> list[str]:
        return super().normalize_import_value(value, field_meta)


SingleTreeNodeCodec = SingleTreeNode
MultiTreeNodeCodec = MultiTreeNode
