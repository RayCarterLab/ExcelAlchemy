from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from excelalchemy.codecs.field_codec import CompositeExcelFieldCodec, ExcelFieldCodecSpec, log_codec_parse_fallback
from excelalchemy.codecs.number import NumberFieldCodec, canonicalize_decimal, transform_decimal
from excelalchemy.field_metadata import FieldMetaInfo
from excelalchemy.messages import MessageKey
from excelalchemy.messages import display_message as dmsg
from excelalchemy.messages import message as msg
from excelalchemy.primitives.identity import Key


class NumberRangeValue:
    start: float | int | None
    end: float | int | None

    def __init__(self, start: Decimal | int | float | None, end: Decimal | int | float | None):
        self.start = transform_decimal(start)
        self.end = transform_decimal(end)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, NumberRangeValue):
            return self.to_dict() == other.to_dict()
        if isinstance(other, Mapping):
            return self.to_dict() == dict(cast(Mapping[str, object], other))
        return False

    def to_dict(self) -> dict[str, float | int | None]:
        return {'start': self.start, 'end': self.end}


class NumberRangeFieldCodec(CompositeExcelFieldCodec):
    @classmethod
    def column_items(cls) -> list[tuple[Key, FieldMetaInfo]]:
        return [
            (Key('start'), FieldMetaInfo(label=dmsg(MessageKey.LABEL_MINIMUM_VALUE))),
            (Key('end'), FieldMetaInfo(label=dmsg(MessageKey.LABEL_MAXIMUM_VALUE))),
        ]

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        return NumberFieldCodec.build_comment(field_meta)

    @classmethod
    def expected_input_message(cls, field_meta: FieldMetaInfo) -> str | None:
        return msg(MessageKey.ENTER_NUMBER_RANGE_EXPECTED_FORMAT)

    @classmethod
    def parse_input(cls, value: object, field_meta: FieldMetaInfo) -> object:
        declared = field_meta.declared
        if isinstance(value, str):
            value = value.strip()

        if isinstance(value, NumberRangeValue):
            return value.to_dict()

        mapping = cls._coerce_mapping(value)
        if mapping is not None:
            try:
                start = cls._parse_decimal_boundary(mapping['start'])
                end = cls._parse_decimal_boundary(mapping['end'])
                return NumberRangeValue(start, end)
            except (KeyError, TypeError, ValueError) as exc:
                log_codec_parse_fallback(cls.__name__, value, field_label=declared.label, exc=exc)
        return value

    @classmethod
    def format_display_value(cls, value: object | None, field_meta: FieldMetaInfo) -> str:
        if value is None or value == '':
            return ''
        if isinstance(value, NumberRangeValue):
            value = value.to_dict()
        try:
            presentation = field_meta.presentation
            parsed = cls._parse_decimal_boundary(value)
            if parsed is None:
                return ''
            return str(transform_decimal(canonicalize_decimal(parsed, presentation.fraction_digits)))
        except Exception:
            return str(value)

    @classmethod
    def normalize_import_value(cls, value: object, field_meta: FieldMetaInfo) -> dict[str, float | int | None]:
        parsed = cls.__maybe_number_range__(value, field_meta)
        errors: list[str] = []
        if parsed.start is not None and parsed.end is not None and parsed.start > parsed.end:
            errors.append(msg(MessageKey.NUMBER_RANGE_MIN_GREATER_THAN_MAX))

        if parsed.start is not None:
            errors.extend(NumberFieldCodec.__check_range__(parsed.start, field_meta))
        if parsed.end is not None:
            errors.extend(NumberFieldCodec.__check_range__(parsed.end, field_meta))

        if errors:
            raise ValueError(*errors)
        else:
            return parsed.to_dict()

    @staticmethod
    def __maybe_number_range__(value: object, field_meta: FieldMetaInfo) -> NumberRangeValue:
        if isinstance(value, NumberRangeValue):
            start = NumberRangeFieldCodec._canonicalize_boundary(value.start, field_meta)
            end = NumberRangeFieldCodec._canonicalize_boundary(value.end, field_meta)
            return NumberRangeValue(start, end)

        mapping = NumberRangeFieldCodec._coerce_mapping(value)
        if mapping is not None:
            try:
                start = NumberRangeFieldCodec._canonicalize_boundary(mapping['start'], field_meta)
                end = NumberRangeFieldCodec._canonicalize_boundary(mapping['end'], field_meta)
                return NumberRangeValue(start, end)
            except Exception as exc:
                raise ValueError(msg(MessageKey.ENTER_NUMBER)) from exc

        raise ValueError(msg(MessageKey.ENTER_NUMBER_EXPECTED_FORMAT))

    @staticmethod
    def _coerce_mapping(value: object) -> Mapping[str, object] | None:
        if not isinstance(value, Mapping):
            return None

        raw_mapping = cast(Mapping[object, object], value)
        mapping: dict[str, object] = {}
        for key, item in raw_mapping.items():
            if not isinstance(key, str):
                return None
            mapping[key] = item
        return mapping

    @staticmethod
    def _parse_decimal_boundary(value: object) -> Decimal | None:
        if value is None or value == '':
            return None
        return Decimal(str(value))

    @staticmethod
    def _canonicalize_boundary(value: object, field_meta: FieldMetaInfo) -> Decimal | None:
        presentation = field_meta.presentation
        parsed = NumberRangeFieldCodec._parse_decimal_boundary(value)
        if parsed is None:
            return None
        return canonicalize_decimal(parsed, presentation.fraction_digits)


class NumberRangeCodec:
    """Factory for explicit number-range codec configuration."""

    def __new__(
        cls,
        *,
        fraction_digits: int | None = None,
        unit: str | None = None,
    ) -> ExcelFieldCodecSpec:
        return ExcelFieldCodecSpec.create(NumberRangeFieldCodec, fraction_digits=fraction_digits, unit=unit)
