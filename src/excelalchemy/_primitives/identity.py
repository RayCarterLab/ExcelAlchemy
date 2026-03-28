"""Internal typed primitives used across the ExcelAlchemy core layer."""

from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class _StringIdentity(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(cls, core_schema.str_schema())


class _IntegerIdentity(int):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(cls, core_schema.int_schema())


class Label(_StringIdentity):
    """Workbook header label."""


class UniqueLabel(Label):
    """Fully qualified workbook header label."""


class Key(_StringIdentity):
    """Schema key used by the Python model."""


class UniqueKey(Key):
    """Fully qualified schema key."""


class RowIndex(_IntegerIdentity):
    """Zero-based workbook row index."""


class ColumnIndex(_IntegerIdentity):
    """Zero-based workbook column index."""


class OptionId(_StringIdentity):
    """Selection option identifier."""


class DataUrlStr(_StringIdentity):
    """Data URL string."""


class Base64Str(DataUrlStr):
    """Deprecated compatibility alias for the legacy data URL string return type."""


class UrlStr(_StringIdentity):
    """Generic URL string."""
