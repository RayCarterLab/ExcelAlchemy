"""Compatibility shim for ``excelalchemy.identity``."""

from excelalchemy._internal.deprecation import warn_compat_import

warn_compat_import('excelalchemy.identity', 'the excelalchemy package root')

from excelalchemy._internal.identity import *  # noqa: F403

