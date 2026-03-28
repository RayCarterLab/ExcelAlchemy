"""Compatibility shim for ``excelalchemy.types.field``."""

from excelalchemy._internal.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.field', 'excelalchemy.metadata')

from excelalchemy.metadata import *  # noqa: F403
