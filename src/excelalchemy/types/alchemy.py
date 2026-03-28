"""Compatibility shim for ``excelalchemy.types.alchemy``."""

from excelalchemy._primitives.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.alchemy', 'excelalchemy.config')

from excelalchemy.config import *  # noqa: F403
