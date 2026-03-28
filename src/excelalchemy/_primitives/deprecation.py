"""Deprecation helpers for public compatibility layers."""

from __future__ import annotations

import warnings

DEPRECATION_REMOVAL_VERSION = '3.0'


class ExcelAlchemyDeprecationWarning(FutureWarning):
    """Warning emitted for deprecated public APIs that still have a compatibility shim."""


def warn_compat_import(import_path: str, replacement: str) -> None:
    warnings.warn(
        (
            f'`{import_path}` is deprecated and will be removed in ExcelAlchemy '
            f'{DEPRECATION_REMOVAL_VERSION}. Import from `{replacement}` instead.'
        ),
        category=ExcelAlchemyDeprecationWarning,
        stacklevel=2,
    )
