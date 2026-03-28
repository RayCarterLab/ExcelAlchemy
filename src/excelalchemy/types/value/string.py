"""Compatibility shim for ``excelalchemy.types.value.string``."""

from excelalchemy._primitives.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.value.string', 'excelalchemy.codecs.string')

from excelalchemy.codecs.string import *  # noqa: F403
