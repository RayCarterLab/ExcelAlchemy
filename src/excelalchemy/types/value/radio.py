"""Compatibility shim for ``excelalchemy.types.value.radio``."""

from excelalchemy._primitives.deprecation import warn_compat_import

warn_compat_import('excelalchemy.types.value.radio', 'excelalchemy.codecs.radio')

from excelalchemy.codecs.radio import *  # noqa: F403
