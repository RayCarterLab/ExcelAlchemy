"""Compatibility shim for ``excelalchemy.types.identity``."""

from excelalchemy._internal.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.identity', 'the excelalchemy package root')

from excelalchemy._internal.identity import *  # noqa: F403
