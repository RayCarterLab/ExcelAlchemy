import logging
from decimal import ROUND_DOWN, Context, Decimal, InvalidOperation
from typing import Any

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
            logging.warning('精度设置的过小，导致精度丢失，%s', e)
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
                '格式：数值',
                field_meta.comment_fraction_digits,
                f'可输入范围：{cls.__get_range_description__(field_meta)}',
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
            logging.warning('ValueType 类型 <%s> 无法解析 Excel 输入, 返回原值:%s, 原因: %s', cls.__name__, value, exc)
            return str(value) if value is not None else ''

    @classmethod
    def deserialize(cls, value: str | None | Any, field_meta: FieldMetaInfo) -> str:
        if value is None or value == '':
            return ''

        try:
            return str(transform_decimal(Decimal(value)))
        except Exception as exc:
            logging.warning('ValueType 类型 <%s> 无法解析 Excel 输入, 返回原值:%s, 原因: %s', cls.__name__, value, exc)
            return str(value)

    @classmethod
    def __get_range_description__(cls, field_meta: FieldMetaInfo) -> str:  # type: ignore[return]
        match (field_meta.importer_le, field_meta.importer_ge):
            case (None, None):
                return '无限制'
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
            raise ValueError('无效输入，请输入数字。') from exc

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
                errors.append(f'请输入在 {field_meta.importer_ge} 和 {field_meta.importer_le} 之间的数字。')
            elif field_meta.importer_le:
                errors.append(f'请输入在 -∞ 和 {field_meta.importer_le} 之间的数字。')
            elif field_meta.importer_ge:
                errors.append(f'请输入在 {field_meta.importer_ge} 和 +∞ 之间的数字。')
            else:
                pass

        return errors

    @classmethod
    def __validate__(cls, value: Decimal | Any, field_meta: FieldMetaInfo) -> float | int:
        # 如果输入不是 Decimal 类型，尝试转换。
        parsed = cls.__maybe_decimal__(value)
        if parsed is None:
            raise ValueError('无效输入，请输入数字。')
        # 初始化一个错误信息列表。
        errors: list[str] = cls.__check_range__(value, field_meta)
        if errors:
            raise ValueError(*errors)
        parsed = canonicalize_decimal(parsed, field_meta.fraction_digits)
        value = transform_decimal(parsed)
        if value is None:
            raise ValueError('无效输入，请输入数字。')
        return value
