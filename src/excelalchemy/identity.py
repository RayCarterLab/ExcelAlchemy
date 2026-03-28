"""Compatibility shim for ``excelalchemy.identity``."""

from excelalchemy._primitives.deprecation import warn_compat_import

warn_compat_import('excelalchemy.identity', 'the excelalchemy package root')

from excelalchemy._primitives.identity import *  # noqa: F403
