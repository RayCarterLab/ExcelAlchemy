"""Resolved Excel-facing field metadata used by runtime components."""

import copy
import datetime
from dataclasses import replace
from functools import cached_property
from typing import Self

from excelalchemy.codecs.field_codec import ExcelFieldCodec
from excelalchemy.field_metadata.constraints import ImportConstraints
from excelalchemy.field_metadata.declaration import DeclaredFieldMeta
from excelalchemy.field_metadata.presentation import WorkbookPresentationMeta
from excelalchemy.field_metadata.runtime import RuntimeFieldBinding
from excelalchemy.messages import MessageKey
from excelalchemy.messages import message as msg
from excelalchemy.primitives.constants import (
    DEFAULT_FIELD_META_ORDER,
    MULTI_CHECKBOX_SEPARATOR,
    CharacterSet,
    DataRangeOption,
    DateFormat,
    Option,
)
from excelalchemy.primitives.identity import Key, Label, OptionId, UniqueKey, UniqueLabel


def _normalize_character_set(character_set: set[CharacterSet] | None) -> frozenset[CharacterSet]:
    return frozenset(character_set or set(CharacterSet))


def _normalize_options(options: list[Option] | tuple[Option, ...] | None) -> tuple[Option, ...] | None:
    if options is None:
        return None
    return tuple(options)


