"""Excel metadata definitions decoupled from Pydantic internals."""

import copy
import datetime
import logging
from collections.abc import Callable, Mapping, Set
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Self, cast

from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from excelalchemy._primitives.constants import (
    DATE_FORMAT_TO_HINT_MAPPING,
    DATE_FORMAT_TO_PYTHON_MAPPING,
    DEFAULT_FIELD_META_ORDER,
    MAX_OPTIONS_COUNT,
    MULTI_CHECKBOX_SEPARATOR,
    UNIQUE_HEADER_CONNECTOR,
    CharacterSet,
    DataRangeOption,
    DateFormat,
    IntStr,
    Option,
)
from excelalchemy._primitives.identity import Key, Label, OptionId, UniqueKey, UniqueLabel
from excelalchemy.codecs.base import ExcelFieldCodec, UndefinedFieldCodec
from excelalchemy.exceptions import ConfigError, ProgrammaticError
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.i18n.messages import message as msg

EXCEL_FIELD_METADATA_KEY = 'excelalchemy_metadata'
type FieldDefaultFactory = Callable[[], object]
type FieldIncludeExclude = Set[IntStr] | bool | None


class PatchFieldMeta(BaseModel):
    unique: bool | None = False  # Workbook hint only. Runtime uniqueness is enforced elsewhere.
    is_primary_key: bool | None = False  # Workbook hint only. Runtime primary-key behavior is configured separately.
    hint: str | None = None  # Workbook-facing help text rendered into header comments.
    options: list[Option] | None = None


@dataclass(slots=True)
class DeclaredFieldMeta:
    """Static workbook field declaration supplied by user code."""

    label: Label
    is_primary_key: bool
    unique: bool
    ignore_import: bool
    required: bool | None
    order: int


@dataclass(slots=True)
class RuntimeFieldBinding:
    """Runtime identity assigned after schema extraction flattens the model."""

    parent_label: Label | None = None
    key: Key | None = None
    parent_key: Key | None = None
    offset: int = DEFAULT_FIELD_META_ORDER
    excel_codec: type[ExcelFieldCodec] = UndefinedFieldCodec


@dataclass(slots=True)
class WorkbookPresentationMeta:
    """Workbook-facing comment and formatting metadata."""

    character_set: set[CharacterSet] = field(default_factory=lambda: set(CharacterSet))
    fraction_digits: int | None = None
    timezone: datetime.timezone = field(default_factory=lambda: datetime.timezone(datetime.timedelta(hours=8), 'CST'))
    date_format: DateFormat | None = None
    date_range_option: DataRangeOption | None = None
    options: list[Option] | None = None
    unit: str | None = None
    hint: str | None = None


@dataclass(slots=True)
class ImportConstraints:
    """Importer-side validation hints mirrored from Pydantic constraints."""

    ge: float | None = None
    le: float | None = None
    max_digits: int | None = None
    decimal_places: int | None = None
    min_items: int | None = None
    max_items: int | None = None
    unique_items: bool | None = None
    min_length: int | None = None
    max_length: int | None = None


