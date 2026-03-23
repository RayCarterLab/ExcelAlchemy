"""定义了一些用于标识的类型"""

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
    """Excel 的列名"""


class UniqueLabel(Label):
    """Excel 唯一的列名"""


class Key(_StringIdentity):
    """Python 模型的键名"""


class UniqueKey(Key):
    """Python 模型唯一的键名"""


class RowIndex(_IntegerIdentity):
    """Excel 的行索引, 从 0 开始"""


class ColumnIndex(_IntegerIdentity):
    """Excel 的列索引, 从 0 开始"""


class OptionId(_StringIdentity):
    """选项 ID"""


class Base64Str(_StringIdentity):
    """Base64 编码的字符串"""


class UrlStr(_StringIdentity):
    """URL 字符串"""
