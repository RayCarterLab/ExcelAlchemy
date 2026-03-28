"""Compatibility shim for ``excelalchemy.types.value.number``."""

from excelalchemy._internal.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.value.number', 'excelalchemy.codecs.number')

from excelalchemy.codecs.number import *  # noqa: F403
