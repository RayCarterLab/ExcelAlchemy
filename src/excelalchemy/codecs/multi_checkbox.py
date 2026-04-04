from typing import cast

from excelalchemy._primitives.constants import MULTI_CHECKBOX_SEPARATOR
from excelalchemy._primitives.identity import OptionId
from excelalchemy.codecs.base import ExcelFieldCodec, log_codec_missing_options, log_codec_parse_fallback
from excelalchemy.exceptions import ProgrammaticError
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.i18n.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo


class MultiCheckbox(ExcelFieldCodec, list[str]):
    __name__ = 'MultiChoice'

    @classmethod
    def selection_entity_plural(cls) -> str | None:
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
        entity_plural = cls.selection_entity_plural()
        if entity_plural is None:
            base_message = msg(MessageKey.SELECT_ONLY_CONFIGURED_OPTIONS)
        else:
            base_message = msg(MessageKey.SELECT_ONLY_CONFIGURED_ENTITIES, entity_plural=entity_plural)

        preview = cls._options_preview(field_meta)
        if preview is None:
            return base_message
        return f'{base_message}. {msg(MessageKey.VALID_VALUES_INCLUDE, options=preview)}'

    @classmethod
    def expected_input_message(cls, field_meta: FieldMetaInfo) -> str | None:
        return cls._compose_selection_message(field_meta)

    @staticmethod
    def _coerce_items(value: object) -> list[object] | None:
        if not isinstance(value, list):
            return None
        return cast(list[object], value)

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        return '\n'.join(
            [
                declared.comment_required,
                presentation.comment_options,
                dmsg(MessageKey.COMMENT_SELECTION_MODE, value=dmsg(MessageKey.COMMENT_SELECTION_VALUE_MULTI)),
                presentation.comment_hint,
            ]
        )

    @classmethod
    def parse_input(cls, value: object, field_meta: FieldMetaInfo) -> list[str] | object:
        items = cls._coerce_items(value)
        if items is not None:
            return [str(item).strip() for item in items]

        if isinstance(value, str):
            return [item.strip() for item in value.split(MULTI_CHECKBOX_SEPARATOR)]

        log_codec_parse_fallback(
            cls.__name__,
            value,
            field_label=field_meta.declared.label,
            reason='Expected a delimited string or a list of selected values',
        )
        return value

    @classmethod
    def normalize_import_value(cls, value: object, field_meta: FieldMetaInfo) -> list[str]:  # OptionId
        declared = field_meta.declared
        presentation = field_meta.presentation
        items = cls._coerce_items(value)
        if items is None:
            raise ValueError(cls._compose_selection_message(field_meta))

        parsed = [str(item).strip() for item in items]

        if presentation.options is None:
            raise ProgrammaticError(msg(MessageKey.OPTIONS_CANNOT_BE_NONE_FOR_VALUE_TYPE, value_type=cls.__name__))

        if not presentation.options:  # empty
            log_codec_missing_options(cls.__name__, field_label=declared.label)
            return parsed

        if len(parsed) != len(set(parsed)):
            raise ValueError(msg(MessageKey.OPTIONS_CONTAIN_DUPLICATES))

        result, errors = presentation.exchange_names_to_option_ids_with_errors(parsed, field_label=declared.label)

        if errors:
            raise ValueError(cls._compose_selection_message(field_meta))
        else:
            return result

    @classmethod
    def format_display_value(cls, value: str | list[OptionId] | None, field_meta: FieldMetaInfo) -> str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        match value:
            case None | '':
                return ''
            case str():
                return value
            case list():
                option_ids = [OptionId(option_id) for option_id in value]
                option_names = presentation.exchange_option_ids_to_names(option_ids, field_label=declared.label)
                return f'{MULTI_CHECKBOX_SEPARATOR}'.join(option_names)


MultiChoiceCodec = MultiCheckbox
