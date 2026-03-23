"""ExcelAlchemy value types，用于生成 pydantic 的模型时，用于标记字段的类型"""

from excelalchemy.types.abstract import ABCValueType

EXCEL_CHOICE_VALUE_TYPE: dict[type[ABCValueType], type[ABCValueType]] = {}


def excel_choice(value_type: type[ABCValueType]) -> type[ABCValueType]:
    EXCEL_CHOICE_VALUE_TYPE[value_type] = value_type
    return value_type
