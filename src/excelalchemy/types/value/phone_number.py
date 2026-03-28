"""Compatibility shim for ``excelalchemy.types.value.phone_number``."""

from excelalchemy._primitives.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.value.phone_number', 'excelalchemy.codecs.phone_number')

from excelalchemy.codecs.phone_number import *  # noqa: F403
