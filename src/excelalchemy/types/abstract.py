"""Compatibility shim for ``excelalchemy.types.abstract``."""

from excelalchemy._primitives.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.abstract', 'excelalchemy.codecs.base')

from excelalchemy.codecs.base import *  # noqa: F403
