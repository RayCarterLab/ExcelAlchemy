"""Configuration objects used to instantiate the ExcelAlchemy facade."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel

from excelalchemy._primitives.deprecation import DEPRECATION_REMOVAL_VERSION, ExcelAlchemyDeprecationWarning
from excelalchemy._primitives.payloads import DataConverter, DmlCallback, ExistenceCheckCallback, ImportContext
from excelalchemy.core.storage_protocol import ExcelStorage
from excelalchemy.exceptions import ConfigError
from excelalchemy.helper.pydantic import get_model_field_names
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import message as msg
from excelalchemy.util.converter import export_data_converter, import_data_converter

if TYPE_CHECKING:
    from minio import Minio


_EMITTED_STORAGE_DEPRECATION_WARNINGS: set[bool] = set()


class ExcelMode(StrEnum):
    """Top-level Excel workflow mode."""

    IMPORT = 'IMPORT'
    EXPORT = 'EXPORT'


class ImportMode(StrEnum):
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    CREATE_OR_UPDATE = 'CREATE_OR_UPDATE'


@dataclass(slots=True, frozen=True)
class StorageOptions:
    """Normalized storage backend settings shared by importer and exporter configs."""

    storage: ExcelStorage | None
    minio: Minio | None
    bucket_name: str
    url_expires: int

    @property
    def has_explicit_storage(self) -> bool:
        return self.storage is not None

    @property
    def has_legacy_minio(self) -> bool:
        return self.minio is not None

    @property
    def uses_legacy_minio_path(self) -> bool:
        return self.storage is None and self.minio is not None


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
    minio: Minio | None = None
    bucket_name: str = 'excel'
    url_expires: int = 3600
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
        minio: Minio | None = None,
        bucket_name: str = 'excel',
        url_expires: int = 3600,
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
            minio=minio,
            bucket_name=bucket_name,
            url_expires=url_expires,
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
        minio: Minio | None = None,
        bucket_name: str = 'excel',
        url_expires: int = 3600,
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
            minio=minio,
            bucket_name=bucket_name,
            url_expires=url_expires,
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
        minio: Minio | None = None,
        bucket_name: str = 'excel',
        url_expires: int = 3600,
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
            minio=minio,
            bucket_name=bucket_name,
            url_expires=url_expires,
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
        self.storage_options = StorageOptions(
            storage=self.storage,
            minio=self.minio,
            bucket_name=self.bucket_name,
            url_expires=self.url_expires,
        )
        if self.storage_options.has_legacy_minio:
            _warn_legacy_storage_path(has_explicit_storage=self.storage_options.has_explicit_storage)


@dataclass(slots=True)
class ExporterConfig[ExportModelT: BaseModel]:
    exporter_model: type[ExportModelT]
    # The converter receives schema keys rather than workbook labels.
    data_converter: DataConverter | None = export_data_converter

    storage: ExcelStorage | None = None
    minio: Minio | None = None
    bucket_name: str = 'excel'
    url_expires: int = 3600
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
        minio: Minio | None = None,
        bucket_name: str = 'excel',
        url_expires: int = 3600,
        locale: str = 'zh-CN',
        sheet_name: str = 'Sheet1',
    ) -> Self:
        """Build an exporter config through the recommended constructor."""
        return cls(
            exporter_model=exporter_model,
            data_converter=data_converter,
            storage=storage,
            minio=minio,
            bucket_name=bucket_name,
            url_expires=url_expires,
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
        self.storage_options = StorageOptions(
            storage=self.storage,
            minio=self.minio,
            bucket_name=self.bucket_name,
            url_expires=self.url_expires,
        )
        if self.storage_options.has_legacy_minio:
            _warn_legacy_storage_path(has_explicit_storage=self.storage_options.has_explicit_storage)


def _warn_legacy_storage_path(*, has_explicit_storage: bool) -> None:
    """Emit a deprecation warning for the legacy built-in Minio config path."""
    if has_explicit_storage in _EMITTED_STORAGE_DEPRECATION_WARNINGS:
        return
    _EMITTED_STORAGE_DEPRECATION_WARNINGS.add(has_explicit_storage)

    detail = (
        ' The explicit `storage=` backend will be used.'
        if has_explicit_storage
        else ' Prefer passing `storage=` with `MinioStorageGateway` or a custom `ExcelStorage` implementation.'
    )
    warnings.warn(
        (
            '`minio`, `bucket_name`, and `url_expires` are deprecated configuration fields and will be removed in '
            f'ExcelAlchemy {DEPRECATION_REMOVAL_VERSION}.{detail}'
        ),
        category=ExcelAlchemyDeprecationWarning,
        stacklevel=3,
    )
