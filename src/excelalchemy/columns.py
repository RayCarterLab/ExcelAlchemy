"""Column metadata declarations for ExcelAlchemy schemas."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import cast

from excelalchemy.codecs.field_codec import ExcelFieldCodec, ExcelFieldCodecSpec
from excelalchemy.field_metadata import FieldMetaInfo
from excelalchemy.primitives.constants import (
    DEFAULT_FIELD_META_ORDER,
    CharacterSet,
    DataRangeOption,
    DateFormat,
    Option,
)

type ExcelColumnCodec = type[ExcelFieldCodec] | ExcelFieldCodecSpec

_CODEC_COLUMN_OPTION_NAMES = frozenset(
    {
        'fraction_digits',
        'timezone',
        'date_format',
        'date_range_option',
        'unit',
        'hint',
        'choice_entity_name',
        'choice_entity_name_plural',
        'choice_include_options_in_comment',
        'choice_include_mode_in_comment',
        'choice_separator',
    }
)


@dataclass(frozen=True, slots=True)
class ExcelColumnSpec:
    """Immutable Excel-facing column declaration for ``Annotated`` fields."""

    label: str
    codec: ExcelColumnCodec | None = None
    is_primary_key: bool = False
    unique: bool = False
    ignore_import: bool = False
    required: bool | None = None
    order: int = DEFAULT_FIELD_META_ORDER
    character_set: frozenset[CharacterSet] | None = None
    fraction_digits: int | None = None
    timezone: datetime.timezone | None = None
    date_format: DateFormat | None = None
    date_range_option: DataRangeOption | None = None
    options: tuple[Option, ...] | None = None
    unit: str | None = None
    hint: str | None = None
    example_value: str | None = None

    def to_field_metadata(self) -> FieldMetaInfo:
        codec_type, codec_options = _resolve_codec(self.codec)
        metadata = FieldMetaInfo(
            label=self.label,
            is_primary_key=self.is_primary_key,
            unique=self.unique,
            ignore_import=self.ignore_import,
            required=self.required,
            order=self.order,
            character_set=set(self.character_set) if self.character_set is not None else None,
            fraction_digits=_merged_option('fraction_digits', self.fraction_digits, codec_options),
            timezone=_merged_option('timezone', self.timezone, codec_options),
            date_format=_merged_option('date_format', self.date_format, codec_options),
            date_range_option=_merged_option('date_range_option', self.date_range_option, codec_options),
            options=list(self.options) if self.options is not None else None,
            unit=_merged_option('unit', self.unit, codec_options),
            hint=_merged_option('hint', self.hint, codec_options),
            example_value=self.example_value,
            choice_entity_name=_merged_option('choice_entity_name', None, codec_options),
            choice_entity_name_plural=_merged_option('choice_entity_name_plural', None, codec_options),
            choice_include_options_in_comment=_merged_option('choice_include_options_in_comment', None, codec_options),
            choice_include_mode_in_comment=_merged_option('choice_include_mode_in_comment', None, codec_options),
            choice_separator=_merged_option('choice_separator', None, codec_options),
        )
        if codec_type is not None:
            metadata.excel_codec = codec_type
        return metadata


def ExcelColumn(
    *,
    label: str,
    codec: ExcelColumnCodec | None = None,
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
) -> ExcelColumnSpec:
    """Excel-specific metadata for ``Annotated`` model fields.

    ``ExcelColumn`` keeps the Python type annotation as the data contract and
    stores workbook-facing behavior in metadata. Pydantic validation constraints
    should stay in ``pydantic.Field``.
    """
    return ExcelColumnSpec(
        label=label,
        codec=codec,
        is_primary_key=is_primary_key,
        unique=unique,
        ignore_import=ignore_import,
        required=required,
        order=order,
        character_set=frozenset(character_set) if character_set is not None else None,
        fraction_digits=fraction_digits,
        timezone=timezone,
        date_format=date_format,
        date_range_option=date_range_option,
        options=tuple(options) if options is not None else None,
        unit=unit,
        hint=hint,
        example_value=example_value,
    )


def _resolve_codec(codec: ExcelColumnCodec | None) -> tuple[type[ExcelFieldCodec] | None, dict[str, object]]:
    if codec is None:
        return None, {}
    if isinstance(codec, ExcelFieldCodecSpec):
        options = codec.as_column_options()
        unknown_options = sorted(set(options) - _CODEC_COLUMN_OPTION_NAMES)
        if unknown_options:
            unknown = ', '.join(unknown_options)
            raise ValueError(f'Unsupported codec column option(s): {unknown}')
        return codec.codec_type, options
    return codec, {}


def _merged_option[ValueT](name: str, column_value: ValueT | None, codec_options: dict[str, object]) -> ValueT | None:
    if name not in codec_options:
        return column_value

    codec_value = codec_options[name]
    if column_value is not None and column_value != codec_value:
        raise ValueError(f'Column option {name!r} was supplied both by ExcelColumn and by codec configuration.')
    return cast(ValueT, codec_value)


__all__ = ['ExcelColumn', 'ExcelColumnCodec', 'ExcelColumnSpec']
