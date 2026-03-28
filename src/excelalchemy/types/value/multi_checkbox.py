"""Compatibility shim for ``excelalchemy.types.value.multi_checkbox``."""

from excelalchemy._primitives.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.value.multi_checkbox', 'excelalchemy.codecs.multi_checkbox')

from excelalchemy.codecs.multi_checkbox import *  # noqa: F403
