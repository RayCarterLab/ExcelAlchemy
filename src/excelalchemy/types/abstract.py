from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Iterable

from pydantic.fields import ModelField

from excelalchemy.types.identity import Key

if TYPE_CHECKING:
    # pyright: reportImportCycles=false
    from excelalchemy.types.field import FieldMetaInfo
else:
    FieldMetaInfo = Any


class ABCValueType(ABC):
    """
    raw_data --> serialize --> __validate__
    raw_data--> deserialize
    """

    @classmethod
    @abstractmethod
    def comment(cls, field_meta: FieldMetaInfo) -> str:
        """用于渲染 Excel 表头的注释"""

    @classmethod
    @abstractmethod
    def serialize(cls, value: Any, field_meta: FieldMetaInfo) -> Any:  # value is always not None
        """用于把用户填入 Excel 的数据，转换成后端代码入口可接收的数据
        如果转换失败，返回原值，用户后续捕获更准确的错误
        """

    @classmethod
    @abstractmethod
    def deserialize(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        """用于把 pandas 读取的 Excel 之后的数据，转回用户可识别的数据, 处理聚合之前的数据"""

    @classmethod
    def __wrapped_validate__(cls, value: Any, field: ModelField) -> Any:
        # pyright: reportGeneralTypeIssues=false
        return cls.__validate__(value, field.field_info)  # type: ignore[arg-type]

    @classmethod
    @abstractmethod
    def __validate__(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        """验证用户输入的值是否符合约束. 接收 serialize 后的值"""

    @classmethod
    def __get_validators__(cls) -> Iterable[Any]:
        yield cls.__wrapped_validate__


class ComplexABCValueType(ABCValueType, dict):
    """用于生成 pydantic 的模型时，用于标记字段的类型"""

    @classmethod
    @abstractmethod
    def comment(cls, field_meta: FieldMetaInfo) -> str:
        """用于渲染 Excel 表头的注释"""

    @classmethod
    @abstractmethod
    def serialize(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        """用于把用户填入 Excel 的数据，转换成后端代码入口可接收的数据
        如果转换失败，返回原值，用户后续捕获更准确的错误
        serialize 是聚合之后的数据
        """

    @classmethod
    @abstractmethod
    def deserialize(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        """用于把 pandas 读取的 Excel 之后的数据，转回用户可识别的数据, 处理聚合之前的数据"""

    @classmethod
    @abstractmethod
    def model_items(cls) -> list[tuple[Key, FieldMetaInfo]]:
        """用于获取模型的所有字段名"""


class SystemReserved(ABCValueType):
    __name__ = 'SystemReserved'

    @classmethod
    def comment(cls, field_meta: FieldMetaInfo) -> str:
        return ''

    @classmethod
    def serialize(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        return value

    @classmethod
    def deserialize(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        return value

    @classmethod
    def __validate__(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        return value


class Undefined(ABCValueType):
    __name__ = 'Undefined'

    @classmethod
    def comment(cls, field_meta: FieldMetaInfo) -> str:
        return ''

    @classmethod
    def serialize(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        return value

    @classmethod
    def deserialize(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        return value

    @classmethod
    def __validate__(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        return value
