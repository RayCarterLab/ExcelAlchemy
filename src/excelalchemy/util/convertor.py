"""Deprecated compatibility shim for the historical converter module name."""

from excelalchemy._primitives.deprecation import warn_compat_import
from excelalchemy.util.converter import export_data_converter, import_data_converter

warn_compat_import('excelalchemy.util.convertor', 'excelalchemy.util.converter')

__all__ = ['export_data_converter', 'import_data_converter']
