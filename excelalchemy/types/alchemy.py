"""实例化 ExcelAlchemy 时的配置"""
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Generic
from typing import Literal
from typing import Type

from minio import Minio

from excelalchemy.const import ContextT
from excelalchemy.const import ExporterModelT
from excelalchemy.const import ImporterCreateModelT
from excelalchemy.const import ImporterUpdateModelT
from excelalchemy.exc import ConfigError
from excelalchemy.util.convertor import export_data_converter
from excelalchemy.util.convertor import import_data_converter


class ExcelMode(str, Enum):
    """Excel 模式"""

    IMPORT = 'IMPORT'
    EXPORT = 'EXPORT'


class ImportMode(str, Enum):
    CREATE = 'CREATE'  # 创建
    UPDATE = 'UPDATE'  # 更新
    CREATE_OR_UPDATE = 'CREATE_OR_UPDATE'  # 创建或更新


@dataclass
class ImporterConfig(Generic[ContextT, ImporterCreateModelT, ImporterUpdateModelT]):
    create_importer_model: Type[ImporterCreateModelT] | None = field(default=None)
    update_importer_model: Type[ImporterUpdateModelT] | None = field(default=None)

    # Callable function receive Key as dict key instead of Label.
    data_converter: Callable[[dict[str, Any]], dict[str, Any]] | None = field(default=import_data_converter)
    creator: Callable[[dict[str, Any], ContextT | None], Awaitable[Any]] | None = field(default=None)
    updater: Callable[[dict[str, Any], ContextT | None], Awaitable[Any]] | None = field(default=None)

    context: ContextT | None = field(default=None)
    is_data_exist: Callable[[dict[str, Any], ContextT | None], Awaitable[bool]] | None = field(default=None)
    exec_formatter: Callable[[Exception], str] = field(default=str)

    import_mode: ImportMode = field(default=ImportMode.CREATE)

    minio: Minio | None = field(default=None)
    bucket_name: str = field(default='excel')
    url_expires: int = field(default=3600)

    sheet_name: Literal['Sheet1'] = field(default='Sheet1')

    def validate_model(self):
        if self.import_mode not in ImportMode.__members__.values():
            raise ConfigError(f'导入模式 {self.import_mode} 不合法')

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
            raise ConfigError(f'导入模式 {self.import_mode} 不合法')
        if not self.create_importer_model:
            raise ConfigError('当选择【创建模式】时，创建模型不能为空')

    # 更新模式验证
    def _validate_update(self):
        if self.import_mode != ImportMode.UPDATE:
            raise ConfigError(f'导入模式 {self.import_mode} 不合法')
        if not self.update_importer_model:
            raise ConfigError('当选择【更新模式】时，更新模型不能为空')

    # 创建或更新模式验证
    def _validate_create_or_update(self):
        if self.import_mode != ImportMode.CREATE_OR_UPDATE:
            raise ConfigError(f'导入模式 {self.import_mode} 不合法')

        if not self.create_importer_model:
            raise ConfigError('当选择【创建或更新模式】时，创建模型不能为空')
        if not self.update_importer_model:
            raise ConfigError('当选择【创建或更新模式】时，更新模型不能为空')
        if not self.is_data_exist:
            raise ConfigError('当选择【创建或更新模式】时，数据存在判断函数不能为空')
        # 创建模型和更新模型的字段必须一致
        if self.create_importer_model.__fields__.keys() != self.update_importer_model.__fields__.keys():
            raise ConfigError('创建模型和更新模型的字段名称必须一致')

    def __post_init__(self):
        self.validate_model()


@dataclass
class ExporterConfig(Generic[ExporterModelT]):
    exporter_model: Type[ExporterModelT]
    # Callable function receive Key as dict key instead of Label.
    data_converter: Callable[[dict[str, Any]], dict[str, Any]] | None = field(default=export_data_converter)

    minio: Minio | None = field(default=None)
    bucket_name: str = field(default='excel')
    url_expires: int = field(default=3600)

    sheet_name: Literal['Sheet1'] = field(default='Sheet1')

    def validate_model(self):
        if not self.exporter_model:
            raise ValueError('导出模型不能为空')
        return self

    def __post_init__(self):
        self.validate_model()
