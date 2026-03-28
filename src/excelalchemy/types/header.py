"""Compatibility shim for ``excelalchemy.types.header``."""

from excelalchemy._internal.deprecation import warn_compat_import

warn_compat_import(
    'excelalchemy.types.header',
    'ExcelAlchemy internals only; avoid importing header models directly',
)

from excelalchemy._internal.header_models import *  # noqa: F403
