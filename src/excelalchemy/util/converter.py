import re
from typing import cast

from excelalchemy._primitives.constants import FIELD_DATA_KEY
from excelalchemy._primitives.identity import Key
from excelalchemy._primitives.payloads import ModelRowPayload


def import_data_converter(data: ModelRowPayload) -> ModelRowPayload:
    result: ModelRowPayload = {}
    for key, value in data.items():
        nested_keys = [_to_snake_case(part) for part in key.split('.')]
        _nested_set(result, nested_keys, value)
    return result


def export_data_converter(data: ModelRowPayload, to_camel: bool = False) -> ModelRowPayload:
    result: ModelRowPayload = {}
    for key, value in data.items():
        converted_key = _to_camel_case(key) if to_camel else _to_snake_case(key)
        if converted_key != FIELD_DATA_KEY:
            result[converted_key] = value
            continue
        if not value:
            continue
        if not isinstance(value, dict):
            raise TypeError(f'Expected fieldData payload to be a mapping, got {type(value)}')

        for field_key, field_value in cast(ModelRowPayload, value).items():
            result[Key(f'{converted_key}.{field_key}')] = field_value
    return result


def _to_snake_case(name: str) -> str:
    first_pass = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', first_pass).lower()


def _to_camel_case(snake_case: str) -> str:
    components = snake_case.split('_')
    return components[0] + ''.join(part.capitalize() if part else '_' for part in components[1:])


def _nested_set(mapping: ModelRowPayload, keys: list[str], value: object) -> None:
    for key in keys[:-1]:
        nested_mapping = mapping.setdefault(key, {})
        if not isinstance(nested_mapping, dict):
            raise TypeError(f'Expected nested mapping at {key!r}, got {type(nested_mapping)}')
        mapping = cast(ModelRowPayload, nested_mapping)
    mapping[keys[-1]] = value
