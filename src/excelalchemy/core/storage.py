"""Storage factory for resolving ExcelAlchemy storage strategies."""

from typing import TYPE_CHECKING

from pydantic import BaseModel

from excelalchemy.config import ExporterConfig, ImporterConfig
from excelalchemy.core.storage_protocol import ExcelStorage
from excelalchemy.exceptions import ConfigError
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import message as msg

if TYPE_CHECKING:
    from excelalchemy.core.storage_minio import MinioStorageGateway


class MissingStorageGateway(ExcelStorage):
    """Fallback storage used when no concrete backend has been configured."""

    def read_excel_table(self, input_excel_name: str, *, skiprows: int, sheet_name: str):
        raise ConfigError(msg(MessageKey.NO_STORAGE_BACKEND_CONFIGURED))

    def upload_excel(self, output_name: str, content_with_prefix: str):
        raise ConfigError(msg(MessageKey.NO_STORAGE_BACKEND_CONFIGURED))


def build_storage_gateway[
    ContextT,
    ImportCreateModelT: BaseModel,
    ImportUpdateModelT: BaseModel,
    ExportModelT: BaseModel,
](
    config: ImporterConfig[ContextT, ImportCreateModelT, ImportUpdateModelT] | ExporterConfig[ExportModelT],
) -> ExcelStorage:
    """Build the default storage strategy for one ExcelAlchemy config."""
    storage_options = config.storage_options
    if storage_options.storage is not None:
        return storage_options.storage
    if storage_options.minio is not None:
        from excelalchemy.core.storage_minio import MinioStorageGateway

        return MinioStorageGateway(config)
    return MissingStorageGateway()


def __getattr__(name: str) -> object:
    if name == 'MinioStorageGateway':
        from excelalchemy.core.storage_minio import MinioStorageGateway

        return MinioStorageGateway
    raise AttributeError(name)


__all__ = ['ExcelStorage', 'MinioStorageGateway', 'MissingStorageGateway', 'build_storage_gateway']
