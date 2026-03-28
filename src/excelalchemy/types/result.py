"""Compatibility shim for ``excelalchemy.types.result``."""

from excelalchemy._internal.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.result', 'excelalchemy.results')

from excelalchemy.results import *  # noqa: F403
