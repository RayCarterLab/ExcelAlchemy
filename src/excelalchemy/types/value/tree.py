"""Compatibility shim for ``excelalchemy.types.value.tree``."""

from excelalchemy._internal.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.value.tree', 'excelalchemy.codecs.tree')

from excelalchemy.codecs.tree import *  # noqa: F403
