from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from excelalchemy._primitives.identity import Key
from excelalchemy.codecs.base import CompositeExcelFieldCodec, log_codec_parse_fallback
from excelalchemy.codecs.number import Number, canonicalize_decimal, transform_decimal
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.i18n.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo


class NumberRange(CompositeExcelFieldCodec):
    start: float | int | None
    end: float | int | None

    __name__ = 'NumberRange'

    def __init__(self, start: Decimal | int | float | None, end: Decimal | int | float | None):
        # Keep dict-like behavior while preserving normalized start/end attributes.
        super().__init__(start=transform_decimal(start), end=transform_decimal(end))
        self.start = transform_decimal(start)
        self.end = transform_decimal(end)

    @classmethod
    def column_items(cls) -> list[tuple[Key, FieldMetaInfo]]:
        return [
            (Key('start'), FieldMetaInfo(label=dmsg(MessageKey.LABEL_MINIMUM_VALUE))),
            (Key('end'), FieldMetaInfo(label=dmsg(MessageKey.LABEL_MAXIMUM_VALUE))),
        ]

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        return Number.build_comment(field_meta)

    @classmethod
    def expected_input_message(cls, field_meta: FieldMetaInfo) -> str | None:
        return msg(MessageKey.ENTER_NUMBER_RANGE_EXPECTED_FORMAT)

    @classmethod
    def parse_input(cls, value: object, field_meta: FieldMetaInfo) -> object:
        declared = field_meta.declared
        if isinstance(value, str):
            value = value.strip()

        if isinstance(value, NumberRange):
            return value

        mapping = cls._coerce_mapping(value)
        if mapping is not None:
            try:
                start = cls._parse_decimal_boundary(mapping['start'])
                end = cls._parse_decimal_boundary(mapping['end'])
                return NumberRange(start, end)
            except (KeyError, TypeError, ValueError) as exc:
                log_codec_parse_fallback(cls.__name__, value, field_label=declared.label, exc=exc)
        return value

    @classmethod
    def format_display_value(cls, value: object | None, field_meta: FieldMetaInfo) -> str:
        if value is None or value == '':
            return ''
        try:
            presentation = field_meta.presentation
            parsed = cls._parse_decimal_boundary(value)
            if parsed is None:
                return ''
            return str(transform_decimal(canonicalize_decimal(parsed, presentation.fraction_digits)))
        except Exception:
            return str(value)

    @classmethod
    def normalize_import_value(cls, value: object, field_meta: FieldMetaInfo) -> 'NumberRange':
        parsed = cls.__maybe_number_range__(value, field_meta)
        errors: list[str] = []
        if parsed.start is not None and parsed.end is not None and parsed.start > parsed.end:
            errors.append(msg(MessageKey.NUMBER_RANGE_MIN_GREATER_THAN_MAX))

        if parsed.start is not None:
            errors.extend(Number.__check_range__(parsed.start, field_meta))
        if parsed.end is not None:
            errors.extend(Number.__check_range__(parsed.end, field_meta))

        if errors:
            raise ValueError(*errors)
        else:
            return parsed

    @staticmethod
    def __maybe_number_range__(value: object, field_meta: FieldMetaInfo) -> 'NumberRange':
        if isinstance(value, NumberRange):
            start = NumberRange._canonicalize_boundary(value.start, field_meta)
            end = NumberRange._canonicalize_boundary(value.end, field_meta)
            return NumberRange(start, end)

        mapping = NumberRange._coerce_mapping(value)
        if mapping is not None:
            try:
                start = NumberRange._canonicalize_boundary(mapping['start'], field_meta)
                end = NumberRange._canonicalize_boundary(mapping['end'], field_meta)
                return NumberRange(start, end)
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
        parsed = NumberRange._parse_decimal_boundary(value)
        if parsed is None:
            return None
        return canonicalize_decimal(parsed, presentation.fraction_digits)


NumberRangeCodec = NumberRange
