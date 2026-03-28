"""Compatibility shim for ``excelalchemy.types.value.date``."""

from excelalchemy._primitives.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.value.date', 'excelalchemy.codecs.date')

from excelalchemy.codecs.date import *  # noqa: F403
