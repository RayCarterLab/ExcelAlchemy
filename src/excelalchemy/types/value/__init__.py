"""Compatibility shim for ``excelalchemy.types.value``."""

from excelalchemy._primitives.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.value', 'excelalchemy.codecs')

from excelalchemy.codecs import *  # noqa: F403
