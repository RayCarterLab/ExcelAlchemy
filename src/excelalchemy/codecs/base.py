from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, cast

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from excelalchemy._primitives.identity import Key

if TYPE_CHECKING:
    from excelalchemy.metadata import FieldMetaInfo

# These aliases remain `Any` intentionally because codec subclasses narrow their
# accepted workbook values heavily. Using `object` here makes every override
# incompatible under pyright's method override rules.
type WorkbookInputValue = Any
type WorkbookDisplayValue = Any
type NormalizedImportValue = Any


def _summarize_exception(exc: Exception) -> str:
    details: list[str] = []
    for arg in exc.args:
        if isinstance(arg, list):
            raw_items = cast(list[object], arg)
            list_items: list[str] = []
            for item in raw_items:
                item_text = item.__name__ if isinstance(item, type) else str(item).strip()
                if item_text:
                    list_items.append(item_text)
            if list_items:
                details.append(', '.join(list_items))
            continue

        text = str(arg).strip()
        if text:
            details.append(text)

    if details:
        return '; '.join(details)
    return exc.__class__.__name__


def log_codec_parse_fallback(
    codec_name: str,
    value: object,
    *,
    field_label: str | None = None,
    exc: Exception,
) -> None:
    field_context = f' for field "{field_label}"' if field_label else ''
    logging.warning(
        'Codec %s could not parse workbook input%s; keeping the original value %r. Reason: %s',
        codec_name,
        field_context,
        value,
        _summarize_exception(exc),
    )


def log_codec_render_fallback(
    codec_name: str,
    value: object,
    *,
    field_label: str | None = None,
    exc: Exception,
) -> None:
    field_context = f' for field "{field_label}"' if field_label else ''
    logging.warning(
        'Codec %s could not format workbook value%s; returning %r as-is. Reason: %s',
        codec_name,
        field_context,
        value,
        _summarize_exception(exc),
    )


class ExcelFieldCodec(ABC):
    """Excel-facing field adapter responsible for comments, parsing, formatting, and normalization."""

    @classmethod
    @abstractmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        """Return the header comment rendered into the workbook template."""

    @classmethod
    @abstractmethod
    def parse_input(cls, value: WorkbookInputValue, field_meta: FieldMetaInfo) -> WorkbookInputValue:
        """Parse workbook input into the intermediate Python value consumed by the import pipeline."""

    @classmethod
    @abstractmethod
    def format_display_value(cls, value: WorkbookDisplayValue, field_meta: FieldMetaInfo) -> WorkbookDisplayValue:
        """Format a raw worksheet value back into a user-recognizable display value."""

    @classmethod
    @abstractmethod
    def normalize_import_value(cls, value: WorkbookInputValue, field_meta: FieldMetaInfo) -> NormalizedImportValue:
        """Validate and normalize parsed input before handing it to the Pydantic layer."""

    @classmethod
    def expected_input_message(cls, field_meta: FieldMetaInfo) -> str | None:
        """Return a user-facing input hint for invalid values when one is known."""
        return None

    @classmethod
    def comment(cls, field_meta: FieldMetaInfo) -> str:
        """Backward-compatible alias for build_comment()."""
        return cls.build_comment(field_meta)

    @classmethod
    def serialize(cls, value: WorkbookInputValue, field_meta: FieldMetaInfo) -> WorkbookInputValue:
        """Backward-compatible alias for parse_input()."""
        return cls.parse_input(value, field_meta)

    @classmethod
    def deserialize(cls, value: WorkbookDisplayValue, field_meta: FieldMetaInfo) -> WorkbookDisplayValue:
        """Backward-compatible alias for format_display_value()."""
        return cls.format_display_value(value, field_meta)

    @classmethod
    def __validate__(cls, value: WorkbookInputValue, field_meta: FieldMetaInfo) -> NormalizedImportValue:
        """Backward-compatible alias for normalize_import_value()."""
        return cls.normalize_import_value(value, field_meta)

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: object,
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        # ExcelAlchemy runs metadata-aware validation in its adapter layer.
        # Pydantic only needs a permissive schema here so model classes can be built in v2.
        return core_schema.any_schema()


class CompositeExcelFieldCodec(ExcelFieldCodec, dict[str, object]):
    """Excel codec for fields that expand into multiple worksheet columns."""

    @classmethod
    @abstractmethod
    def column_items(cls) -> list[tuple[Key, FieldMetaInfo]]:
        """Return the schema keys and metadata for each expanded worksheet column."""

    @classmethod
    def model_items(cls) -> list[tuple[Key, FieldMetaInfo]]:
        """Backward-compatible alias for column_items()."""
        return cls.column_items()


class SystemReserved(ExcelFieldCodec):
    __name__ = 'SystemReserved'

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        return ''

    @classmethod
    def parse_input(cls, value: WorkbookInputValue, field_meta: FieldMetaInfo) -> WorkbookInputValue:
        return value

    @classmethod
    def format_display_value(
        cls,
        value: WorkbookDisplayValue,
        field_meta: FieldMetaInfo,
    ) -> WorkbookDisplayValue:
        return value

    @classmethod
    def normalize_import_value(
        cls,
        value: WorkbookInputValue,
        field_meta: FieldMetaInfo,
    ) -> NormalizedImportValue:
        return value


class Undefined(ExcelFieldCodec):
    __name__ = 'Undefined'

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        return ''

    @classmethod
    def parse_input(cls, value: WorkbookInputValue, field_meta: FieldMetaInfo) -> WorkbookInputValue:
        return value

    @classmethod
    def format_display_value(
        cls,
        value: WorkbookDisplayValue,
        field_meta: FieldMetaInfo,
    ) -> WorkbookDisplayValue:
        return value

    @classmethod
    def normalize_import_value(
        cls,
        value: WorkbookInputValue,
        field_meta: FieldMetaInfo,
    ) -> NormalizedImportValue:
        return value


ABCValueType = ExcelFieldCodec
ComplexABCValueType = CompositeExcelFieldCodec
SystemFieldCodec = SystemReserved
UndefinedFieldCodec = Undefined
