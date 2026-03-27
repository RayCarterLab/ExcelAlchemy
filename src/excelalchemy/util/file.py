import math
from typing import Any

from excelalchemy.const import UNIQUE_HEADER_CONNECTOR

EXCEL_PREFIX = 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64'


def add_excel_prefix(content: str) -> str:
    """Add Excel prefix for base64 content string."""

    return f'{EXCEL_PREFIX},{content}'


def remove_excel_prefix(content: str) -> str:
    """Remove Excel prefixes for base64 content string."""
    return content.lstrip(f'{EXCEL_PREFIX},')


def flatten(data: dict[str, Any], level: list[Any] | None = None) -> dict[str, Any]:
    """平铺嵌套的字典

    >>> flatten( {'a': {'b': {'c': 12}}})  # dotted path expansion
    {'a.b.c': 12}
    """
    tmp_dict = {}
    level = level or []
    for key, val in data.items():
        if isinstance(val, dict):
            tmp_dict.update(flatten(val, level + [key]))
        else:
            tmp_dict[f'{UNIQUE_HEADER_CONNECTOR}'.join(level + [key])] = val
    return tmp_dict


def value_is_nan(value: Any) -> bool:
    """判断 value 是否为空单元格或 NaN。"""
    if value is None:
        return True

    if isinstance(value, float) and math.isnan(value):
        return True

    if isinstance(value, list | tuple):
        return any(value_is_nan(item) for item in value)

    return False