class FieldMetaInfo:
    """Excel field metadata independent from any validation backend."""

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
            character_set=character_set or set(CharacterSet),
            fraction_digits=fraction_digits,
            timezone=timezone or datetime.timezone(datetime.timedelta(hours=8), 'CST'),
            date_format=date_format,
            date_range_option=date_range_option,
            options=options,
            unit=unit,
            hint=hint,
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
    def excel_codec(self) -> type[ExcelFieldCodec]:
        return self.runtime_binding.excel_codec

    @excel_codec.setter
    def excel_codec(self, value: type[ExcelFieldCodec]) -> None:
        self.runtime_binding.excel_codec = value

    @property
    def value_type(self) -> type[ExcelFieldCodec]:
        """Backward-compatible alias for excel_codec."""
        return self.excel_codec

    @value_type.setter
    def value_type(self, value: type[ExcelFieldCodec]) -> None:
        self.excel_codec = value

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
        option_names: list[str] = []

        for option_id in option_ids:
            option_id = OptionId(option_id)
            try:
                option_names.append(self.options_id_map[option_id].name)
            except KeyError:
                logging.warning('Could not find option id %s; returning the original value', option_id)
                option_names.append(option_id)

        return option_names

    def exchange_names_to_option_ids_with_errors(self, names: list[str]) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        result: list[str] = []
        for name in names:
            option = self.options_name_map.get(name)
            if option is None:
                errors.append(msg(MessageKey.OPTION_NOT_FOUND_HEADER_COMMENT))
            else:
                result.append(option.id)
        return result, errors

    @property
    def unique_label(self) -> UniqueLabel:
        if self.parent_label is None:
            raise RuntimeError(msg(MessageKey.PARENT_LABEL_EMPTY_RUNTIME))
        label = (
            f'{self.parent_label}{UNIQUE_HEADER_CONNECTOR}{self.label}'
            if self.parent_label != self.label
            else self.label
        )
        return UniqueLabel(label)

    @property
    def unique_key(self) -> UniqueKey:
        if self.parent_key is None:
            raise RuntimeError(msg(MessageKey.PARENT_KEY_EMPTY_RUNTIME))
        if self.key is None:
            raise RuntimeError(msg(MessageKey.KEY_EMPTY_RUNTIME))
        key = f'{self.parent_key}{UNIQUE_HEADER_CONNECTOR}{self.key}' if self.parent_key != self.key else self.key
        return UniqueKey(key)

    @cached_property
    def options_id_map(self) -> dict[OptionId, Option]:
        if self.options is None:
            return {}
        if len(self.options) > MAX_OPTIONS_COUNT:
            logging.warning(
                'Field "%s" defines %s options; please confirm that this is intentional because options are not meant for large datasets',
                self.label,
                len(self.options),
            )
        return {option.id: option for option in self.options}

    @cached_property
    def options_name_map(self) -> dict[str, Option]:
        if self.options is None:
            return {}
        if len(self.options) > MAX_OPTIONS_COUNT:
            logging.warning(
                'Field "%s" defines %s options; please confirm that this is intentional because options are not meant for large datasets',
                self.label,
                len(self.options),
            )
        return {option.name: option for option in self.options}

    @property
    def comment_required(self) -> str:
        value_key = (
            MessageKey.COMMENT_REQUIRED_VALUE_REQUIRED if self.required else MessageKey.COMMENT_REQUIRED_VALUE_OPTIONAL
        )
        return dmsg(MessageKey.COMMENT_REQUIRED, value=dmsg(value_key))

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
    def comment_options(self) -> str:
        if self.options is None:
            return ''
        return dmsg(MessageKey.COMMENT_OPTIONS, value=MULTI_CHECKBOX_SEPARATOR.join(x.name for x in self.options))

    @property
    def comment_fraction_digits(self) -> str:
        return dmsg(MessageKey.COMMENT_FRACTION_DIGITS, value=self.fraction_digits or 0)

    @property
    def comment_unit(self) -> str:
        return dmsg(MessageKey.COMMENT_UNIT, value=self.unit or dmsg(MessageKey.COMMENT_UNIT_VALUE_NONE))

    @property
    def comment_unique(self) -> str:
        value_key = (
            MessageKey.COMMENT_UNIQUE_VALUE_UNIQUE if self.unique else MessageKey.COMMENT_UNIQUE_VALUE_NON_UNIQUE
        )
        return dmsg(MessageKey.COMMENT_UNIQUE, value=dmsg(value_key))

    @property
    def comment_max_length(self) -> str:
        return dmsg(
            MessageKey.COMMENT_MAX_LENGTH,
            value=self.importer_max_length or dmsg(MessageKey.COMMENT_MAX_LENGTH_VALUE_UNLIMITED),
        )

    @property
    def must_date_format(self) -> DateFormat:
        if self.date_format is None:
            raise ConfigError(msg(MessageKey.DATE_FORMAT_EMPTY_RUNTIME))
        return self.date_format

    @property
    def python_date_format(self) -> str:
        return DATE_FORMAT_TO_PYTHON_MAPPING[self.must_date_format]

    def __repr__(self) -> str:
        return (
            f'FieldMeta(label={self.label!r}, '
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
        self.declared_meta.label = Label(value)

    @property
    def is_primary_key(self) -> bool:
        return self.declared_meta.is_primary_key

    @is_primary_key.setter
    def is_primary_key(self, value: bool) -> None:
        self.declared_meta.is_primary_key = value

    @property
    def unique(self) -> bool:
        return self.declared_meta.unique

    @unique.setter
    def unique(self, value: bool) -> None:
        self.declared_meta.unique = value

    @property
    def ignore_import(self) -> bool:
        return self.declared_meta.ignore_import

    @ignore_import.setter
    def ignore_import(self, value: bool) -> None:
        self.declared_meta.ignore_import = value

    @property
    def required(self) -> bool | None:
        return self.declared_meta.required

    @required.setter
    def required(self, value: bool | None) -> None:
        self.declared_meta.required = value

    @property
    def order(self) -> int:
        return self.declared_meta.order

    @order.setter
    def order(self, value: int) -> None:
        self.declared_meta.order = value

    @property
    def parent_label(self) -> Label | None:
        return self.runtime_binding.parent_label

    @parent_label.setter
    def parent_label(self, value: Label | None) -> None:
        self.runtime_binding.parent_label = value

    @property
    def key(self) -> Key | None:
        return self.runtime_binding.key

    @key.setter
    def key(self, value: Key | None) -> None:
        self.runtime_binding.key = value

    @property
    def parent_key(self) -> Key | None:
        return self.runtime_binding.parent_key

    @parent_key.setter
    def parent_key(self, value: Key | None) -> None:
        self.runtime_binding.parent_key = value

    @property
    def offset(self) -> int:
        return self.runtime_binding.offset

    @offset.setter
    def offset(self, value: int) -> None:
        self.runtime_binding.offset = value

    @property
    def character_set(self) -> set[CharacterSet]:
        return self.presentation_meta.character_set

    @character_set.setter
    def character_set(self, value: set[CharacterSet]) -> None:
        self.presentation_meta.character_set = value

    @property
    def fraction_digits(self) -> int | None:
        return self.presentation_meta.fraction_digits

    @fraction_digits.setter
    def fraction_digits(self, value: int | None) -> None:
        self.presentation_meta.fraction_digits = value

    @property
    def timezone(self) -> datetime.timezone:
        return self.presentation_meta.timezone

    @timezone.setter
    def timezone(self, value: datetime.timezone) -> None:
        self.presentation_meta.timezone = value

    @property
    def date_format(self) -> DateFormat | None:
        return self.presentation_meta.date_format

    @date_format.setter
    def date_format(self, value: DateFormat | None) -> None:
        self.presentation_meta.date_format = value

    @property
    def date_range_option(self) -> DataRangeOption | None:
        return self.presentation_meta.date_range_option

    @date_range_option.setter
    def date_range_option(self, value: DataRangeOption | None) -> None:
        self.presentation_meta.date_range_option = value

    @property
    def options(self) -> list[Option] | None:
        return self.presentation_meta.options

    @options.setter
    def options(self, value: list[Option] | None) -> None:
        self.presentation_meta.options = value

    @property
    def unit(self) -> str | None:
        return self.presentation_meta.unit

    @unit.setter
    def unit(self, value: str | None) -> None:
        self.presentation_meta.unit = value

    @property
    def hint(self) -> str | None:
        return self.presentation_meta.hint

    @hint.setter
    def hint(self, value: str | None) -> None:
        self.presentation_meta.hint = value

    @property
    def importer_ge(self) -> float | None:
        return self.import_constraints.ge

    @importer_ge.setter
    def importer_ge(self, value: float | None) -> None:
        self.import_constraints.ge = value

    @property
    def importer_le(self) -> float | None:
        return self.import_constraints.le

    @importer_le.setter
    def importer_le(self, value: float | None) -> None:
        self.import_constraints.le = value

    @property
    def importer_max_digits(self) -> int | None:
        return self.import_constraints.max_digits

    @importer_max_digits.setter
    def importer_max_digits(self, value: int | None) -> None:
        self.import_constraints.max_digits = value

    @property
    def importer_decimal_places(self) -> int | None:
        return self.import_constraints.decimal_places

    @importer_decimal_places.setter
    def importer_decimal_places(self, value: int | None) -> None:
        self.import_constraints.decimal_places = value

    @property
    def importer_min_length(self) -> int | None:
        return self.import_constraints.min_length

    @importer_min_length.setter
    def importer_min_length(self, value: int | None) -> None:
        self.import_constraints.min_length = value

    @property
    def importer_max_length(self) -> int | None:
        return self.import_constraints.max_length

    @importer_max_length.setter
    def importer_max_length(self, value: int | None) -> None:
        self.import_constraints.max_length = value

    @property
    def importer_min_items(self) -> int | None:
        return self.import_constraints.min_items

    @importer_min_items.setter
    def importer_min_items(self, value: int | None) -> None:
        self.import_constraints.min_items = value

    @property
    def importer_max_items(self) -> int | None:
        return self.import_constraints.max_items

    @importer_max_items.setter
    def importer_max_items(self, value: int | None) -> None:
        self.import_constraints.max_items = value

    @property
    def importer_unique_items(self) -> bool | None:
        return self.import_constraints.unique_items

    @importer_unique_items.setter
    def importer_unique_items(self, value: bool | None) -> None:
        self.import_constraints.unique_items = value


def extract_declared_field_metadata(field_info: FieldInfo) -> FieldMetaInfo:
    metadata = _resolve_declared_field_metadata(field_info)
    return _overlay_pydantic_field_constraints(metadata.clone(), field_info)


def _resolve_declared_field_metadata(field_info: FieldInfo) -> FieldMetaInfo:
    for item in field_info.metadata:
        if isinstance(item, FieldMetaInfo):
            return item

    if isinstance(field_info.default, FieldMetaInfo):
        raise ProgrammaticError(
            'Annotated fields must place ExcelMeta(...) inside Annotated metadata; '
            'use `field: Annotated[T, Field(...), ExcelMeta(...)]`'
        )

    json_schema_extra = field_info.json_schema_extra
    if not isinstance(json_schema_extra, Mapping):
        raise ProgrammaticError(msg(MessageKey.FIELD_DEFINITIONS_MUST_USE_FIELDMETA))

    json_schema_mapping = cast(Mapping[str, object], json_schema_extra)
    metadata = json_schema_mapping.get(EXCEL_FIELD_METADATA_KEY)
    if not isinstance(metadata, FieldMetaInfo):
        raise ProgrammaticError(msg(MessageKey.FIELD_DEFINITIONS_MUST_USE_FIELDMETA))
    return metadata


def _overlay_pydantic_field_constraints(metadata: FieldMetaInfo, field_info: FieldInfo) -> FieldMetaInfo:
    for item in field_info.metadata:
        if isinstance(item, FieldMetaInfo):
            continue

        ge = getattr(item, 'ge', None)
        if ge is not None:
            metadata.importer_ge = ge

        le = getattr(item, 'le', None)
        if le is not None:
            metadata.importer_le = le

        max_digits = getattr(item, 'max_digits', None)
        if max_digits is not None:
            metadata.importer_max_digits = max_digits

        decimal_places = getattr(item, 'decimal_places', None)
        if decimal_places is not None:
            metadata.importer_decimal_places = decimal_places

        min_length = getattr(item, 'min_length', None)
        if min_length is not None:
            metadata.importer_min_length = min_length
            metadata.importer_min_items = min_length

        max_length = getattr(item, 'max_length', None)
        if max_length is not None:
            metadata.importer_max_length = max_length
            metadata.importer_max_items = max_length

        unique_items = getattr(item, 'unique_items', None)
        if unique_items is not None:
            metadata.importer_unique_items = unique_items

    return metadata


def _build_excel_metadata(
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
    ge: float | None = None,
    le: float | None = None,
    max_digits: int | None = None,
    decimal_places: int | None = None,
    min_items: int | None = None,
    max_items: int | None = None,
    unique_items: bool | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
) -> FieldMetaInfo:
    return FieldMetaInfo(
        label=label,
        is_primary_key=is_primary_key,
        unique=unique,
        ignore_import=ignore_import,
        required=required,
        order=order,
        character_set=character_set,
        fraction_digits=fraction_digits,
        timezone=timezone,
        date_format=date_format,
        date_range_option=date_range_option,
        options=options,
        unit=unit,
        hint=hint,
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


def ExcelMeta(
    *,
    label: str,
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
    ge: float | None = None,
    le: float | None = None,
    max_digits: int | None = None,
    decimal_places: int | None = None,
    min_items: int | None = None,
    max_items: int | None = None,
    unique_items: bool | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
) -> FieldMetaInfo:
    """Excel-specific metadata for use with Annotated[..., Field(...), ExcelMeta(...)]."""
    return _build_excel_metadata(
        label=label,
        is_primary_key=is_primary_key,
        unique=unique,
        ignore_import=ignore_import,
        required=required,
        order=order,
        character_set=character_set,
        fraction_digits=fraction_digits,
        timezone=timezone,
        date_format=date_format,
        date_range_option=date_range_option,
        options=options,
        unit=unit,
        hint=hint,
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


# pylint: disable=invalid-name
# pylint: disable=too-many-locals
def FieldMeta(
    default: object = PydanticUndefined,
    *,
    label: str,
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
    default_factory: FieldDefaultFactory | None = None,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    exclude: FieldIncludeExclude = None,
    include: FieldIncludeExclude = None,
    const: bool | None = None,
    ge: float | None = None,
    le: float | None = None,
    multiple_of: float | None = None,
    allow_inf_nan: bool | None = None,
    max_digits: int | None = None,
    decimal_places: int | None = None,
    min_items: int | None = None,
    max_items: int | None = None,
    unique_items: bool | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    allow_mutation: bool | None = True,
    regex: str | None = None,
    discriminator: str | None = None,
    repr: bool = True,
    **extra: object,
) -> Any:
    metadata = _build_excel_metadata(
        label=label,
        is_primary_key=is_primary_key,
        unique=unique,
        ignore_import=ignore_import,
        required=required,
        order=order,
        character_set=character_set,
        fraction_digits=fraction_digits,
        timezone=timezone,
        date_format=date_format,
        date_range_option=date_range_option,
        options=options,
        unit=unit,
        hint=hint,
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

    json_schema_extra: dict[str, Any] = {EXCEL_FIELD_METADATA_KEY: metadata} | extra
    if include is not None:
        json_schema_extra['include'] = include
    if const is not None:
        json_schema_extra['const'] = const
    if min_items is not None:
        json_schema_extra['min_items'] = min_items
    if max_items is not None:
        json_schema_extra['max_items'] = max_items
    if unique_items is not None:
        json_schema_extra['unique_items'] = unique_items

    field_kwargs: dict[str, Any] = {
        'repr': repr,
        'json_schema_extra': json_schema_extra,
    }
    if default_factory is not None:
        field_kwargs['default_factory'] = default_factory
    if alias is not None:
        field_kwargs['alias'] = alias
    if title is not None:
        field_kwargs['title'] = title
    if description is not None:
        field_kwargs['description'] = description
    if isinstance(exclude, bool):
        field_kwargs['exclude'] = exclude
    if ge is not None:
        field_kwargs['ge'] = ge
    if le is not None:
        field_kwargs['le'] = le
    if multiple_of is not None:
        field_kwargs['multiple_of'] = multiple_of
    if allow_inf_nan is not None:
        field_kwargs['allow_inf_nan'] = allow_inf_nan
    if max_digits is not None:
        field_kwargs['max_digits'] = max_digits
    if decimal_places is not None:
        field_kwargs['decimal_places'] = decimal_places
    if min_length is not None:
        field_kwargs['min_length'] = min_length
    if max_length is not None:
        field_kwargs['max_length'] = max_length
    if regex is not None:
        field_kwargs['pattern'] = regex
    if discriminator is not None:
        field_kwargs['discriminator'] = discriminator
    if allow_mutation is not None and allow_mutation is not True:
        field_kwargs['frozen'] = not allow_mutation

    return Field(default, **field_kwargs)
