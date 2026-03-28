from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from excelalchemy._internal.identity import Key

if TYPE_CHECKING:
    from excelalchemy.metadata import FieldMetaInfo
else:
    FieldMetaInfo = Any


class ExcelFieldCodec(ABC):
    """Excel-facing field adapter responsible for comments, parsing, formatting, and normalization."""

    @classmethod
    @abstractmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        """用于渲染 Excel 表头的注释"""

    @classmethod
    @abstractmethod
    def parse_input(cls, value: Any, field_meta: FieldMetaInfo) -> Any:  # value is always not None
        """用于把用户填入 Excel 的数据，转换成后端代码入口可接收的数据
        如果转换失败，返回原值，用户后续捕获更准确的错误
        """

    @classmethod
    @abstractmethod
    def format_display_value(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        """用于把 worksheet 读入后的值转回用户可识别的数据, 处理聚合之前的数据"""

    @classmethod
    @abstractmethod
    def normalize_import_value(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        """验证用户输入的值是否符合约束. 接收 serialize 后的值"""

    @classmethod
    def comment(cls, field_meta: FieldMetaInfo) -> str:
        """Backward-compatible alias for build_comment()."""
        return cls.build_comment(field_meta)

    @classmethod
    def serialize(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        """Backward-compatible alias for parse_input()."""
        return cls.parse_input(value, field_meta)

    @classmethod
    def deserialize(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        """Backward-compatible alias for format_display_value()."""
        return cls.format_display_value(value, field_meta)

    @classmethod
    def __validate__(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        """Backward-compatible alias for normalize_import_value()."""
        return cls.normalize_import_value(value, field_meta)

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        # ExcelAlchemy runs metadata-aware validation in its adapter layer.
        # Pydantic only needs a permissive schema here so model classes can be built in v2.
        return core_schema.any_schema()


class CompositeExcelFieldCodec(ExcelFieldCodec, dict):
    """Excel codec for fields that expand into multiple worksheet columns."""

    @classmethod
    @abstractmethod
    def column_items(cls) -> list[tuple[Key, FieldMetaInfo]]:
        """用于获取模型的所有字段名"""

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
    def parse_input(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        return value

    @classmethod
    def format_display_value(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        return value

    @classmethod
    def normalize_import_value(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        return value


class Undefined(ExcelFieldCodec):
    __name__ = 'Undefined'

    @classmethod
    def build_comment(cls, field_meta: FieldMetaInfo) -> str:
        return ''

    @classmethod
    def parse_input(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        return value

    @classmethod
    def format_display_value(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        return value

    @classmethod
    def normalize_import_value(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        return value


ABCValueType = ExcelFieldCodec
ComplexABCValueType = CompositeExcelFieldCodec
SystemFieldCodec = SystemReserved
UndefinedFieldCodec = Undefined
