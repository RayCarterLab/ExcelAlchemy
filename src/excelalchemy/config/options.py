"""Normalized config option groups."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel

from excelalchemy.config.modes import ImportMode
from excelalchemy.primitives.payloads import DataConverter, DmlCallback, ExistenceCheckCallback, ImportContext
from excelalchemy.storage import ExcelStorage


@dataclass(slots=True, frozen=True)
class StorageOptions:
    """Normalized storage backend settings shared by importer and exporter configs."""

    storage: ExcelStorage | None

    @property
    def has_storage(self) -> bool:
        return self.storage is not None


@dataclass(slots=True, frozen=True)
class ImporterSchemaOptions[ImportCreateModelT: BaseModel, ImportUpdateModelT: BaseModel]:
    """Schema declaration and workbook presentation settings for imports."""

    create_importer_model: type[ImportCreateModelT] | None
    update_importer_model: type[ImportUpdateModelT] | None
    sheet_name: str
    locale: str


@dataclass(slots=True, frozen=True)
class ImportBehavior[ContextT]:
    """Execution callbacks and import workflow policy."""

    data_converter: DataConverter | None
    creator: DmlCallback[ContextT] | None
    updater: DmlCallback[ContextT] | None
    context: ImportContext[ContextT]
    is_data_exist: ExistenceCheckCallback[ContextT] | None
    exec_formatter: Callable[[Exception], str]
    import_mode: ImportMode


@dataclass(slots=True, frozen=True)
class ExporterSchemaOptions[ExportModelT: BaseModel]:
    """Schema declaration and workbook presentation settings for exports."""

    exporter_model: type[ExportModelT]
    sheet_name: str
    locale: str


@dataclass(slots=True, frozen=True)
class ExportBehavior:
    """Execution behavior used when rendering export rows."""

    data_converter: DataConverter | None


__all__ = [
    'ExportBehavior',
    'ExporterSchemaOptions',
    'ImportBehavior',
    'ImporterSchemaOptions',
    'StorageOptions',
]
