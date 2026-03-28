"""Compatibility shim for ``excelalchemy.types.value.url``."""

from excelalchemy._primitives.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.value.url', 'excelalchemy.codecs.url')

from excelalchemy.codecs.url import *  # noqa: F403
