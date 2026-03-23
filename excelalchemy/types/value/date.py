import logging
from datetime import datetime
from typing import Any, cast

import pendulum
from pendulum import DateTime

from excelalchemy.const import DATE_FORMAT_TO_HINT_MAPPING, MILLISECOND_TO_SECOND, DataRangeOption
from excelalchemy.exc import ConfigError
from excelalchemy.types.abstract import ABCValueType
from excelalchemy.types.field import FieldMetaInfo


class Date(ABCValueType, datetime):
    __name__ = '日期选择'

    @classmethod
    def comment(cls, field_meta: FieldMetaInfo) -> str:
        if not field_meta.date_format:
            raise ConfigError('日期格式未定义')
        return '\n'.join(
            [
                field_meta.comment_required,
                field_meta.comment_date_format,
                field_meta.comment_date_range_option,
                field_meta.comment_hint,
            ]
        )

    @classmethod
    def serialize(cls, value: str | DateTime | Any, field_meta: FieldMetaInfo) -> datetime | Any:
        if isinstance(value, DateTime):
            logging.info('类型【%s】无需序列化: %s, 返回原值 %s ', cls.__name__, field_meta.label, value)
            return value

        if not field_meta.date_format:
            raise ConfigError('日期格式未定义')

        value = str(value).strip()
        try:
            # pyright: reportPrivateImportUsage=false
            # pyright: reportUnknownMemberType=false
            # pyright: reportGeneralTypeIssues=false
            v = value.replace('/', '-')  # pendulum 不支持 / 作为日期分隔符
            dt: DateTime = cast(DateTime, pendulum.parse(v))
            return dt.replace(tzinfo=field_meta.timezone)
        except Exception as exc:
            logging.warning('ValueType 类型 <%s> 无法解析 Excel 输入，返回原值：%s，原因：%s', cls.__name__, value, exc)
            return value

    @classmethod
    def deserialize(cls, value: str | datetime | None | Any, field_meta: FieldMetaInfo) -> str:
        match value:
            case None | '':
                return ''
            case datetime():
                return value.strftime(field_meta.python_date_format)
            case int() | float():
                return datetime.fromtimestamp(int(value) / MILLISECOND_TO_SECOND).strftime(
                    field_meta.python_date_format
                )
            case _:
                return str(value) if value is not None else ''

    @classmethod
    def __validate__(cls, value: Any, field_meta: FieldMetaInfo) -> int:
        if field_meta.date_format is None:
            raise ConfigError('日期格式未定义')

        if not isinstance(value, datetime):
            raise ValueError(f'请输入格式为{DATE_FORMAT_TO_HINT_MAPPING[field_meta.date_format]}的日期')

        parsed = cls._parse_date(value, field_meta)
        errors = cls._validate_date_range(parsed, field_meta)

        if errors:
            raise ValueError(*errors)
        else:
            return int(parsed.timestamp() * MILLISECOND_TO_SECOND)

    @staticmethod
    def _parse_date(v: datetime, field_meta: FieldMetaInfo) -> datetime:
        format_ = field_meta.python_date_format
        parsed = datetime.strptime(v.strftime(format_), format_)
        parsed = parsed.replace(tzinfo=field_meta.timezone)
        return parsed

    @staticmethod
    def _validate_date_range(parsed: datetime, field_meta: FieldMetaInfo) -> list[str]:
        now = datetime.now(tz=field_meta.timezone)
        errors: list[str] = []

        match field_meta.date_range_option:
            case DataRangeOption.PRE:
                if parsed > now:
                    errors.append('需早于当前时间（含当前时间）')
            case DataRangeOption.NEXT:
                if parsed < now:
                    errors.append('需晚于当前时间（含当前时间）')
            case DataRangeOption.NONE | None:
                ...

        return errors
