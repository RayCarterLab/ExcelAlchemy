"""Configuration mode enums."""

from enum import StrEnum


class ExcelMode(StrEnum):
    """Top-level Excel workflow mode."""

    IMPORT = 'IMPORT'
    EXPORT = 'EXPORT'


class ImportMode(StrEnum):
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    CREATE_OR_UPDATE = 'CREATE_OR_UPDATE'


__all__ = ['ExcelMode', 'ImportMode']
