from typing import Any, ClassVar

from excelalchemy.types.field import FieldMetaInfo
from excelalchemy.types.value.number import Number


class Money(Number):
    MONEY_FRACTION_DIGITS: ClassVar[int] = 2

    @classmethod
    def _money_field_meta(cls, field_meta: FieldMetaInfo) -> FieldMetaInfo:
        money_field_meta = field_meta.clone()
        money_field_meta.fraction_digits = cls.MONEY_FRACTION_DIGITS
        return money_field_meta

    @classmethod
    def comment(cls, field_meta: FieldMetaInfo) -> str:
        return super().comment(cls._money_field_meta(field_meta))

    @classmethod
    def deserialize(cls, value: str | None | Any, field_meta: FieldMetaInfo) -> str:
        return super().deserialize(value, cls._money_field_meta(field_meta))

    @classmethod
    def __validate__(cls, value: Any, field_meta: FieldMetaInfo) -> float | int:
        return super().__validate__(value, cls._money_field_meta(field_meta))
