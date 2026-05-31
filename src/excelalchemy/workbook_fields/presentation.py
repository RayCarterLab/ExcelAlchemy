"""Workbook-facing field presentation and comment metadata."""

import datetime
from dataclasses import dataclass, field

from excelalchemy.diagnostics import (
    log_metadata_large_option_set,
    log_metadata_missing_option_id,
)
from excelalchemy.errors import ConfigError
from excelalchemy.messages import MessageKey
from excelalchemy.messages import display_message as dmsg
from excelalchemy.messages import message as msg
from excelalchemy.primitives.constants import (
    DATE_FORMAT_TO_HINT_MAPPING,
    DATE_FORMAT_TO_PYTHON_MAPPING,
    MAX_OPTIONS_COUNT,
    MULTI_CHECKBOX_SEPARATOR,
    CharacterSet,
    DataRangeOption,
    DateFormat,
    Option,
)
from excelalchemy.primitives.identity import Label, OptionId


@dataclass(slots=True, frozen=True)
class WorkbookPresentationMeta:
    """Workbook-facing comment and formatting metadata."""

    character_set: frozenset[CharacterSet] = field(default_factory=lambda: frozenset(CharacterSet))
    fraction_digits: int | None = None
    timezone: datetime.timezone = field(default_factory=lambda: datetime.timezone(datetime.timedelta(hours=8), 'CST'))
    date_format: DateFormat | None = None
    date_range_option: DataRangeOption | None = None
    options: tuple[Option, ...] | None = None
    unit: str | None = None
    hint: str | None = None
    example_value: str | None = None
    choice_entity_name: str | None = None
    choice_entity_name_plural: str | None = None
    choice_include_options_in_comment: bool = True
    choice_include_mode_in_comment: bool = True
    choice_separator: str = MULTI_CHECKBOX_SEPARATOR

    @property
    def comment_date_format(self) -> str:
        if self.date_format is None:
            return ''
        return dmsg(MessageKey.COMMENT_DATE_FORMAT, value=DATE_FORMAT_TO_HINT_MAPPING[self.date_format])

    @property
    def comment_date_range_option(self) -> str:
        if self.date_range_option is None:
            return dmsg(MessageKey.COMMENT_DATE_RANGE_OPTION, value=dmsg(MessageKey.DATE_RANGE_OPTION_NONE_DISPLAY))
        option_mapping = {
            DataRangeOption.PRE: MessageKey.DATE_RANGE_OPTION_PRE_DISPLAY,
            DataRangeOption.NEXT: MessageKey.DATE_RANGE_OPTION_NEXT_DISPLAY,
            DataRangeOption.NONE: MessageKey.DATE_RANGE_OPTION_NONE_DISPLAY,
        }
        return dmsg(MessageKey.COMMENT_DATE_RANGE_OPTION, value=dmsg(option_mapping[self.date_range_option]))

    @property
    def comment_hint(self) -> str:
        if self.hint is None:
            return ''
        return dmsg(MessageKey.COMMENT_HINT, value=self.hint)

    @property
    def comment_example(self) -> str:
        if self.example_value is None or not self.example_value.strip():
            return ''
        return dmsg(MessageKey.COMMENT_EXAMPLE, value=self.example_value)

    @property
    def comment_options(self) -> str:
        if self.options is None:
            return ''
        return dmsg(
            MessageKey.COMMENT_OPTIONS, value=MULTI_CHECKBOX_SEPARATOR.join(option.name for option in self.options)
        )

    @property
    def comment_fraction_digits(self) -> str:
        return dmsg(MessageKey.COMMENT_FRACTION_DIGITS, value=self.fraction_digits or 0)

    @property
    def comment_unit(self) -> str:
        return dmsg(MessageKey.COMMENT_UNIT, value=self.unit or dmsg(MessageKey.COMMENT_UNIT_VALUE_NONE))

    @property
    def must_date_format(self) -> DateFormat:
        if self.date_format is None:
            raise ConfigError(msg(MessageKey.DATE_FORMAT_EMPTY_RUNTIME))
        return self.date_format

    @property
    def python_date_format(self) -> str:
        return DATE_FORMAT_TO_PYTHON_MAPPING[self.must_date_format]

    def options_id_map(self, *, field_label: Label) -> dict[OptionId, Option]:
        if self.options is None:
            return {}
        if len(self.options) > MAX_OPTIONS_COUNT:
            log_metadata_large_option_set(field_label=str(field_label), option_count=len(self.options))
        return {option.id: option for option in self.options}

    def options_name_map(self, *, field_label: Label) -> dict[str, Option]:
        if self.options is None:
            return {}
        if len(self.options) > MAX_OPTIONS_COUNT:
            log_metadata_large_option_set(field_label=str(field_label), option_count=len(self.options))
        return {option.name: option for option in self.options}

    def exchange_option_ids_to_names(
        self,
        option_ids: list[str] | list[OptionId],
        *,
        field_label: Label,
    ) -> list[str]:
        option_id_map = self.options_id_map(field_label=field_label)
        option_names: list[str] = []

        for option_id in option_ids:
            normalized_id = OptionId(option_id)
            try:
                option_names.append(option_id_map[normalized_id].name)
            except KeyError:
                log_metadata_missing_option_id(option_id=str(normalized_id), field_label=str(field_label))
                option_names.append(normalized_id)

        return option_names

    def exchange_names_to_option_ids_with_errors(
        self,
        names: list[str],
        *,
        field_label: Label,
    ) -> tuple[list[str], list[str]]:
        option_name_map = self.options_name_map(field_label=field_label)
        errors: list[str] = []
        result: list[str] = []
        for name in names:
            option = option_name_map.get(name)
            if option is None:
                errors.append(msg(MessageKey.OPTION_NOT_FOUND_HEADER_COMMENT))
            else:
                result.append(option.id)
        return result, errors


__all__ = ['WorkbookPresentationMeta']
