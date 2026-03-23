import re
from typing import Any

from excelalchemy.const import FIELD_DATA_KEY
from excelalchemy.types.identity import Key


def import_data_converter(data: dict[str, Any]) -> dict[str, Any]:  # noqa: C901
    # _to_snake_case
    result: dict[str, Any] = {}
    for k, v in data.items():
        snake_keys = [_to_snake_case(key) for key in k.split('.')]
        _nested_set(result, snake_keys, v)
    return result


def export_data_converter(data: dict[str, Any], to_camel: bool = False) -> dict[str, Any]:  # noqa: C901
    result: dict[str, Any] = {}
    for k, v in data.items():
        camel_key = _to_camel_case(k) if to_camel else _to_snake_case(k)
        if camel_key != FIELD_DATA_KEY:
            result[camel_key] = v
            continue
        if not v:
            continue

        for field_key, field_value in v.items():
            result[Key(f'{camel_key}.{field_key}')] = field_value
    return result


def _to_snake_case(name: str) -> str:
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def _to_camel_case(snake_str: str) -> str:
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'capitalize' method and join them together.
    return components[0] + ''.join(x.capitalize() if x else '_' for x in components[1:])


def _nested_set(obj: dict[str, Any], keys: list[str], value: Any) -> None:
    for key in keys[:-1]:
        obj = obj.setdefault(key, {})
    obj[keys[-1]] = value
