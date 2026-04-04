from datetime import datetime
from typing import cast

import pendulum
from pendulum import DateTime

from excelalchemy._primitives.constants import DATE_FORMAT_TO_HINT_MAPPING, MILLISECOND_TO_SECOND, DataRangeOption
from excelalchemy.codecs.base import (
    ExcelFieldCodec,
    NormalizedImportValue,
    WorkbookDisplayValue,
    WorkbookInputValue,
    codec_logger,
    log_codec_parse_fallback,
)
from excelalchemy.exceptions import ConfigError
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo


class Date(ExcelFieldCodec, datetime):
    __name__ = 'Date'

    @classmethod
    def expected_input_message(cls, field_meta: FieldMetaInfo) -> str | None:
        presentation = field_meta.presentation
        if presentation.date_format is None:
            return None
        return msg(MessageKey.ENTER_DATE_FORMAT, date_format=DATE_FORMAT_TO_HINT_MAPPING[presentation.date_format])

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        if not presentation.date_format:
            raise ConfigError(msg(MessageKey.DATE_FORMAT_NOT_CONFIGURED))
        return '\n'.join(
            [
                declared.comment_required,
                presentation.comment_date_format,
                presentation.comment_date_range_option,
                presentation.comment_hint,
            ]
        )

    @classmethod
    def parse_input(
        cls,
        value: str | DateTime | WorkbookInputValue,
        field_meta: FieldMetaInfo,
    ) -> datetime | WorkbookInputValue:
        declared = field_meta.declared
        presentation = field_meta.presentation
        if isinstance(value, DateTime):
            codec_logger.info(
                'Codec %s received a parsed datetime for %s; returning it unchanged: %s',
                cls.__name__,
                declared.label,
                value,
            )
            return value

        if not presentation.date_format:
            raise ConfigError(msg(MessageKey.DATE_FORMAT_NOT_CONFIGURED))

        value = str(value).strip()
        try:
            v = value.replace('/', '-')  # pendulum does not accept "/" as a date separator here.
            dt: DateTime = cast(DateTime, pendulum.parse(v))
            return dt.replace(tzinfo=presentation.timezone)
        except Exception as exc:
            log_codec_parse_fallback(cls.__name__, value, field_label=declared.label, exc=exc)
            return value

    @classmethod
    def format_display_value(
        cls,
        value: str | datetime | WorkbookDisplayValue | None,
        field_meta: FieldMetaInfo,
    ) -> str:
        presentation = field_meta.presentation
        match value:
            case None | '':
                return ''
            case datetime():
                return value.strftime(presentation.python_date_format)
            case int() | float():
                return datetime.fromtimestamp(int(value) / MILLISECOND_TO_SECOND).strftime(
                    presentation.python_date_format
                )
            case _:
                return str(value) if value is not None else ''

    @classmethod
    def normalize_import_value(cls, value: WorkbookInputValue, field_meta: FieldMetaInfo) -> NormalizedImportValue:
        presentation = field_meta.presentation
        if presentation.date_format is None:
            raise ConfigError(msg(MessageKey.DATE_FORMAT_NOT_CONFIGURED))

        if not isinstance(value, datetime):
            raise ValueError(
                msg(MessageKey.ENTER_DATE_FORMAT, date_format=DATE_FORMAT_TO_HINT_MAPPING[presentation.date_format])
            )

        parsed = cls._parse_date(value, field_meta)
        errors = cls._validate_date_range(parsed, field_meta)

        if errors:
            raise ValueError(*errors)
        else:
            return int(parsed.timestamp() * MILLISECOND_TO_SECOND)

    @staticmethod
    def _parse_date(v: datetime, field_meta: FieldMetaInfo) -> datetime:
        presentation = field_meta.presentation
        format_ = presentation.python_date_format
        parsed = datetime.strptime(v.strftime(format_), format_)
        parsed = parsed.replace(tzinfo=presentation.timezone)
        return parsed

    @staticmethod
    def _validate_date_range(parsed: datetime, field_meta: FieldMetaInfo) -> list[str]:
        presentation = field_meta.presentation
        now = datetime.now(tz=presentation.timezone)
        errors: list[str] = []

        match presentation.date_range_option:
            case DataRangeOption.PRE:
                if parsed > now:
                    errors.append(msg(MessageKey.DATE_MUST_BE_EARLIER_THAN_NOW))
            case DataRangeOption.NEXT:
                if parsed < now:
                    errors.append(msg(MessageKey.DATE_MUST_BE_LATER_THAN_NOW))
            case DataRangeOption.NONE | None:
                ...

        return errors


DateCodec = Date
