"""Compatibility shim for ``excelalchemy.types.value.staff``."""

from excelalchemy._primitives.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.value.staff', 'excelalchemy.codecs.staff')

from excelalchemy.codecs.staff import *  # noqa: F403
