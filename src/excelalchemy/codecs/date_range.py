import logging
from collections.abc import Mapping
from datetime import datetime
from typing import cast

import pendulum
from pendulum import DateTime
from pydantic import BaseModel

from excelalchemy._primitives.constants import DATE_FORMAT_TO_PYTHON_MAPPING, MILLISECOND_TO_SECOND, DataRangeOption
from excelalchemy._primitives.identity import Key
from excelalchemy.codecs.base import CompositeExcelFieldCodec
from excelalchemy.exceptions import ConfigError
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.i18n.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo


class _DateRangeImpl(BaseModel):
    start: datetime | None
    end: datetime | None


class DateRange(CompositeExcelFieldCodec):
    start: datetime | None
    end: datetime | None

    __name__ = 'DateRange'

    @classmethod
    def model_validate(cls, obj: object) -> 'DateRange':
        impl = _DateRangeImpl.model_validate(obj)
        self = cls(impl.start, impl.end)
        return self

    def __init__(self, start: datetime | None, end: datetime | None):
        # Pydantic model dumps intentionally store timestamps rather than datetime objects here.
        _start = int(start.timestamp() * MILLISECOND_TO_SECOND) if start else None
        _end = int(end.timestamp() * MILLISECOND_TO_SECOND) if end else None
        super().__init__(start=_start, end=_end)
        self.start = start
        self.end = end

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
            ]
        )

    @classmethod
    def parse_input(cls, value: object, field_meta: FieldMetaInfo) -> object:
        mapping = cls._coerce_mapping(value)
        if mapping is not None:
            try:
                return {
                    'start': cls._parse_optional_datetime(mapping.get('start'), field_meta),
                    'end': cls._parse_optional_datetime(mapping.get('end'), field_meta),
                }
            except Exception as exc:
                logging.warning('Could not parse value %s for field %s. Reason: %s', value, cls.__name__, exc)
                return value

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            try:
                return cls._parse_datetime_text(value, field_meta)
            except Exception as exc:
                logging.warning('Could not parse value %s for field %s. Reason: %s', value, cls.__name__, exc)
                return value

        return value

    @classmethod
    def normalize_import_value(
        cls,
        value: object,
        field_meta: FieldMetaInfo,
    ) -> 'DateRange':
        presentation = field_meta.presentation
        try:
            parsed = DateRange.model_validate(value)
            parsed.start = pendulum.instance(parsed.start, tz=presentation.timezone) if parsed.start else None
            parsed.end = pendulum.instance(parsed.end, tz=presentation.timezone) if parsed.end else None
        except Exception as exc:
            raise ValueError(msg(MessageKey.INVALID_INPUT)) from exc

        errors: list[str] = []
        now = datetime.now(tz=presentation.timezone)

        if parsed.start and parsed.end and parsed.start > parsed.end:
            errors.append(msg(MessageKey.DATE_RANGE_START_AFTER_END))

        match presentation.date_range_option:
            case DataRangeOption.PRE:
                if (parsed.start and parsed.start > now) or (parsed.end and parsed.end > now):
                    errors.append(msg(MessageKey.DATE_MUST_BE_EARLIER_THAN_NOW))
            case DataRangeOption.NEXT:
                if (parsed.start and parsed.start < now) or (parsed.end and parsed.end < now):
                    errors.append(msg(MessageKey.DATE_MUST_BE_LATER_THAN_NOW))
            case DataRangeOption.NONE | None:
                ...  # do nothing

        if errors:
            raise ValueError(*errors)
        else:
            return parsed

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

        logging.warning('%s could not be deserialized; returning the original value', cls.__name__)
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
        return DateRange._parse_datetime_text(value, field_meta)

    @staticmethod
    def _parse_datetime_text(value: str, field_meta: FieldMetaInfo) -> DateTime:
        presentation = field_meta.presentation
        parsed = pendulum.parse(value)
        if isinstance(parsed, DateTime):
            return parsed.replace(tzinfo=presentation.timezone)
        if isinstance(parsed, datetime):
            return pendulum.instance(parsed).replace(tzinfo=presentation.timezone)
        raise ValueError(msg(MessageKey.INVALID_INPUT))


DateRangeCodec = DateRange
