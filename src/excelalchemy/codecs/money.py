from dataclasses import replace
from typing import ClassVar

from excelalchemy.codecs.base import NormalizedImportValue, WorkbookDisplayValue, WorkbookInputValue
from excelalchemy.codecs.number import Number
from excelalchemy.metadata import FieldMetaInfo


class Money(Number):
    MONEY_FRACTION_DIGITS: ClassVar[int] = 2

    @classmethod
    def _money_field_meta(cls, field_meta: FieldMetaInfo) -> FieldMetaInfo:
        money_field_meta = field_meta.clone()
        money_field_meta.presentation_meta = replace(
            money_field_meta.presentation_meta,
            fraction_digits=cls.MONEY_FRACTION_DIGITS,
        )
        return money_field_meta

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        return super().build_comment(cls._money_field_meta(field_meta))

    @classmethod
    def format_display_value(
        cls,
        value: str | WorkbookDisplayValue | None,
        field_meta: FieldMetaInfo,
    ) -> str:
        return super().format_display_value(value, cls._money_field_meta(field_meta))

    @classmethod
    def normalize_import_value(
        cls,
        value: WorkbookInputValue,
        field_meta: FieldMetaInfo,
    ) -> NormalizedImportValue:
        return super().normalize_import_value(value, cls._money_field_meta(field_meta))


MoneyCodec = Money
