"""Compatibility shim for ``excelalchemy.types.value.money``."""

from excelalchemy._primitives.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.value.money', 'excelalchemy.codecs.money')

from excelalchemy.codecs.money import *  # noqa: F403
