from typing import cast

from excelalchemy.codecs.field_codec import (
    ExcelFieldCodec,
    ExcelFieldCodecSpec,
    WorkbookDisplayValue,
    WorkbookInputValue,
    log_codec_missing_options,
    log_codec_option_resolution_fallback,
    log_codec_parse_fallback,
)
from excelalchemy.errors import ProgrammaticError
from excelalchemy.field_metadata import FieldMetaInfo
from excelalchemy.messages import MessageKey
from excelalchemy.messages import display_message as dmsg
from excelalchemy.messages import message as msg
from excelalchemy.primitives.constants import MULTI_CHECKBOX_SEPARATOR
from excelalchemy.primitives.identity import OptionId


class SingleChoiceFieldCodec(ExcelFieldCodec):
    @classmethod
    def _options_preview(cls, field_meta: FieldMetaInfo, *, limit: int = 5) -> str | None:
        options = field_meta.presentation.options
        if not options:
            return None
        preview = field_meta.presentation.choice_separator.join(option.name for option in options[:limit])
        if len(options) > limit:
            preview = f'{preview}{field_meta.presentation.choice_separator}...'
        return preview

    @classmethod
    def _compose_selection_message(cls, field_meta: FieldMetaInfo) -> str:
        entity = field_meta.presentation.choice_entity_name
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
        if presentation.choice_include_options_in_comment and not presentation.options:
            log_codec_missing_options(cls.__name__, field_label=declared.label)

        return '\n'.join(
            [
                declared.comment_required,
                *([presentation.comment_options] if presentation.choice_include_options_in_comment else []),
                *(
                    [dmsg(MessageKey.COMMENT_SELECTION_MODE, value=dmsg(MessageKey.COMMENT_SELECTION_VALUE_SINGLE))]
                    if presentation.choice_include_mode_in_comment
                    else []
                ),
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
    def normalize_import_value(cls, value: str, field_meta: FieldMetaInfo) -> OptionId | str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        if presentation.choice_separator in value:
            raise ValueError(cls._compose_selection_message(field_meta))

        parsed = value.strip()

        if presentation.options is None:
            raise ProgrammaticError(msg(MessageKey.OPTIONS_CANNOT_BE_NONE_FOR_SELECTION_FIELDS))

        if not presentation.options:
            log_codec_missing_options(cls.__name__, field_label=declared.label)
            return parsed

        options_id_map = presentation.options_id_map(field_label=declared.label)
        if parsed in options_id_map:
            return parsed

        options_name_map = presentation.options_name_map(field_label=declared.label)
        if parsed not in options_name_map:
            raise ValueError(cls._compose_selection_message(field_meta))

        return options_name_map[parsed].id


class MultiChoiceFieldCodec(ExcelFieldCodec):
    @classmethod
    def _options_preview(cls, field_meta: FieldMetaInfo, *, limit: int = 5) -> str | None:
        options = field_meta.presentation.options
        if not options:
            return None
        preview = field_meta.presentation.choice_separator.join(option.name for option in options[:limit])
        if len(options) > limit:
            preview = f'{preview}{field_meta.presentation.choice_separator}...'
        return preview

    @classmethod
    def _compose_selection_message(cls, field_meta: FieldMetaInfo) -> str:
        entity_plural = field_meta.presentation.choice_entity_name_plural
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
                *([presentation.comment_options] if presentation.choice_include_options_in_comment else []),
                *(
                    [dmsg(MessageKey.COMMENT_SELECTION_MODE, value=dmsg(MessageKey.COMMENT_SELECTION_VALUE_MULTI))]
                    if presentation.choice_include_mode_in_comment
                    else []
                ),
                presentation.comment_hint,
                *([presentation.comment_example] if presentation.comment_example else []),
            ]
        )

    @classmethod
    def parse_input(cls, value: object, field_meta: FieldMetaInfo) -> list[str] | object:
        items = cls._coerce_items(value)
        if items is not None:
            return [str(item).strip() for item in items]

        if isinstance(value, str):
            return [item.strip() for item in value.split(field_meta.presentation.choice_separator)]

        log_codec_parse_fallback(
            cls.__name__,
            value,
            field_label=field_meta.declared.label,
            reason='Expected a delimited string or a list of selected values',
        )
        return value

    @classmethod
    def normalize_import_value(cls, value: object, field_meta: FieldMetaInfo) -> list[str]:
        declared = field_meta.declared
        presentation = field_meta.presentation
        items = cls._coerce_items(value)
        if items is None:
            raise ValueError(cls._compose_selection_message(field_meta))

        parsed = [str(item).strip() for item in items]

        if presentation.options is None:
            raise ProgrammaticError(msg(MessageKey.OPTIONS_CANNOT_BE_NONE_FOR_VALUE_TYPE, value_type=cls.__name__))

        if not presentation.options:
            log_codec_missing_options(cls.__name__, field_label=declared.label)
            return parsed

        if len(parsed) != len(set(parsed)):
            raise ValueError(msg(MessageKey.OPTIONS_CONTAIN_DUPLICATES))

        result, errors = presentation.exchange_names_to_option_ids_with_errors(parsed, field_label=declared.label)

        if errors:
            raise ValueError(cls._compose_selection_message(field_meta))
        return result

    @classmethod
    def format_display_value(cls, value: str | list[object] | None, field_meta: FieldMetaInfo) -> str:
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
                return presentation.choice_separator.join(option_names)


class SingleChoiceCodec:
    """Factory for explicit single-choice codec configuration."""

    def __new__(
        cls,
        *,
        entity_name: str | None = None,
        hint: str | None = None,
        include_options_in_comment: bool = True,
        include_mode_in_comment: bool = True,
        separator: str = MULTI_CHECKBOX_SEPARATOR,
    ) -> ExcelFieldCodecSpec:
        return ExcelFieldCodecSpec.create(
            SingleChoiceFieldCodec,
            hint=hint,
            choice_entity_name=entity_name,
            choice_include_options_in_comment=include_options_in_comment,
            choice_include_mode_in_comment=include_mode_in_comment,
            choice_separator=separator,
        )


class MultiChoiceCodec:
    """Factory for explicit multi-choice codec configuration."""

    def __new__(
        cls,
        *,
        entity_name_plural: str | None = None,
        hint: str | None = None,
        include_options_in_comment: bool = True,
        include_mode_in_comment: bool = True,
        separator: str = MULTI_CHECKBOX_SEPARATOR,
    ) -> ExcelFieldCodecSpec:
        return ExcelFieldCodecSpec.create(
            MultiChoiceFieldCodec,
            hint=hint,
            choice_entity_name_plural=entity_name_plural,
            choice_include_options_in_comment=include_options_in_comment,
            choice_include_mode_in_comment=include_mode_in_comment,
            choice_separator=separator,
        )
