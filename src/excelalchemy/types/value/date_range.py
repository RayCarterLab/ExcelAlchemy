"""Compatibility shim for ``excelalchemy.types.value.date_range``."""

from excelalchemy._internal.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.value.date_range', 'excelalchemy.codecs.date_range')

from excelalchemy.codecs.date_range import *  # noqa: F403
