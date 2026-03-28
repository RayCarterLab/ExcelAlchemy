"""Compatibility shim for ``excelalchemy.types.value.email``."""

from excelalchemy._primitives.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.value.email', 'excelalchemy.codecs.email')

from excelalchemy.codecs.email import *  # noqa: F403
