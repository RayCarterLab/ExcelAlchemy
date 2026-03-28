"""Compatibility re-exports for the pre-refactor ``excelalchemy.types`` namespace."""

from excelalchemy._primitives.deprecation import warn_compat_import

warn_compat_import(
    'excelalchemy.types',
    'excelalchemy.metadata, excelalchemy.results, excelalchemy.config, excelalchemy.codecs, and the excelalchemy package root',
)

from excelalchemy._primitives.header_models import *  # noqa: F403
from excelalchemy._primitives.identity import *  # noqa: F403
from excelalchemy.codecs.base import *  # noqa: F403
from excelalchemy.config import *  # noqa: F403
from excelalchemy.metadata import *  # noqa: F403
from excelalchemy.results import *  # noqa: F403
