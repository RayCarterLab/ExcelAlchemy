"""Compatibility shim for ``excelalchemy.types.value.boolean``."""

from excelalchemy._internal.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.value.boolean', 'excelalchemy.codecs.boolean')

from excelalchemy.codecs.boolean import *  # noqa: F403
