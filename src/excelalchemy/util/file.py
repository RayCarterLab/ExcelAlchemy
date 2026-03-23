import base64
import io
from datetime import timedelta
from tempfile import TemporaryFile
from typing import IO, Any

import pandas
from minio import Minio
from urllib3.response import BaseHTTPResponse

from excelalchemy.const import UNIQUE_HEADER_CONNECTOR

EXCEL_PREFIX = 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64'


def add_excel_prefix(content: str) -> str:
    """Add Excel prefix for base64 content string."""

    return f'{EXCEL_PREFIX},{content}'


def remove_excel_prefix(content: str) -> str:
    """Remove Excel prefixes for base64 content string."""
    return content.lstrip(f'{EXCEL_PREFIX},')


def construct_file_like_object(response: BaseHTTPResponse) -> IO[bytes]:
    """Construct a file like object from HTTPResponse.

    You must close the file after you finished using it.
    """
    tmp = TemporaryFile()
    tmp.write(response.read())
    tmp.seek(0)
    return tmp


def read_file_from_minio_object(
    client: Minio,
    bucket_name: str,
    filename: str,
) -> IO[bytes]:
    """ "Read file content by <Minio> object."""
    response: BaseHTTPResponse = client.get_object(bucket_name, filename)
    return construct_file_like_object(response)


def upload_file_from_minio_object(
    client: Minio,
    bucket_name: str,
    filename: str,
    content: str,
    expires: int,
) -> str:
    """把文件上传到minio"""

    data = base64.b64decode(content)
    client.put_object(bucket_name, filename, io.BytesIO(data), len(data))
    return client.presigned_get_object(
        bucket_name,
        filename,
        expires=timedelta(seconds=expires),
    )


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
    """判断 value 是否是 NaN"""
    is_nan = pandas.isna(value)
    if isinstance(is_nan, bool) and is_nan:
        return True
    if isinstance(value, list) and any(is_nan):  # type: ignore[arg-type]
        return True
    return False
