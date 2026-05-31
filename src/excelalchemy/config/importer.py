"""Importer configuration object."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Self

from pydantic import BaseModel

from excelalchemy.adapters.pydantic import get_model_field_names
from excelalchemy.config.modes import ImportMode
from excelalchemy.config.options import ImportBehavior, ImporterSchemaOptions, StorageOptions
from excelalchemy.errors import ConfigError
from excelalchemy.messages import MessageKey
from excelalchemy.messages import message as msg
from excelalchemy.primitives.payloads import DataConverter, DmlCallback, ExistenceCheckCallback, ImportContext
from excelalchemy.storage import ExcelStorage
from excelalchemy.util.converter import import_data_converter


@dataclass(slots=True)
class ImporterConfig[ContextT, ImportCreateModelT: BaseModel, ImportUpdateModelT: BaseModel]:
    create_importer_model: type[ImportCreateModelT] | None = None
    update_importer_model: type[ImportUpdateModelT] | None = None

    # The converter receives schema keys rather than workbook labels.
    data_converter: DataConverter | None = import_data_converter
    creator: DmlCallback[ContextT] | None = None
    updater: DmlCallback[ContextT] | None = None

    context: ImportContext[ContextT] = None
    is_data_exist: ExistenceCheckCallback[ContextT] | None = None
    exec_formatter: Callable[[Exception], str] = str

    import_mode: ImportMode = ImportMode.CREATE

    storage: ExcelStorage | None = None
    locale: str = 'zh-CN'

    sheet_name: str = 'Sheet1'
    schema_options: ImporterSchemaOptions[ImportCreateModelT, ImportUpdateModelT] = field(init=False, repr=False)
    behavior: ImportBehavior[ContextT] = field(init=False, repr=False)
    storage_options: StorageOptions = field(init=False, repr=False)

    @classmethod
    def for_create(
        cls,
        importer_model: type[ImportCreateModelT],
        *,
        data_converter: DataConverter | None = import_data_converter,
        creator: DmlCallback[ContextT] | None = None,
        updater: DmlCallback[ContextT] | None = None,
        context: ImportContext[ContextT] = None,
        is_data_exist: ExistenceCheckCallback[ContextT] | None = None,
        exec_formatter: Callable[[Exception], str] = str,
        storage: ExcelStorage | None = None,
        locale: str = 'zh-CN',
        sheet_name: str = 'Sheet1',
    ) -> Self:
        """Build a create-mode importer config through the recommended constructor."""
        return cls(
            create_importer_model=importer_model,
            data_converter=data_converter,
            creator=creator,
            updater=updater,
            context=context,
            is_data_exist=is_data_exist,
            exec_formatter=exec_formatter,
            import_mode=ImportMode.CREATE,
            storage=storage,
            locale=locale,
            sheet_name=sheet_name,
        )

    @classmethod
    def for_update(
        cls,
        importer_model: type[ImportUpdateModelT],
        *,
        data_converter: DataConverter | None = import_data_converter,
        creator: DmlCallback[ContextT] | None = None,
        updater: DmlCallback[ContextT] | None = None,
        context: ImportContext[ContextT] = None,
        is_data_exist: ExistenceCheckCallback[ContextT] | None = None,
        exec_formatter: Callable[[Exception], str] = str,
        storage: ExcelStorage | None = None,
        locale: str = 'zh-CN',
        sheet_name: str = 'Sheet1',
    ) -> Self:
        """Build an update-mode importer config through the recommended constructor."""
        return cls(
            update_importer_model=importer_model,
            data_converter=data_converter,
            creator=creator,
            updater=updater,
            context=context,
            is_data_exist=is_data_exist,
            exec_formatter=exec_formatter,
            import_mode=ImportMode.UPDATE,
            storage=storage,
            locale=locale,
            sheet_name=sheet_name,
        )

    @classmethod
    def for_create_or_update(
        cls,
        *,
        create_importer_model: type[ImportCreateModelT],
        update_importer_model: type[ImportUpdateModelT],
        is_data_exist: ExistenceCheckCallback[ContextT],
        data_converter: DataConverter | None = import_data_converter,
        creator: DmlCallback[ContextT] | None = None,
        updater: DmlCallback[ContextT] | None = None,
        context: ImportContext[ContextT] = None,
        exec_formatter: Callable[[Exception], str] = str,
        storage: ExcelStorage | None = None,
        locale: str = 'zh-CN',
        sheet_name: str = 'Sheet1',
    ) -> Self:
        """Build a create-or-update importer config through the recommended constructor."""
        return cls(
            create_importer_model=create_importer_model,
            update_importer_model=update_importer_model,
            data_converter=data_converter,
            creator=creator,
            updater=updater,
            context=context,
            is_data_exist=is_data_exist,
            exec_formatter=exec_formatter,
            import_mode=ImportMode.CREATE_OR_UPDATE,
            storage=storage,
            locale=locale,
            sheet_name=sheet_name,
        )

    def validate_model(self) -> Self:
        if self.import_mode not in ImportMode.__members__.values():
            raise ConfigError(msg(MessageKey.INVALID_IMPORT_MODE, import_mode=self.import_mode))

        match self.import_mode:
            case ImportMode.CREATE:
                self._validate_create()
            case ImportMode.UPDATE:
                self._validate_update()
            case ImportMode.CREATE_OR_UPDATE:
                self._validate_create_or_update()

        return self

    def _validate_create(self) -> None:
        if self.import_mode != ImportMode.CREATE:
            raise ConfigError(msg(MessageKey.INVALID_IMPORT_MODE, import_mode=self.import_mode))
        if not self.create_importer_model:
            raise ConfigError(msg(MessageKey.CREATE_IMPORTER_MODEL_REQUIRED_CREATE))

    def _validate_update(self) -> None:
        if self.import_mode != ImportMode.UPDATE:
            raise ConfigError(msg(MessageKey.INVALID_IMPORT_MODE, import_mode=self.import_mode))
        if not self.update_importer_model:
            raise ConfigError(msg(MessageKey.UPDATE_IMPORTER_MODEL_REQUIRED_UPDATE))

    def _validate_create_or_update(self) -> None:
        if self.import_mode != ImportMode.CREATE_OR_UPDATE:
            raise ConfigError(msg(MessageKey.INVALID_IMPORT_MODE, import_mode=self.import_mode))

        if not self.create_importer_model:
            raise ConfigError(msg(MessageKey.CREATE_IMPORTER_MODEL_REQUIRED_CREATE_OR_UPDATE))
        if not self.update_importer_model:
            raise ConfigError(msg(MessageKey.UPDATE_IMPORTER_MODEL_REQUIRED_CREATE_OR_UPDATE))
        if not self.is_data_exist:
            raise ConfigError(msg(MessageKey.IS_DATA_EXIST_REQUIRED_CREATE_OR_UPDATE))
        # Create and update models must expose the same schema keys.
        if get_model_field_names(self.create_importer_model) != get_model_field_names(self.update_importer_model):
            raise ConfigError(msg(MessageKey.IMPORTER_MODELS_FIELD_NAMES_MUST_MATCH))

    def __post_init__(self) -> None:
        self.validate_model()
        self.schema_options = ImporterSchemaOptions(
            create_importer_model=self.create_importer_model,
            update_importer_model=self.update_importer_model,
            sheet_name=self.sheet_name,
            locale=self.locale,
        )
        self.behavior = ImportBehavior(
            data_converter=self.data_converter,
            creator=self.creator,
            updater=self.updater,
            context=self.context,
            is_data_exist=self.is_data_exist,
            exec_formatter=self.exec_formatter,
            import_mode=self.import_mode,
        )
        self.storage_options = StorageOptions(storage=self.storage)


__all__ = ['ImporterConfig']
