import math
from collections.abc import Mapping, Sequence
from typing import cast

from excelalchemy._primitives.constants import UNIQUE_HEADER_CONNECTOR

EXCEL_MEDIA_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
EXCEL_PREFIX = f'data:{EXCEL_MEDIA_TYPE};base64'


def add_excel_prefix(content: str) -> str:
    """Add Excel prefix for base64 content string."""

    return f'{EXCEL_PREFIX},{content}'


def remove_excel_prefix(content: str) -> str:
    """Remove Excel prefixes for base64 content string."""
    prefix = f'{EXCEL_PREFIX},'
    return content.removeprefix(prefix)


def flatten(data: Mapping[str, object], level: list[str] | None = None) -> dict[str, object]:
    """Flatten a nested mapping into unique-header paths.

    >>> flatten( {'a': {'b': {'c': 12}}})  # dotted path expansion
    {'a.b.c': 12}
    """
    tmp_dict: dict[str, object] = {}
    level = level or []
    for key, val in data.items():
        if isinstance(val, Mapping):
            nested = cast(Mapping[str, object], val)
            tmp_dict.update(flatten(nested, [*level, key]))
        else:
            tmp_dict[f'{UNIQUE_HEADER_CONNECTOR}'.join([*level, key])] = val
    return tmp_dict


def value_is_nan(value: object) -> bool:
    """Return whether a worksheet value should be treated as empty or NaN."""
    if value is None:
        return True

    if isinstance(value, float) and math.isnan(value):
        return True

    if isinstance(value, Sequence) and not isinstance(value, str):
        items = cast(Sequence[object], value)
        return any(value_is_nan(item) for item in items)

    return False
