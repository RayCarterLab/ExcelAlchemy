from collections.abc import Mapping
from datetime import datetime
from datetime import timezone as DateTimeZone
from typing import cast

import pendulum
from pendulum import DateTime
from pydantic import BaseModel

from excelalchemy.codecs.date import parse_excel_datetime_text
from excelalchemy.codecs.field_codec import (
    CompositeExcelFieldCodec,
    ExcelFieldCodecSpec,
    log_codec_parse_fallback,
    log_codec_render_fallback,
)
from excelalchemy.errors import ConfigError
from excelalchemy.field_metadata import FieldMetaInfo
from excelalchemy.messages import MessageKey
from excelalchemy.messages import display_message as dmsg
from excelalchemy.messages import message as msg
from excelalchemy.messages import user_message as umsg
from excelalchemy.primitives.constants import (
    DATE_FORMAT_TO_PYTHON_MAPPING,
    MILLISECOND_TO_SECOND,
    DataRangeOption,
    DateFormat,
)
from excelalchemy.primitives.identity import Key


class _DateRangeImpl(BaseModel):
    start: datetime | None
    end: datetime | None


class DateRangeValue:
    start: datetime | None
    end: datetime | None

    @classmethod
    def model_validate(cls, obj: object) -> 'DateRangeValue':
        impl = _DateRangeImpl.model_validate(obj)
        self = cls(impl.start, impl.end)
        return self

    def __init__(self, start: datetime | None, end: datetime | None):
        self.start = start
        self.end = end

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DateRangeValue):
            return self.to_dict() == other.to_dict()
        if isinstance(other, Mapping):
            return self.to_dict() == dict(cast(Mapping[str, object], other))
        return False

    def to_dict(self) -> dict[str, int | None]:
        return {
            'start': int(self.start.timestamp() * MILLISECOND_TO_SECOND) if self.start else None,
            'end': int(self.end.timestamp() * MILLISECOND_TO_SECOND) if self.end else None,
        }


