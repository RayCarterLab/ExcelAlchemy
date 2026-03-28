import logging
from datetime import datetime
from typing import Any

import pendulum
from pendulum import DateTime
from pydantic import BaseModel

from excelalchemy._internal.constants import DATE_FORMAT_TO_PYTHON_MAPPING, MILLISECOND_TO_SECOND, DataRangeOption
from excelalchemy._internal.identity import Key
from excelalchemy.codecs.base import CompositeExcelFieldCodec
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

    __name__ = '日期范围'

    @classmethod
    def model_validate(cls, obj: Any) -> 'DateRange':
        impl = _DateRangeImpl.model_validate(obj)
        self = cls(impl.start, impl.end)
        return self

    def __init__(self, start: datetime | None, end: datetime | None):
        # trick, BaseMode.dict() 会得到时间戳，而不是 datetime 对象，这是预期的行为
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
        if field_meta.date_format is None:
            raise RuntimeError(msg(MessageKey.DATE_FORMAT_NOT_CONFIGURED))

        return '\n'.join(
            [
                field_meta.comment_required,
                field_meta.comment_date_format,
                dmsg(MessageKey.COMMENT_DATE_RANGE_START_NOT_AFTER_END, extra_hint=field_meta.hint or ''),
            ]
        )

    @classmethod
    def parse_input(cls, value: dict[str, str] | Any, field_meta: FieldMetaInfo) -> dict[str, DateTime | None] | Any:
        match value:
            case dict():
                try:
                    start_str, end_str = value.get('start'), value.get('end')
                    start_time = (
                        pendulum.parse(start_str).replace(  # type: ignore
                            tzinfo=field_meta.timezone,
                        )
                        if start_str
                        else None
                    )
                    end_time = (
                        pendulum.parse(end_str).replace(  # type: ignore
                            tzinfo=field_meta.timezone,
                        )
                        if end_str
                        else None
                    )

                    return {'start': start_time, 'end': end_time}
                except Exception as e:
                    logging.warning('Could not parse value %s for field %s. Reason: %s', value, cls.__name__, e)
                    return value
            case datetime():
                return value
            case str():
                try:
                    datetime_value = pendulum.parse(value).replace(tzinfo=field_meta.timezone)  # type: ignore
                except Exception as e:
                    logging.warning('Could not parse value %s for field %s. Reason: %s', value, cls.__name__, e)
                    return value
                return datetime_value
            case _:
                return value

    @classmethod
    def normalize_import_value(
        cls,
        value: dict[str, DateTime | None] | Any,
        field_meta: FieldMetaInfo,
    ) -> 'DateRange':
        try:
            parsed = DateRange.model_validate(value)
            parsed.start = parsed.start.replace(tzinfo=field_meta.timezone) if parsed.start else parsed.start
            parsed.end = parsed.end.replace(tzinfo=field_meta.timezone) if parsed.end else parsed.end
        except Exception as exc:
            raise ValueError(msg(MessageKey.INVALID_INPUT)) from exc

        errors: list[str] = []
        now = datetime.now(tz=field_meta.timezone)

        if parsed.start and parsed.end and parsed.start > parsed.end:
            errors.append(msg(MessageKey.DATE_RANGE_START_AFTER_END))

        match field_meta.date_range_option:
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
    def format_display_value(cls, value: dict[str, str] | str | Any | None, field_meta: FieldMetaInfo) -> str:
        if value is None or value == '':
            return ''
        date_format = field_meta.must_date_format
        py_date_format = DATE_FORMAT_TO_PYTHON_MAPPING[date_format]

        if isinstance(value, str):
            return value

        if isinstance(value, datetime):
            return value.strftime(py_date_format)

        if isinstance(value, dict):
            return cls.__deserialize__dict(py_date_format, value)

        logging.warning('%s could not be deserialized; returning the original value', cls.__name__)
        return value if value is not None else ''

    @classmethod
    def __deserialize__dict(cls, py_date_format: str, value: dict[str, Any]) -> str:
        start, end = value['start'], value['end']
        if isinstance(start, datetime):
            start = start.strftime(py_date_format)
        elif isinstance(start, (int, float)):
            start = datetime.fromtimestamp(start / MILLISECOND_TO_SECOND).strftime(py_date_format)

        if isinstance(end, datetime):
            end = end.strftime(py_date_format)
        elif isinstance(end, (int, float)):
            end = datetime.fromtimestamp(end / MILLISECOND_TO_SECOND).strftime(py_date_format)
        return start + ' - ' + end


DateRangeCodec = DateRange
