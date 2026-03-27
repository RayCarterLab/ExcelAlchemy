"""实例化 ExcelAlchemy 时的配置"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Literal

from pydantic import BaseModel

from excelalchemy.core.storage_protocol import ExcelStorage
from excelalchemy.exc import ConfigError
from excelalchemy.helper.pydantic import get_model_field_names
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import message as msg
from excelalchemy.util.convertor import export_data_converter, import_data_converter

if TYPE_CHECKING:
    from minio import Minio


class ExcelMode(str, Enum):
    """Excel 模式"""

    IMPORT = 'IMPORT'
    EXPORT = 'EXPORT'


class ImportMode(str, Enum):
    CREATE = 'CREATE'  # 创建
    UPDATE = 'UPDATE'  # 更新
    CREATE_OR_UPDATE = 'CREATE_OR_UPDATE'  # 创建或更新


@dataclass
class ImporterConfig[ContextT, ImporterCreateModelT: BaseModel, ImporterUpdateModelT: BaseModel]:
    create_importer_model: type[ImporterCreateModelT] | None = field(default=None)
    update_importer_model: type[ImporterUpdateModelT] | None = field(default=None)

    # Callable function receive Key as dict key instead of Label.
    data_converter: Callable[[dict[str, Any]], dict[str, Any]] | None = field(default=import_data_converter)
    creator: Callable[[dict[str, Any], ContextT | None], Awaitable[Any]] | None = field(default=None)
    updater: Callable[[dict[str, Any], ContextT | None], Awaitable[Any]] | None = field(default=None)

    context: ContextT | None = field(default=None)
    is_data_exist: Callable[[dict[str, Any], ContextT | None], Awaitable[bool]] | None = field(default=None)
    exec_formatter: Callable[[Exception], str] = field(default=str)

    import_mode: ImportMode = field(default=ImportMode.CREATE)

    storage: ExcelStorage | None = field(default=None)
    minio: Minio | None = field(default=None)
    bucket_name: str = field(default='excel')
    url_expires: int = field(default=3600)
    locale: str = field(default='zh-CN')

    sheet_name: Literal['Sheet1'] = field(default='Sheet1')

    def validate_model(self):
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

    # 创建模式验证
    def _validate_create(self):
        if self.import_mode != ImportMode.CREATE:
            raise ConfigError(msg(MessageKey.INVALID_IMPORT_MODE, import_mode=self.import_mode))
        if not self.create_importer_model:
            raise ConfigError(msg(MessageKey.CREATE_IMPORTER_MODEL_REQUIRED_CREATE))

    # 更新模式验证
    def _validate_update(self):
        if self.import_mode != ImportMode.UPDATE:
            raise ConfigError(msg(MessageKey.INVALID_IMPORT_MODE, import_mode=self.import_mode))
        if not self.update_importer_model:
            raise ConfigError(msg(MessageKey.UPDATE_IMPORTER_MODEL_REQUIRED_UPDATE))

    # 创建或更新模式验证
    def _validate_create_or_update(self):
        if self.import_mode != ImportMode.CREATE_OR_UPDATE:
            raise ConfigError(msg(MessageKey.INVALID_IMPORT_MODE, import_mode=self.import_mode))

        if not self.create_importer_model:
            raise ConfigError(msg(MessageKey.CREATE_IMPORTER_MODEL_REQUIRED_CREATE_OR_UPDATE))
        if not self.update_importer_model:
            raise ConfigError(msg(MessageKey.UPDATE_IMPORTER_MODEL_REQUIRED_CREATE_OR_UPDATE))
        if not self.is_data_exist:
            raise ConfigError(msg(MessageKey.IS_DATA_EXIST_REQUIRED_CREATE_OR_UPDATE))
        # 创建模型和更新模型的字段必须一致
        if get_model_field_names(self.create_importer_model) != get_model_field_names(self.update_importer_model):
            raise ConfigError(msg(MessageKey.IMPORTER_MODELS_FIELD_NAMES_MUST_MATCH))

    def __post_init__(self):
        self.validate_model()


@dataclass
class ExporterConfig[ExporterModelT: BaseModel]:
    exporter_model: type[ExporterModelT]
    # Callable function receive Key as dict key instead of Label.
    data_converter: Callable[[dict[str, Any]], dict[str, Any]] | None = field(default=export_data_converter)

    storage: ExcelStorage | None = field(default=None)
    minio: Minio | None = field(default=None)
    bucket_name: str = field(default='excel')
    url_expires: int = field(default=3600)
    locale: str = field(default='zh-CN')

    sheet_name: Literal['Sheet1'] = field(default='Sheet1')

    def validate_model(self):
        if not self.exporter_model:
            raise ValueError(msg(MessageKey.EXPORTER_MODEL_CANNOT_BE_EMPTY))
        return self

    def __post_init__(self):
        self.validate_model()
