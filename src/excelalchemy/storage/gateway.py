"""Storage gateway resolution for ExcelAlchemy configs."""

from pydantic import BaseModel

from excelalchemy.config import ExporterConfig, ImporterConfig
from excelalchemy.errors import ConfigError
from excelalchemy.messages import MessageKey
from excelalchemy.messages import message as msg
from excelalchemy.primitives.identity import UrlStr
from excelalchemy.storage.base import ExcelStorage
from excelalchemy.workbook.table import WorksheetTable


class MissingStorageGateway(ExcelStorage):
    """Fallback storage used when no concrete backend has been configured."""

    def read_excel_table(self, input_excel_name: str, *, skiprows: int, sheet_name: str) -> WorksheetTable:
        raise ConfigError(msg(MessageKey.NO_STORAGE_BACKEND_CONFIGURED))

    def upload_excel(self, output_name: str, content_with_prefix: str) -> UrlStr:
        raise ConfigError(msg(MessageKey.NO_STORAGE_BACKEND_CONFIGURED))


def build_storage_gateway[
    ContextT,
    ImportCreateModelT: BaseModel,
    ImportUpdateModelT: BaseModel,
    ExportModelT: BaseModel,
](
    config: ImporterConfig[ContextT, ImportCreateModelT, ImportUpdateModelT] | ExporterConfig[ExportModelT],
) -> ExcelStorage:
    """Resolve the configured storage strategy for one ExcelAlchemy config."""
    storage_options = config.storage_options
    if storage_options.storage is not None:
        return storage_options.storage
    return MissingStorageGateway()


__all__ = ['MissingStorageGateway', 'build_storage_gateway']
