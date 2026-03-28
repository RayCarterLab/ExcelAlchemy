"""Compatibility shim for ``excelalchemy.header_models``."""

from excelalchemy._internal.deprecation import warn_compat_import

warn_compat_import(
    'excelalchemy.header_models',
    'ExcelAlchemy internals only; avoid importing header models directly',
)

from excelalchemy._internal.header_models import *  # noqa: F403