class DateRangeFieldCodec(CompositeExcelFieldCodec):
    @classmethod
    def column_items(cls) -> list[tuple[Key, FieldMetaInfo]]:
        return [
            (Key('start'), FieldMetaInfo(label=dmsg(MessageKey.LABEL_START_DATE))),
            (Key('end'), FieldMetaInfo(label=dmsg(MessageKey.LABEL_END_DATE))),
        ]

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        if presentation.date_format is None:
            raise ConfigError(
                msg(MessageKey.DATE_FORMAT_NOT_CONFIGURED), message_key=MessageKey.DATE_FORMAT_NOT_CONFIGURED
            )

        return '\n'.join(
            [
                declared.comment_required,
                presentation.comment_date_format,
                dmsg(MessageKey.COMMENT_DATE_RANGE_START_NOT_AFTER_END, extra_hint=presentation.hint or ''),
                *([presentation.comment_example] if presentation.comment_example else []),
            ]
        )

    @classmethod
    def expected_input_message(cls, field_meta: FieldMetaInfo) -> str | None:
        return umsg(MessageKey.ENTER_DATE_RANGE_EXPECTED_FORMAT)

    @classmethod
    def parse_input(cls, value: object, field_meta: FieldMetaInfo) -> object:
        declared = field_meta.declared
        mapping = cls._coerce_mapping(value)
        if mapping is not None:
            try:
                return {
                    'start': cls._parse_optional_datetime(mapping.get('start'), field_meta),
                    'end': cls._parse_optional_datetime(mapping.get('end'), field_meta),
                }
            except Exception as exc:
                log_codec_parse_fallback(cls.__name__, value, field_label=declared.label, exc=exc)
                return value

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            try:
                return cls._parse_datetime_text(value, field_meta)
            except Exception as exc:
                log_codec_parse_fallback(cls.__name__, value, field_label=declared.label, exc=exc)
                return value

        return value

    @classmethod
    def normalize_import_value(
        cls,
        value: object,
        field_meta: FieldMetaInfo,
    ) -> dict[str, int | None]:
        presentation = field_meta.presentation
        try:
            parsed = value if isinstance(value, DateRangeValue) else DateRangeValue.model_validate(value)
            parsed.start = pendulum.instance(parsed.start, tz=presentation.timezone) if parsed.start else None
            parsed.end = pendulum.instance(parsed.end, tz=presentation.timezone) if parsed.end else None
        except Exception as exc:
            raise ValueError(umsg(MessageKey.INVALID_INPUT)) from exc

        errors: list[str] = []
        now = datetime.now(tz=presentation.timezone)

        if parsed.start and parsed.end and parsed.start > parsed.end:
            errors.append(umsg(MessageKey.DATE_RANGE_START_AFTER_END))

        match presentation.date_range_option:
            case DataRangeOption.PRE:
                if (parsed.start and parsed.start > now) or (parsed.end and parsed.end > now):
                    errors.append(umsg(MessageKey.DATE_MUST_BE_EARLIER_THAN_NOW))
            case DataRangeOption.NEXT:
                if (parsed.start and parsed.start < now) or (parsed.end and parsed.end < now):
                    errors.append(umsg(MessageKey.DATE_MUST_BE_LATER_THAN_NOW))
            case DataRangeOption.NONE | None:
                ...  # do nothing

        if errors:
            raise ValueError(*errors)
        else:
            return parsed.to_dict()

    @classmethod
    def format_display_value(cls, value: object | None, field_meta: FieldMetaInfo) -> str:
        if value is None or value == '':
            return ''
        presentation = field_meta.presentation
        date_format = presentation.must_date_format
        py_date_format = DATE_FORMAT_TO_PYTHON_MAPPING[date_format]

        if isinstance(value, str):
            return value

        if isinstance(value, datetime):
            return value.strftime(py_date_format)

        mapping = cls._coerce_mapping(value)
        if mapping is not None:
            return cls.__deserialize__dict(py_date_format, mapping)

        log_codec_render_fallback(
            cls.__name__,
            value,
            field_label=field_meta.declared.label,
            reason='The workbook value is not a string, datetime, or start/end mapping',
        )
        return str(value)

    @classmethod
    def __deserialize__dict(cls, py_date_format: str, value: Mapping[str, object]) -> str:
        start = cls._format_boundary(value['start'], py_date_format)
        end = cls._format_boundary(value['end'], py_date_format)
        return start + ' - ' + end

    @staticmethod
    def _format_boundary(value: object, py_date_format: str) -> str:
        start = value
        if isinstance(start, datetime):
            start = start.strftime(py_date_format)
        elif isinstance(start, (int, float)):
            start = datetime.fromtimestamp(start / MILLISECOND_TO_SECOND).strftime(py_date_format)
        return str(start)

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
    def _parse_optional_datetime(value: object, field_meta: FieldMetaInfo) -> DateTime | None:
        if value is None or value == '':
            return None
        if not isinstance(value, str):
            raise TypeError(f'Expected a string date value, got {type(value)}')
        return DateRangeFieldCodec._parse_datetime_text(value, field_meta)

    @staticmethod
    def _parse_datetime_text(value: str, field_meta: FieldMetaInfo) -> DateTime:
        return parse_excel_datetime_text(value, field_meta)


class DateRangeCodec:
    """Factory for explicit date-range codec configuration."""

    @staticmethod
    def day(
        *,
        timezone: DateTimeZone | None = None,
        date_range_option: DataRangeOption | None = None,
    ) -> ExcelFieldCodecSpec:
        return DateRangeCodec.format(DateFormat.DAY, timezone=timezone, date_range_option=date_range_option)

    @staticmethod
    def month(
        *,
        timezone: DateTimeZone | None = None,
        date_range_option: DataRangeOption | None = None,
    ) -> ExcelFieldCodecSpec:
        return DateRangeCodec.format(DateFormat.MONTH, timezone=timezone, date_range_option=date_range_option)

    @staticmethod
    def year(
        *,
        timezone: DateTimeZone | None = None,
        date_range_option: DataRangeOption | None = None,
    ) -> ExcelFieldCodecSpec:
        return DateRangeCodec.format(DateFormat.YEAR, timezone=timezone, date_range_option=date_range_option)

    @staticmethod
    def minute(
        *,
        timezone: DateTimeZone | None = None,
        date_range_option: DataRangeOption | None = None,
    ) -> ExcelFieldCodecSpec:
        return DateRangeCodec.format(DateFormat.MINUTE, timezone=timezone, date_range_option=date_range_option)

    @staticmethod
    def format(
        date_format: DateFormat,
        *,
        timezone: DateTimeZone | None = None,
        date_range_option: DataRangeOption | None = None,
    ) -> ExcelFieldCodecSpec:
        return ExcelFieldCodecSpec.create(
            DateRangeFieldCodec,
            date_format=date_format,
            timezone=timezone,
            date_range_option=date_range_option,
        )
