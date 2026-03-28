"""Compatibility shim for ``excelalchemy.header_models``."""

from excelalchemy._primitives.deprecation import warn_compat_import

warn_compat_import(
    'excelalchemy.header_models',
    'ExcelAlchemy internals only; avoid importing header models directly',
)

from excelalchemy._primitives.header_models import *  # noqa: F403
