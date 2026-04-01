"""Import execution helpers for create, update, and upsert flows."""

from collections.abc import Callable

from pydantic import BaseModel

from excelalchemy._primitives.identity import RowIndex
from excelalchemy._primitives.payloads import DataConverter, DmlCallback, ImportContext, ModelRowPayload
from excelalchemy.config import ImporterConfig, ImportMode
from excelalchemy.exceptions import ConfigError, ExcelCellError, ExcelRowError
from excelalchemy.helper.pydantic import instantiate_pydantic_model
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import message as msg

from .rows import ImportIssueTracker
from .table import WorksheetTable


class ImportExecutor[ContextT, ImportCreateModelT: BaseModel, ImportUpdateModelT: BaseModel]:
    """Execute import-side DML while keeping validation and error mapping isolated."""

    def __init__(
        self,
        config: ImporterConfig[ContextT, ImportCreateModelT, ImportUpdateModelT],
        issue_tracker: ImportIssueTracker,
        get_context: Callable[[], ImportContext[ContextT]],
    ):
        self.config = config
        self.schema_options = config.schema_options
        self.behavior = config.behavior
        self.issue_tracker = issue_tracker
        self.get_context = get_context

    async def execute(self, row_index: RowIndex, data: ModelRowPayload, worksheet_table: WorksheetTable) -> bool:
        """Dispatch one aggregated row to the configured import mode handler."""
        match self.behavior.import_mode:
            case ImportMode.CREATE:
                return await self._create(row_index, data, worksheet_table)
            case ImportMode.UPDATE:
                return await self._update(row_index, data, worksheet_table)
            case ImportMode.CREATE_OR_UPDATE:
                return await self._create_or_update(row_index, data, worksheet_table)
        raise ConfigError(msg(MessageKey.UNSUPPORTED_IMPORT_MODE, import_mode=self.behavior.import_mode))

    async def _create(self, row_index: RowIndex, data: ModelRowPayload, worksheet_table: WorksheetTable) -> bool:
        if self.behavior.creator is None:
            raise ConfigError(msg(MessageKey.CREATOR_NOT_CONFIGURED))
        if self.schema_options.create_importer_model is None:
            raise ConfigError(msg(MessageKey.CREATE_IMPORTER_MODEL_NOT_CONFIGURED))
        return await self._invoke_dml(
            row_index,
            data,
            worksheet_table,
            self.schema_options.create_importer_model,
            self.behavior.creator,
            self.behavior.data_converter,
            self.behavior.exec_formatter,
        )

    async def _update(self, row_index: RowIndex, data: ModelRowPayload, worksheet_table: WorksheetTable) -> bool:
        if self.behavior.updater is None:
            raise ConfigError(msg(MessageKey.UPDATER_NOT_CONFIGURED))
        if self.schema_options.update_importer_model is None:
            raise ConfigError(msg(MessageKey.UPDATE_IMPORTER_MODEL_NOT_CONFIGURED))
        return await self._invoke_dml(
            row_index,
            data,
            worksheet_table,
            self.schema_options.update_importer_model,
            self.behavior.updater,
            self.behavior.data_converter,
            self.behavior.exec_formatter,
        )

    async def _create_or_update(
        self,
        row_index: RowIndex,
        data: ModelRowPayload,
        worksheet_table: WorksheetTable,
    ) -> bool:
        if self.behavior.is_data_exist is None:
            raise ConfigError(msg(MessageKey.IS_DATA_EXIST_NOT_CONFIGURED))

        converted_data = self.behavior.data_converter(dict(data)) if self.behavior.data_converter else data
        is_data_exist = await self.behavior.is_data_exist(converted_data, self.get_context())
        if is_data_exist:
            return await self._update(row_index, data, worksheet_table)
        return await self._create(row_index, data, worksheet_table)

    async def _invoke_dml(
        self,
        row_index: RowIndex,
        data: ModelRowPayload,
        worksheet_table: WorksheetTable,
        importer_model: type[BaseModel],
        dml_func: DmlCallback[ContextT],
        data_converter: DataConverter | None,
        exec_formatter: Callable[[Exception], str],
    ) -> bool:
        """Validate one row payload and call the user-supplied DML function."""
        importer_instance_or_errors = instantiate_pydantic_model(data, importer_model)
        if isinstance(importer_instance_or_errors, list):
            validation_errors = importer_instance_or_errors
            cell_errors = [error for error in validation_errors if isinstance(error, ExcelCellError)]
            self.issue_tracker.register_row_error(row_index, validation_errors)
            if cell_errors:
                self.issue_tracker.register_cell_errors(row_index, cell_errors, worksheet_table)
            return False

        converted_data = importer_instance_or_errors.model_dump(exclude_unset=True)
        if data_converter is not None:
            converted_data = data_converter(converted_data)

        try:
            await dml_func(converted_data, self.get_context())
        except ExcelCellError as error:
            self.issue_tracker.register_row_error(row_index, error)
            self.issue_tracker.register_cell_errors(row_index, [error], worksheet_table)
            return False
        except Exception as error:
            self.issue_tracker.register_row_error(row_index, ExcelRowError(exec_formatter(error)))
            return False

        return True
