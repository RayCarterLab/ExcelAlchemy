"""Compatibility shim for ``excelalchemy.exc``."""

from excelalchemy._internal.deprecation import warn_compat_import

warn_compat_import('excelalchemy.exc', 'excelalchemy.exceptions')

from excelalchemy.exceptions import *  # noqa: F403

