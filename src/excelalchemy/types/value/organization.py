"""Compatibility shim for ``excelalchemy.types.value.organization``."""

from excelalchemy._internal.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.value.organization', 'excelalchemy.codecs.organization')

from excelalchemy.codecs.organization import *  # noqa: F403
