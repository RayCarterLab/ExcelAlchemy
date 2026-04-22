from excelalchemy._primitives.constants import MULTI_CHECKBOX_SEPARATOR
from excelalchemy._primitives.identity import OptionId
from excelalchemy.codecs.base import (
    ExcelFieldCodec,
    WorkbookDisplayValue,
    WorkbookInputValue,
    log_codec_missing_options,
    log_codec_option_resolution_fallback,
)
from excelalchemy.exceptions import ProgrammaticError
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.i18n.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo


class Radio(ExcelFieldCodec, str):
    __name__ = 'SingleChoice'

    @classmethod
    def selection_entity_singular(cls) -> str | None:
        return None

    @classmethod
    def _options_preview(cls, field_meta: FieldMetaInfo, *, limit: int = 5) -> str | None:
        options = field_meta.presentation.options
        if not options:
            return None
        preview = MULTI_CHECKBOX_SEPARATOR.join(option.name for option in options[:limit])
        if len(options) > limit:
            preview = f'{preview}{MULTI_CHECKBOX_SEPARATOR}...'
        return preview

    @classmethod
    def _compose_selection_message(cls, field_meta: FieldMetaInfo) -> str:
        entity = cls.selection_entity_singular()
        if entity is None:
            base_message = msg(MessageKey.SELECT_ONE_CONFIGURED_OPTION)
        else:
            base_message = msg(MessageKey.SELECT_ONE_CONFIGURED_ENTITY, entity=entity)

        preview = cls._options_preview(field_meta)
        if preview is None:
            return base_message
        return f'{base_message}. {msg(MessageKey.VALID_VALUES_INCLUDE, options=preview)}'

    @classmethod
    def expected_input_message(cls, field_meta: FieldMetaInfo) -> str | None:
        return cls._compose_selection_message(field_meta)

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        if not presentation.options:
            log_codec_missing_options(cls.__name__, field_label=declared.label)

        return '\n'.join(
            [
                declared.comment_required,
                presentation.comment_options,
                dmsg(MessageKey.COMMENT_SELECTION_MODE, value=dmsg(MessageKey.COMMENT_SELECTION_VALUE_SINGLE)),
                presentation.comment_hint,
                *([presentation.comment_example] if presentation.comment_example else []),
            ]
        )

    @classmethod
    def parse_input(cls, value: WorkbookInputValue, field_meta: FieldMetaInfo) -> str:
        return str(value).strip()

    @classmethod
    def format_display_value(cls, value: WorkbookDisplayValue | None, field_meta: FieldMetaInfo) -> str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        if value is None or value == '':
            return ''

        try:
            return presentation.options_id_map(field_label=declared.label)[value.strip()].name
        except Exception as exc:
            log_codec_option_resolution_fallback(cls.__name__, value, field_label=declared.label, exc=exc)
        return value if value is not None else ''

    @classmethod
    def normalize_import_value(cls, value: str, field_meta: FieldMetaInfo) -> OptionId | str:  # return Option.id
        declared = field_meta.declared
        presentation = field_meta.presentation
        if MULTI_CHECKBOX_SEPARATOR in value:
            raise ValueError(cls._compose_selection_message(field_meta))

        parsed = value.strip()

        if presentation.options is None:
            raise ProgrammaticError(msg(MessageKey.OPTIONS_CANNOT_BE_NONE_FOR_SELECTION_FIELDS))

        if not presentation.options:  # empty
            log_codec_missing_options(cls.__name__, field_label=declared.label)
            return parsed

        options_id_map = presentation.options_id_map(field_label=declared.label)
        if parsed in options_id_map:
            return parsed

        options_name_map = presentation.options_name_map(field_label=declared.label)
        if parsed not in options_name_map:
            raise ValueError(cls._compose_selection_message(field_meta))

        return options_name_map[parsed].id


SingleChoiceCodec = Radio