class FieldMetaInfo:
    """Resolved Excel column metadata used by the runtime.

    Public 3.0 declarations use ``Annotated[T, ExcelColumn(...)]``. Schema
    extraction resolves those declarations into this object, which keeps the
    runtime-facing state split across:

    - ``DeclaredFieldMeta`` for declaration semantics
    - ``RuntimeFieldBinding`` for flattened runtime identity
    - ``WorkbookPresentationMeta`` for workbook-facing hints and formatting
    - ``ImportConstraints`` for importer-side validation hints

    New code should prefer these layer objects over treating ``FieldMetaInfo``
    as a flat mutable record.
    """

    def __init__(
        self,
        *,
        label: str | Label,
        is_primary_key: bool = False,
        unique: bool = False,
        ignore_import: bool = False,
        required: bool | None = None,
        order: int = DEFAULT_FIELD_META_ORDER,
        character_set: set[CharacterSet] | None = None,
        fraction_digits: int | None = None,
        timezone: datetime.timezone | None = None,
        date_format: DateFormat | None = None,
        date_range_option: DataRangeOption | None = None,
        options: list[Option] | None = None,
        unit: str | None = None,
        hint: str | None = None,
        example_value: str | None = None,
        choice_entity_name: str | None = None,
        choice_entity_name_plural: str | None = None,
        choice_include_options_in_comment: bool | None = None,
        choice_include_mode_in_comment: bool | None = None,
        choice_separator: str | None = None,
        ge: float | None = None,
        le: float | None = None,
        max_digits: int | None = None,
        decimal_places: int | None = None,
        min_items: int | None = None,
        max_items: int | None = None,
        unique_items: bool | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
    ) -> None:
        self.declared_meta = DeclaredFieldMeta(
            label=Label(label),
            is_primary_key=is_primary_key,
            unique=unique or is_primary_key,
            ignore_import=ignore_import,
            required=required,
            order=order,
        )
        self.runtime_binding = RuntimeFieldBinding()
        self.presentation_meta = WorkbookPresentationMeta(
            character_set=_normalize_character_set(character_set),
            fraction_digits=fraction_digits,
            timezone=timezone or datetime.timezone(datetime.timedelta(hours=8), 'CST'),
            date_format=date_format,
            date_range_option=date_range_option,
            options=_normalize_options(options),
            unit=unit,
            hint=hint,
            example_value=example_value,
            choice_entity_name=choice_entity_name,
            choice_entity_name_plural=choice_entity_name_plural,
            choice_include_options_in_comment=(
                True if choice_include_options_in_comment is None else choice_include_options_in_comment
            ),
            choice_include_mode_in_comment=(
                True if choice_include_mode_in_comment is None else choice_include_mode_in_comment
            ),
            choice_separator=choice_separator or MULTI_CHECKBOX_SEPARATOR,
        )
        self.import_constraints = ImportConstraints(
            ge=ge,
            le=le,
            max_digits=max_digits,
            decimal_places=decimal_places,
            min_items=min_items,
            max_items=max_items,
            unique_items=unique_items,
            min_length=min_length,
            max_length=max_length,
        )

    def clone(self) -> Self:
        return copy.deepcopy(self)

    def inherited_from(self, parent: Self) -> Self:
        runtime = self.clone()
        runtime.order = parent.order
        runtime.character_set = runtime.character_set or parent.character_set
        runtime.fraction_digits = runtime.fraction_digits or parent.fraction_digits
        runtime.timezone = runtime.timezone or parent.timezone
        runtime.date_format = runtime.date_format or parent.date_format
        runtime.date_range_option = runtime.date_range_option or parent.date_range_option
        runtime.unit = runtime.unit or parent.unit
        return runtime

    def bind_runtime(
        self,
        *,
        required: bool,
        excel_codec: type[ExcelFieldCodec],
        parent_label: Label,
        parent_key: Key,
        key: Key,
        offset: int,
    ) -> Self:
        runtime = self.clone()
        runtime.required = required
        runtime.excel_codec = excel_codec
        runtime.parent_label = parent_label
        runtime.parent_key = parent_key
        runtime.key = key
        runtime.offset = offset
        return runtime

    @property
    def declared(self) -> DeclaredFieldMeta:
        return self.declared_meta

    @property
    def runtime(self) -> RuntimeFieldBinding:
        return self.runtime_binding

    @property
    def presentation(self) -> WorkbookPresentationMeta:
        return self.presentation_meta

    @property
    def constraints(self) -> ImportConstraints:
        return self.import_constraints

    @property
    def excel_codec(self) -> type[ExcelFieldCodec]:
        return self.runtime_binding.excel_codec

    @excel_codec.setter
    def excel_codec(self, value: type[ExcelFieldCodec]) -> None:
        self.runtime_binding = replace(self.runtime_binding, excel_codec=value)

    def set_is_primary_key(self, is_primary_key: bool | None) -> None:
        if is_primary_key is None:
            return
        self.is_primary_key = is_primary_key
        if self.is_primary_key:
            self.unique = True
            self.required = True

    def set_unique(self, unique: bool | None) -> None:
        if unique is None:
            return
        self.unique = unique
        if self.unique:
            self.required = True

    def validate_state(self) -> None:
        if self.is_primary_key and not self.unique:
            raise ValueError(msg(MessageKey.PRIMARY_KEY_MUST_BE_UNIQUE))
        if (self.is_primary_key or self.unique) and self.required is False:
            raise ValueError(msg(MessageKey.PRIMARY_KEY_AND_UNIQUE_MUST_BE_REQUIRED))

    def exchange_option_ids_to_names(self, option_ids: list[str] | list[OptionId]) -> list[str]:
        return self.presentation_meta.exchange_option_ids_to_names(option_ids, field_label=self.label)

    def exchange_names_to_option_ids_with_errors(self, names: list[str]) -> tuple[list[str], list[str]]:
        return self.presentation_meta.exchange_names_to_option_ids_with_errors(names, field_label=self.label)

    @property
    def unique_label(self) -> UniqueLabel:
        return self.runtime_binding.make_unique_label(label=self.label)

    @property
    def unique_key(self) -> UniqueKey:
        return self.runtime_binding.make_unique_key(key=self.key)

    @cached_property
    def options_id_map(self) -> dict[OptionId, Option]:
        return self.presentation_meta.options_id_map(field_label=self.label)

    @cached_property
    def options_name_map(self) -> dict[str, Option]:
        return self.presentation_meta.options_name_map(field_label=self.label)

    @property
    def comment_required(self) -> str:
        return self.declared_meta.comment_required

    @property
    def comment_date_format(self) -> str:
        return self.presentation_meta.comment_date_format

    @property
    def comment_date_range_option(self) -> str:
        return self.presentation_meta.comment_date_range_option

    @property
    def comment_hint(self) -> str:
        return self.presentation_meta.comment_hint

    @property
    def comment_example(self) -> str:
        return self.presentation_meta.comment_example

    @property
    def comment_options(self) -> str:
        return self.presentation_meta.comment_options

    @property
    def comment_fraction_digits(self) -> str:
        return self.presentation_meta.comment_fraction_digits

    @property
    def comment_unit(self) -> str:
        return self.presentation_meta.comment_unit

    @property
    def comment_unique(self) -> str:
        return self.declared_meta.comment_unique

    @property
    def comment_max_length(self) -> str:
        return self.import_constraints.comment_max_length

    @property
    def must_date_format(self) -> DateFormat:
        return self.presentation_meta.must_date_format

    @property
    def python_date_format(self) -> str:
        return self.presentation_meta.python_date_format

    def __repr__(self) -> str:
        return (
            f'ExcelColumn(label={self.label!r}, '
            f'order={self.order!r}, '
            f'excel_codec={self.excel_codec.__name__!r}, '
            f'required={self.required!r}, '
            f'unique={self.unique!r}, '
            f'comment_required={self.comment_required!r}, '
            f'comment_unique={self.comment_unique!r})'
        )

    __str__ = __repr__

    @property
    def label(self) -> Label:
        return self.declared_meta.label

    @label.setter
    def label(self, value: str | Label) -> None:
        self.declared_meta = replace(self.declared_meta, label=Label(value))

    @property
    def is_primary_key(self) -> bool:
        return self.declared_meta.is_primary_key

    @is_primary_key.setter
    def is_primary_key(self, value: bool) -> None:
        self.declared_meta = replace(self.declared_meta, is_primary_key=value)

    @property
    def unique(self) -> bool:
        return self.declared_meta.unique

    @unique.setter
    def unique(self, value: bool) -> None:
        self.declared_meta = replace(self.declared_meta, unique=value)

    @property
    def ignore_import(self) -> bool:
        return self.declared_meta.ignore_import

    @ignore_import.setter
    def ignore_import(self, value: bool) -> None:
        self.declared_meta = replace(self.declared_meta, ignore_import=value)

    @property
    def required(self) -> bool | None:
        return self.declared_meta.required

    @required.setter
    def required(self, value: bool | None) -> None:
        self.declared_meta = replace(self.declared_meta, required=value)

    @property
    def order(self) -> int:
        return self.declared_meta.order

    @order.setter
    def order(self, value: int) -> None:
        self.declared_meta = replace(self.declared_meta, order=value)

    @property
    def parent_label(self) -> Label | None:
        return self.runtime_binding.parent_label

    @parent_label.setter
    def parent_label(self, value: Label | None) -> None:
        self.runtime_binding = replace(self.runtime_binding, parent_label=value)

    @property
    def key(self) -> Key | None:
        return self.runtime_binding.key

    @key.setter
    def key(self, value: Key | None) -> None:
        self.runtime_binding = replace(self.runtime_binding, key=value)

    @property
    def parent_key(self) -> Key | None:
        return self.runtime_binding.parent_key

    @parent_key.setter
    def parent_key(self, value: Key | None) -> None:
        self.runtime_binding = replace(self.runtime_binding, parent_key=value)

    @property
    def offset(self) -> int:
        return self.runtime_binding.offset

    @offset.setter
    def offset(self, value: int) -> None:
        self.runtime_binding = replace(self.runtime_binding, offset=value)

    @property
    def character_set(self) -> set[CharacterSet]:
        return set(self.presentation_meta.character_set)

    @character_set.setter
    def character_set(self, value: set[CharacterSet]) -> None:
        self.presentation_meta = replace(self.presentation_meta, character_set=_normalize_character_set(value))

    @property
    def fraction_digits(self) -> int | None:
        return self.presentation_meta.fraction_digits

    @fraction_digits.setter
    def fraction_digits(self, value: int | None) -> None:
        self.presentation_meta = replace(self.presentation_meta, fraction_digits=value)

    @property
    def timezone(self) -> datetime.timezone:
        return self.presentation_meta.timezone

    @timezone.setter
    def timezone(self, value: datetime.timezone) -> None:
        self.presentation_meta = replace(self.presentation_meta, timezone=value)

    @property
    def date_format(self) -> DateFormat | None:
        return self.presentation_meta.date_format

    @date_format.setter
    def date_format(self, value: DateFormat | None) -> None:
        self.presentation_meta = replace(self.presentation_meta, date_format=value)

    @property
    def date_range_option(self) -> DataRangeOption | None:
        return self.presentation_meta.date_range_option

    @date_range_option.setter
    def date_range_option(self, value: DataRangeOption | None) -> None:
        self.presentation_meta = replace(self.presentation_meta, date_range_option=value)

    @property
    def options(self) -> list[Option] | None:
        if self.presentation_meta.options is None:
            return None
        return list(self.presentation_meta.options)

    @options.setter
    def options(self, value: list[Option] | None) -> None:
        self.presentation_meta = replace(self.presentation_meta, options=_normalize_options(value))

    @property
    def unit(self) -> str | None:
        return self.presentation_meta.unit

    @unit.setter
    def unit(self, value: str | None) -> None:
        self.presentation_meta = replace(self.presentation_meta, unit=value)

    @property
    def hint(self) -> str | None:
        return self.presentation_meta.hint

    @hint.setter
    def hint(self, value: str | None) -> None:
        self.presentation_meta = replace(self.presentation_meta, hint=value)

    @property
    def example_value(self) -> str | None:
        return self.presentation_meta.example_value

    @example_value.setter
    def example_value(self, value: str | None) -> None:
        self.presentation_meta = replace(self.presentation_meta, example_value=value)

    @property
    def importer_ge(self) -> float | None:
        return self.import_constraints.ge

    @importer_ge.setter
    def importer_ge(self, value: float | None) -> None:
        self.import_constraints = replace(self.import_constraints, ge=value)

    @property
    def importer_le(self) -> float | None:
        return self.import_constraints.le

    @importer_le.setter
    def importer_le(self, value: float | None) -> None:
        self.import_constraints = replace(self.import_constraints, le=value)

    @property
    def importer_max_digits(self) -> int | None:
        return self.import_constraints.max_digits

    @importer_max_digits.setter
    def importer_max_digits(self, value: int | None) -> None:
        self.import_constraints = replace(self.import_constraints, max_digits=value)

    @property
    def importer_decimal_places(self) -> int | None:
        return self.import_constraints.decimal_places

    @importer_decimal_places.setter
    def importer_decimal_places(self, value: int | None) -> None:
        self.import_constraints = replace(self.import_constraints, decimal_places=value)

    @property
    def importer_min_length(self) -> int | None:
        return self.import_constraints.min_length

    @importer_min_length.setter
    def importer_min_length(self, value: int | None) -> None:
        self.import_constraints = replace(self.import_constraints, min_length=value)

    @property
    def importer_max_length(self) -> int | None:
        return self.import_constraints.max_length

    @importer_max_length.setter
    def importer_max_length(self, value: int | None) -> None:
        self.import_constraints = replace(self.import_constraints, max_length=value)

    @property
    def importer_min_items(self) -> int | None:
        return self.import_constraints.min_items

    @importer_min_items.setter
    def importer_min_items(self, value: int | None) -> None:
        self.import_constraints = replace(self.import_constraints, min_items=value)

    @property
    def importer_max_items(self) -> int | None:
        return self.import_constraints.max_items

    @importer_max_items.setter
    def importer_max_items(self, value: int | None) -> None:
        self.import_constraints = replace(self.import_constraints, max_items=value)

    @property
    def importer_unique_items(self) -> bool | None:
        return self.import_constraints.unique_items

    @importer_unique_items.setter
    def importer_unique_items(self, value: bool | None) -> None:
        self.import_constraints = replace(self.import_constraints, unique_items=value)


__all__ = ['FieldMetaInfo']
