"""Compatibility shim for ``excelalchemy.types.value.number_range``."""

from excelalchemy._internal.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.value.number_range', 'excelalchemy.codecs.number_range')

from excelalchemy.codecs.number_range import *  # noqa: F403
