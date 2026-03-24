"""Import execution helpers for create, update, and upsert flows."""

from typing import Any, Awaitable, Callable

from pandas import DataFrame
from pydantic import BaseModel

from excelalchemy.exc import ConfigError, ExcelCellError, ExcelRowError
from excelalchemy.helper.pydantic import instantiate_pydantic_model
from excelalchemy.types.alchemy import ImporterConfig, ImportMode
from excelalchemy.types.identity import Key, RowIndex

from .rows import ImportIssueTracker


class ImportExecutor[ContextT]:
    """Execute import-side DML while keeping validation and error mapping isolated."""

    def __init__(
        self,
        config: ImporterConfig[Any, Any, Any],
        issue_tracker: ImportIssueTracker,
        get_context: Callable[[], ContextT | None],
    ):
        self.config = config
        self.issue_tracker = issue_tracker
        self.get_context = get_context

    async def execute(self, row_index: RowIndex, data: dict[Key, Any], df: DataFrame) -> bool:
        """Dispatch one aggregated row to the configured import mode handler."""
        match self.config.import_mode:
            case ImportMode.CREATE:
                return await self._create(row_index, data, df)
            case ImportMode.UPDATE:
                return await self._update(row_index, data, df)
            case ImportMode.CREATE_OR_UPDATE:
                return await self._create_or_update(row_index, data, df)
        raise ConfigError(f'不支持的导入模式: {self.config.import_mode}')

    async def _create(self, row_index: RowIndex, data: dict[Key, Any], df: DataFrame) -> bool:
        if self.config.creator is None:
            raise ConfigError('未配置 creator')
        if self.config.create_importer_model is None:
            raise ConfigError('未配置 create_importer_model')
        return await self._invoke_dml(
            row_index,
            data,
            df,
            self.config.create_importer_model,
            self.config.creator,
            self.config.data_converter,
            self.config.exec_formatter,
        )

    async def _update(self, row_index: RowIndex, data: dict[Key, Any], df: DataFrame) -> bool:
        if self.config.updater is None:
            raise ConfigError('未配置 updater')
        if self.config.update_importer_model is None:
            raise ConfigError('未配置 update_importer_model')
        return await self._invoke_dml(
            row_index,
            data,
            df,
            self.config.update_importer_model,
            self.config.updater,
            self.config.data_converter,
            self.config.exec_formatter,
        )

    async def _create_or_update(self, row_index: RowIndex, data: dict[Key, Any], df: DataFrame) -> bool:
        if self.config.is_data_exist is None:
            raise ConfigError('未配置 is_data_exists')

        converted_data = self.config.data_converter(dict(data)) if self.config.data_converter else data
        is_data_exist = await self.config.is_data_exist(converted_data, self.get_context())
        if is_data_exist:
            return await self._update(row_index, data, df)
        return await self._create(row_index, data, df)

    async def _invoke_dml(
        self,
        row_index: RowIndex,
        data: dict[Key, Any],
        df: DataFrame,
        importer_model: type[BaseModel],
        dml_func: Callable[[dict[str, Any], ContextT | None], Awaitable[Any]],
        data_converter: Callable[[dict[str, Any]], dict[str, Any]] | None,
        exec_formatter: Callable[[Exception], str],
    ) -> bool:
        """Validate one row payload and call the user-supplied DML function."""
        importer_instance_or_errors = instantiate_pydantic_model(data, importer_model)
        if not isinstance(importer_instance_or_errors, importer_model):
            errors: list[ExcelCellError] = importer_instance_or_errors  # type: ignore[assignment]
            self.issue_tracker.register_row_error(row_index, errors)
            self.issue_tracker.register_cell_errors(row_index, errors, df)
            return False

        importer_instance = importer_instance_or_errors
        converted_data = importer_instance.model_dump(exclude_unset=True)
        if data_converter is not None:
            converted_data = data_converter(converted_data)

        try:
            await dml_func(converted_data, self.get_context())
        except ExcelCellError as error:
            self.issue_tracker.register_row_error(row_index, error)
            return False
        except Exception as error:
            self.issue_tracker.register_row_error(row_index, ExcelRowError(exec_formatter(error)))
            return False

        return True
