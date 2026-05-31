"""Exporter configuration object."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self

from pydantic import BaseModel

from excelalchemy.config.options import ExportBehavior, ExporterSchemaOptions, StorageOptions
from excelalchemy.messages import MessageKey
from excelalchemy.messages import message as msg
from excelalchemy.primitives.payloads import DataConverter
from excelalchemy.storage import ExcelStorage
from excelalchemy.util.converter import export_data_converter


@dataclass(slots=True)
class ExporterConfig[ExportModelT: BaseModel]:
    exporter_model: type[ExportModelT]
    # The converter receives schema keys rather than workbook labels.
    data_converter: DataConverter | None = export_data_converter

    storage: ExcelStorage | None = None
    locale: str = 'zh-CN'

    sheet_name: str = 'Sheet1'
    schema_options: ExporterSchemaOptions[ExportModelT] = field(init=False, repr=False)
    behavior: ExportBehavior = field(init=False, repr=False)
    storage_options: StorageOptions = field(init=False, repr=False)

    @classmethod
    def for_model(
        cls,
        exporter_model: type[ExportModelT],
        *,
        data_converter: DataConverter | None = export_data_converter,
        storage: ExcelStorage | None = None,
        locale: str = 'zh-CN',
        sheet_name: str = 'Sheet1',
    ) -> Self:
        """Build an exporter config through the recommended constructor."""
        return cls(
            exporter_model=exporter_model,
            data_converter=data_converter,
            storage=storage,
            locale=locale,
            sheet_name=sheet_name,
        )

    @classmethod
    def for_storage(
        cls,
        exporter_model: type[ExportModelT],
        *,
        storage: ExcelStorage,
        data_converter: DataConverter | None = export_data_converter,
        locale: str = 'zh-CN',
        sheet_name: str = 'Sheet1',
    ) -> Self:
        """Build an exporter config for the recommended explicit-storage path."""
        return cls.for_model(
            exporter_model,
            data_converter=data_converter,
            storage=storage,
            locale=locale,
            sheet_name=sheet_name,
        )

    def validate_model(self) -> Self:
        if not self.exporter_model:
            raise ValueError(msg(MessageKey.EXPORTER_MODEL_CANNOT_BE_EMPTY))
        return self

    def __post_init__(self) -> None:
        self.validate_model()
        self.schema_options = ExporterSchemaOptions(
            exporter_model=self.exporter_model,
            sheet_name=self.sheet_name,
            locale=self.locale,
        )
        self.behavior = ExportBehavior(data_converter=self.data_converter)
        self.storage_options = StorageOptions(storage=self.storage)


__all__ = ['ExporterConfig']
