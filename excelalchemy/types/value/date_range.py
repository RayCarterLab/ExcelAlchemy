import logging
from datetime import datetime
from typing import Any

import pendulum

# pyright: reportPrivateImportUsage=false
from pendulum import DateTime
from pydantic import BaseModel

from excelalchemy.const import DATE_FORMAT_TO_PYTHON_MAPPING, MILLISECOND_TO_SECOND, DataRangeOption
from excelalchemy.types.abstract import ComplexABCValueType
from excelalchemy.types.field import FieldMetaInfo
from excelalchemy.types.identity import Key


class _DateRangeImpl(BaseModel):
    start: datetime | None
    end: datetime | None


class DateRange(ComplexABCValueType):
    start: datetime | None
    end: datetime | None

    __name__ = '日期范围'

    @classmethod
    def parse_obj(cls, obj: Any) -> 'DateRange':
        impl = _DateRangeImpl.parse_obj(obj)
        self = cls(impl.start, impl.end)
        return self

    def __init__(self, start: datetime | None, end: datetime | None):
        # pyright: reportUnknownMemberType=false
        # trick, BaseMode.dict() 会得到时间戳，而不是 datetime 对象，这是预期的行为
        _start = int(start.timestamp() * MILLISECOND_TO_SECOND) if start else None
        _end = int(end.timestamp() * MILLISECOND_TO_SECOND) if end else None
        super().__init__(start=_start, end=_end)
        self.start = start
        self.end = end

    @classmethod
    def model_items(cls) -> list[tuple[Key, FieldMetaInfo]]:
        return [
            (Key('start'), FieldMetaInfo(label='开始日期')),
            (Key('end'), FieldMetaInfo(label='结束日期')),
        ]

    @classmethod
    def comment(cls, field_meta: FieldMetaInfo) -> str:
        if field_meta.date_format is None:
            raise RuntimeError('日期格式未定义')

        return '\n'.join(
            [
                field_meta.comment_required,
                field_meta.comment_date_format,
                f'提示：开始日期不得晚于结束日期{field_meta.hint or ""}',
            ]
        )

    @classmethod
    def serialize(cls, value: dict[str, str] | Any, field_meta: FieldMetaInfo) -> dict[str, DateTime | None] | Any:
        match value:
            case dict():
                try:
                    start_str, end_str = value.get('start'), value.get('end')
                    # pyright: reportGeneralTypeIssues=false
                    # pyright: reportUnknownArgumentType=false
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
    def __validate__(
        cls,
        value: dict[str, DateTime | None] | Any,
        field_meta: FieldMetaInfo,
    ) -> 'DateRange':
        try:
            parsed = DateRange.parse_obj(value)
            parsed.start = parsed.start.replace(tzinfo=field_meta.timezone) if parsed.start else parsed.start
            parsed.end = parsed.end.replace(tzinfo=field_meta.timezone) if parsed.end else parsed.end
        except Exception as exc:
            raise ValueError('无法识别的输入') from exc

        errors: list[str] = []
        now = datetime.now(tz=field_meta.timezone)

        if parsed.start and parsed.end and parsed.start > parsed.end:
            errors.append('开始日期不得晚于结束日期')

        match field_meta.date_range_option:
            case DataRangeOption.PRE:
                if (parsed.start and parsed.start > now) or (parsed.end and parsed.end > now):
                    errors.append('需早于当前时间（含当前时间）')
            case DataRangeOption.NEXT:
                if (parsed.start and parsed.start < now) or (parsed.end and parsed.end < now):
                    errors.append('需晚于当前时间（含当前时间）')
            case DataRangeOption.NONE | None:
                ...  # do nothing

        if errors:
            raise ValueError(*errors)
        else:
            return parsed

    @classmethod
    def deserialize(cls, value: dict[str, str] | str | Any | None, field_meta: FieldMetaInfo) -> str:
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

        logging.warning('%s 反序列化失败，返回原值', cls.__name__)
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
