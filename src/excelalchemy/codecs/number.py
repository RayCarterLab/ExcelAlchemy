from decimal import ROUND_DOWN, Context, Decimal, InvalidOperation

from excelalchemy.codecs.base import (
    ExcelFieldCodec,
    NormalizedImportValue,
    WorkbookDisplayValue,
    WorkbookInputValue,
    codec_logger,
    log_codec_parse_fallback,
)
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.i18n.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo


def canonicalize_decimal(value: Decimal, digits_limit: int | None) -> Decimal:
    """Quantize a Decimal to the configured precision when needed."""
    exponent = value.as_tuple().exponent
    if digits_limit is not None and isinstance(exponent, int) and abs(exponent) != digits_limit:
        try:
            value = Decimal(value).quantize(
                Decimal(f'0.{"0" * digits_limit}'),
                context=Context(rounding=ROUND_DOWN),
            )
        except InvalidOperation as e:
            codec_logger.warning('Codec Number detected precision loss while quantizing fraction_digits: %s', e)
    return value


def transform_decimal(value: Decimal | int | float | None) -> float | int | None:
    """Convert a Decimal into an int or float for workbook-facing output."""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return value

    if value.as_tuple().exponent == 0:
        return int(value)
    else:
        return float(value)


class Number(Decimal, ExcelFieldCodec):
    __name__ = 'Number'

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        declared = field_meta.declared
        presentation = field_meta.presentation
        return '\n'.join(
            [
                declared.comment_required,
                dmsg(MessageKey.COMMENT_NUMBER_FORMAT),
                presentation.comment_fraction_digits,
                dmsg(MessageKey.COMMENT_NUMBER_INPUT_RANGE, value=cls.__get_range_description__(field_meta)),
                presentation.comment_unit,
            ]
        )

    @classmethod
    def parse_input(
        cls,
        value: str | int | float | WorkbookInputValue | None,
        field_meta: FieldMetaInfo,
    ) -> Decimal | WorkbookInputValue:
        declared = field_meta.declared
        if isinstance(value, str):
            value = value.strip()
        if value is None:
            return ''
        try:
            return transform_decimal(Decimal(str(value)))
        except Exception as exc:
            log_codec_parse_fallback(cls.__name__, value, field_label=declared.label, exc=exc)
            return str(value)

    @classmethod
    def format_display_value(
        cls,
        value: str | WorkbookDisplayValue | None,
        field_meta: FieldMetaInfo,
    ) -> str:
        if value is None or value == '':
            return ''

        try:
            return str(transform_decimal(Decimal(value)))
        except Exception:
            return str(value)

    @classmethod
    def __get_range_description__(cls, field_meta: FieldMetaInfo) -> str:
        constraints = field_meta.constraints
        upper_bound = constraints.le
        lower_bound = constraints.ge

        if upper_bound is None and lower_bound is None:
            return dmsg(MessageKey.DATE_RANGE_OPTION_NONE_DISPLAY)
        if lower_bound is None:
            return f'≤ {upper_bound}'
        if upper_bound is None:
            return f'≥ {lower_bound}'
        return f'{lower_bound}～{upper_bound}'

    @staticmethod
    def __maybe_decimal__(value: WorkbookInputValue) -> Decimal | None:
        # Convert non-Decimal input through Decimal for validation.
        if isinstance(value, Decimal):
            return value

        try:
            parsed = Decimal(str(value))
        except Exception as exc:
            raise ValueError(msg(MessageKey.INVALID_NUMBER_ENTER_NUMBER)) from exc

        return parsed

    @staticmethod
    def __check_range__(value: Decimal | float | int, field_meta: FieldMetaInfo) -> list[str]:
        errors: list[str] = []
        constraints = field_meta.constraints

        # Read the configured importer bounds from field metadata.
        importer_le = constraints.le or Decimal('Infinity')
        importer_ge = constraints.ge or Decimal('-Infinity')

        # Ensure the parsed decimal stays within the accepted range.
        if not importer_ge <= value <= importer_le:
            if constraints.le and constraints.ge:
                errors.append(
                    msg(
                        MessageKey.NUMBER_BETWEEN_MIN_AND_MAX,
                        minimum=constraints.ge,
                        maximum=constraints.le,
                    )
                )
            elif constraints.le:
                errors.append(msg(MessageKey.NUMBER_BETWEEN_NEG_INF_AND_MAX, maximum=constraints.le))
            elif constraints.ge:
                errors.append(msg(MessageKey.NUMBER_BETWEEN_MIN_AND_POS_INF, minimum=constraints.ge))

        return errors

    @classmethod
    def normalize_import_value(
        cls,
        value: Decimal | WorkbookInputValue,
        field_meta: FieldMetaInfo,
    ) -> NormalizedImportValue:
        # Convert non-Decimal input before range validation.
        presentation = field_meta.presentation
        parsed = cls.__maybe_decimal__(value)
        if parsed is None:
            raise ValueError(msg(MessageKey.INVALID_NUMBER_ENTER_NUMBER))
        errors: list[str] = cls.__check_range__(parsed, field_meta)
        if errors:
            raise ValueError(*errors)
        parsed = canonicalize_decimal(parsed, presentation.fraction_digits)
        value = transform_decimal(parsed)
        if value is None:
            raise ValueError(msg(MessageKey.INVALID_NUMBER_ENTER_NUMBER))
        return value


NumberCodec = Number
