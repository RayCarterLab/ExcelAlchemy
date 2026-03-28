"""Storage factory for resolving ExcelAlchemy storage strategies."""

from typing import TYPE_CHECKING, Any

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
    ImporterCreateModelT: BaseModel,
    ImporterUpdateModelT: BaseModel,
    ExporterModelT: BaseModel,
](
    config: ImporterConfig[ContextT, ImporterCreateModelT, ImporterUpdateModelT] | ExporterConfig[ExporterModelT],
) -> ExcelStorage:
    """Build the default storage strategy for one ExcelAlchemy config."""
    storage = getattr(config, 'storage', None)
    if storage is not None:
        return storage
    if getattr(config, 'minio', None) is not None:
        from excelalchemy.core.storage_minio import MinioStorageGateway

        return MinioStorageGateway(config)
    return MissingStorageGateway()


def __getattr__(name: str) -> Any:
    if name == 'MinioStorageGateway':
        from excelalchemy.core.storage_minio import MinioStorageGateway

        return MinioStorageGateway
    raise AttributeError(name)


__all__ = ['ExcelStorage', 'MinioStorageGateway', 'MissingStorageGateway', 'build_storage_gateway']
