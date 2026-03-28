"""Compatibility shim for ``excelalchemy.types.identity``."""

from excelalchemy._primitives.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.identity', 'the excelalchemy package root')

from excelalchemy._primitives.identity import *  # noqa: F403
