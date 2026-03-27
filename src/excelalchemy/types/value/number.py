import logging
from decimal import ROUND_DOWN, Context, Decimal, InvalidOperation
from typing import Any

from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.i18n.messages import message as msg
from excelalchemy.types.abstract import ABCValueType
from excelalchemy.types.field import FieldMetaInfo


def canonicalize_decimal(value: Decimal, digits_limit: int | None) -> Decimal:
    """将 Decimal 转换为指定精度的 Decimal"""
    if digits_limit is not None and abs(value.as_tuple().exponent) != digits_limit:  # type: ignore[arg-type]
        try:
            value = Decimal(value).quantize(
                Decimal(f'0.{"0" * digits_limit}'),
                context=Context(rounding=ROUND_DOWN),
            )
        except InvalidOperation as e:
            logging.warning('fraction_digits is too small and causes precision loss: %s', e)
    return value


def transform_decimal(value: Decimal | int | float | None) -> float | int | None:
    """将 Decimal 转换为 float 或 int"""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return value

    if not isinstance(value, Decimal):
        raise TypeError(f'Expected Decimal, got {type(value)}')

    if value.as_tuple().exponent == 0:
        return int(value)
    else:
        return float(value)


class Number(Decimal, ABCValueType):
    __name__ = '数值输入'

    @classmethod
    def comment(cls, field_meta: FieldMetaInfo) -> str:
        return '\n'.join(
            [
                field_meta.comment_required,
                dmsg(MessageKey.COMMENT_NUMBER_FORMAT),
                field_meta.comment_fraction_digits,
                dmsg(MessageKey.COMMENT_NUMBER_INPUT_RANGE, value=cls.__get_range_description__(field_meta)),
                field_meta.comment_unit,
            ]
        )

    @classmethod
    def serialize(cls, value: str | int | float | None, field_meta: FieldMetaInfo) -> Decimal | Any:
        if isinstance(value, str):
            value = value.strip()
        try:
            return transform_decimal(Decimal(value))  # type: ignore[arg-type]
        except Exception as exc:
            logging.warning('ValueType <%s> could not parse Excel input %s; returning the original value. Reason: %s', cls.__name__, value, exc)
            return str(value) if value is not None else ''

    @classmethod
    def deserialize(cls, value: str | None | Any, field_meta: FieldMetaInfo) -> str:
        if value is None or value == '':
            return ''

        try:
            return str(transform_decimal(Decimal(value)))
        except Exception as exc:
            logging.warning('ValueType <%s> could not parse Excel input %s; returning the original value. Reason: %s', cls.__name__, value, exc)
            return str(value)

    @classmethod
    def __get_range_description__(cls, field_meta: FieldMetaInfo) -> str:  # type: ignore[return]
        match (field_meta.importer_le, field_meta.importer_ge):
            case (None, None):
                return dmsg(MessageKey.DATE_RANGE_OPTION_NONE_DISPLAY)
            case (_, None):
                return f'≤ {field_meta.importer_le}'
            case (None, _):
                return f'≥ {field_meta.importer_ge}'
            case (le, ge):
                return f'{ge}～{le}'

    @staticmethod
    def __maybe_decimal__(value: Any) -> Decimal | None:
        # 如果输入不是 Decimal 类型，尝试转换。
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

        # 从 field_meta 对象中获取导入者上限和下限值。
        importer_le = field_meta.importer_le or Decimal('Infinity')
        importer_ge = field_meta.importer_ge or Decimal('-Infinity')

        # 确保解析后的 decimal 在接受范围内。
        if not importer_ge <= value <= importer_le:
            if field_meta.importer_le and field_meta.importer_ge:
                errors.append(
                    msg(
                        MessageKey.NUMBER_BETWEEN_MIN_AND_MAX,
                        minimum=field_meta.importer_ge,
                        maximum=field_meta.importer_le,
                    )
                )
            elif field_meta.importer_le:
                errors.append(msg(MessageKey.NUMBER_BETWEEN_NEG_INF_AND_MAX, maximum=field_meta.importer_le))
            elif field_meta.importer_ge:
                errors.append(msg(MessageKey.NUMBER_BETWEEN_MIN_AND_POS_INF, minimum=field_meta.importer_ge))
            else:
                pass

        return errors

    @classmethod
    def __validate__(cls, value: Decimal | Any, field_meta: FieldMetaInfo) -> float | int:
        # 如果输入不是 Decimal 类型，尝试转换。
        parsed = cls.__maybe_decimal__(value)
        if parsed is None:
            raise ValueError(msg(MessageKey.INVALID_NUMBER_ENTER_NUMBER))
        # 初始化一个错误信息列表。
        errors: list[str] = cls.__check_range__(value, field_meta)
        if errors:
            raise ValueError(*errors)
        parsed = canonicalize_decimal(parsed, field_meta.fraction_digits)
        value = transform_decimal(parsed)
        if value is None:
            raise ValueError(msg(MessageKey.INVALID_NUMBER_ENTER_NUMBER))
        return value
