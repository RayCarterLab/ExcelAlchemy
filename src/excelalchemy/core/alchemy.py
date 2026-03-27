import logging
from functools import cached_property
from typing import Any, Callable, Iterable, cast

from pydantic import BaseModel

from excelalchemy.const import (
    REASON_COLUMN_KEY,
    REASON_COLUMN_LABEL,
    RESULT_COLUMN_KEY,
    RESULT_COLUMN_LABEL,
)
from excelalchemy.core.abstract import ABCExcelAlchemy
from excelalchemy.core.executor import ImportExecutor
from excelalchemy.core.headers import ExcelHeaderParser, ExcelHeaderValidator
from excelalchemy.core.rendering import ExcelRenderer
from excelalchemy.core.rows import ImportIssueTracker, RowAggregator
from excelalchemy.core.schema import ExcelSchemaLayout
from excelalchemy.core.storage import build_storage_gateway
from excelalchemy.core.storage_protocol import ExcelStorage
from excelalchemy.core.table import WorksheetTable
from excelalchemy.exc import ConfigError, ExcelCellError, ExcelRowError
from excelalchemy.helper.pydantic import get_model_field_names
from excelalchemy.types.abstract import SystemReserved
from excelalchemy.types.alchemy import ExcelMode, ExporterConfig, ImporterConfig, ImportMode
from excelalchemy.types.field import FieldMetaInfo
from excelalchemy.types.header import ExcelHeader
from excelalchemy.types.identity import Base64Str, Key, Label, RowIndex, UniqueKey, UniqueLabel, UrlStr
from excelalchemy.types.result import ImportResult, ValidateHeaderResult, ValidateResult
from excelalchemy.util.file import flatten

HEADER_HINT_LINE_COUNT = 1

RESULT_COLUMN = FieldMetaInfo(label=RESULT_COLUMN_LABEL)
RESULT_COLUMN.parent_label = RESULT_COLUMN.label
RESULT_COLUMN.key = RESULT_COLUMN.parent_key = RESULT_COLUMN_KEY
RESULT_COLUMN.value_type = SystemReserved

REASON_COLUMN = FieldMetaInfo(label=REASON_COLUMN_LABEL)
REASON_COLUMN.parent_label = REASON_COLUMN.label
REASON_COLUMN.key = REASON_COLUMN.parent_key = REASON_COLUMN_KEY
REASON_COLUMN.value_type = SystemReserved


class ExcelAlchemy[
    ContextT,
    ImporterCreateModelT: BaseModel,
    ImporterUpdateModelT: BaseModel,
    CreateModelT: BaseModel,
    UpdateModelT: BaseModel,
    ExporterModelT: BaseModel,
](
    ABCExcelAlchemy[
        ContextT,
        ImporterCreateModelT,
        ImporterUpdateModelT,
        CreateModelT,
        UpdateModelT,
        ExporterModelT,
    ]
):
    def __init__(
        self,
        config: ImporterConfig[ContextT, ImporterCreateModelT, ImporterUpdateModelT] | ExporterConfig[ExporterModelT],
    ):
        self.df = WorksheetTable()
        self.header_df = WorksheetTable()
        self.config = config
        self.context: ContextT | None = None
        self.__state_df_has_been_loaded__ = False

        self.import_result_field_meta: list[FieldMetaInfo] = [RESULT_COLUMN, REASON_COLUMN]
        self.import_result_label_to_field_meta = {
            field_meta.unique_label: field_meta for field_meta in self.import_result_field_meta
        }

        self._header_parser = ExcelHeaderParser()
        self._header_validator = ExcelHeaderValidator()
        self._renderer = ExcelRenderer()
        self._storage_gateway: ExcelStorage = build_storage_gateway(config)
        self._layout: ExcelSchemaLayout
        self._issue_tracker: ImportIssueTracker | None = None
        self._row_aggregator: RowAggregator | None = None
        self._executor: ImportExecutor[ContextT] | None = None

        self.__init_from_config__()

    def __init_from_config__(self) -> None:
        self.context = getattr(self.config, 'context', None)
        model = self.__get_importer_model__()
        self._layout = ExcelSchemaLayout.from_model(model)
        self.__sync_layout_state__()

        self._issue_tracker = ImportIssueTracker(self._layout, self.import_result_field_meta)
        self.cell_errors = self._issue_tracker.cell_errors
        self.row_errors = self._issue_tracker.row_errors

        if isinstance(self.config, ImporterConfig):
            self._row_aggregator = RowAggregator(self._layout, self.config.import_mode)
            self._executor = ImportExecutor(self.config, self._issue_tracker, lambda: self.context)

    def __sync_layout_state__(self) -> None:
        self.field_metas = self._layout.field_metas
        self.unique_label_to_field_meta = self._layout.unique_label_to_field_meta
        self.parent_label_to_field_metas = self._layout.parent_label_to_field_metas
        self.parent_key_to_field_metas = self._layout.parent_key_to_field_metas
        self.unique_key_to_field_meta = self._layout.unique_key_to_field_meta
        self.ordered_field_meta = self._layout.ordered_field_meta

    def __get_importer_model__(self) -> type[ImporterCreateModelT] | type[ImporterUpdateModelT] | type[ExporterModelT]:
        importer_model = None
        if self.excel_mode == ExcelMode.IMPORT:
            if not isinstance(self.config, ImporterConfig):
                raise ConfigError(f'导入模式的配置类必须是 {ImporterConfig.__name__}')
            if self.config.import_mode in (ImportMode.CREATE, ImportMode.CREATE_OR_UPDATE):
                importer_model = self.config.create_importer_model  # type: ignore[assignment]
            elif self.config.import_mode == ImportMode.UPDATE:
                importer_model = self.config.update_importer_model  # type: ignore[assignment]
        elif self.excel_mode == ExcelMode.EXPORT:
            if not isinstance(self.config, ExporterConfig):
                raise ConfigError(f'导出模式的配置类必须是 {ExporterConfig.__name__}')
            importer_model = self.config.exporter_model  # type: ignore[assignment]

        if importer_model is None:
            raise ConfigError('请检查配置类是否定义了导入模型或导出模型')
        return importer_model

    def download_template(self, sample_data: list[dict[str, Any]] | None = None) -> str:
        if self.excel_mode != ExcelMode.IMPORT:
            raise ConfigError('只支持导入模式调用此方法')

        keys = self._select_output_excel_keys()
        has_merged_header = self.has_merged_header(keys)
        if has_merged_header:
            df = self._export_with_merged_header(sample_data, keys)
        else:
            df = self._export_with_simple_header(sample_data, keys)
        return self._renderer.render_template(df, self.unique_label_to_field_meta, has_merged_header=has_merged_header)

    async def import_data(self, input_excel_name: str, output_excel_name: str) -> ImportResult:
        assert isinstance(self.config, ImporterConfig)
        assert self._executor is not None
        if self.excel_mode != ExcelMode.IMPORT:
            raise ConfigError('只支持导入模式调用此方法')

        validate_header = self._validate_header(input_excel_name)
        if not validate_header.is_valid:
            return ImportResult.from_validate_header_result(validate_header)

        self.df = self.df.iloc[1:]
        self._set_columns(self.df)
        self.df = self.df.reset_index(drop=True)

        all_success, success_count, fail_count = True, 0, 0
        for table_row_index, row in self.df.iloc[self.extra_header_count_on_import :].iterrows():
            aggregate_data = self._aggregate_data(cast(dict[UniqueLabel, Any], row.to_dict()))
            success = await self._executor.execute(cast(RowIndex, table_row_index), aggregate_data, self.df)
            all_success = all_success and success
            success_count, fail_count = (success_count + 1, fail_count) if success else (success_count, fail_count + 1)

        url = None
        if not all_success:
            self._add_result_column()
            content_with_prefix = self._render_import_result_excel()
            url = self._upload_file(output_excel_name, content_with_prefix)

        return ImportResult(
            result=(ValidateResult.DATA_INVALID, ValidateResult.SUCCESS)[int(all_success)],
            url=url,
            success_count=success_count,
            fail_count=fail_count,
        )

    def export(self, data: list[dict[str, Any]], keys: list[Key] | None = None) -> Base64Str:
        df, has_merged_header = self._gen_export_df(data, keys)
        return self._renderer.render_data(
            df,
            field_meta_mapping=self.unique_label_to_field_meta,
            has_merged_header=has_merged_header,
            errors={},
        )

    def export_upload(self, output_name: str, data: list[dict[str, Any]], keys: list[Key] | None = None) -> UrlStr:
        return self._upload_file(output_name, self.export(data, keys))

    def add_context(self, context: ContextT) -> None:
        if self.context is not None:
            logging.warning('已经存在旧的转换模型上下文, 旧的上下文将被替换, 请确认此操作符合预期')
        self.context = context

    @cached_property
    def input_excel_has_merged_header(self) -> bool:
        if not self.__state_df_has_been_loaded__:
            raise ConfigError('请保证 df 已经初始化')
        return self._header_parser.has_merged_header(self.header_df)

    @cached_property
    def input_excel_headers(self) -> list[ExcelHeader]:
        if not self.__state_df_has_been_loaded__:
            raise ConfigError('请保证 df 已经初始化')
        return self._header_parser.extract(self.header_df)

    @property
    def excel_mode(self) -> ExcelMode:
        if isinstance(self.config, ImporterConfig):
            return ExcelMode.IMPORT
        return ExcelMode.EXPORT

    @property
    def extra_header_count_on_import(self) -> int:
        if self.excel_mode != ExcelMode.IMPORT:
            raise ConfigError('只支持导入模式读取此属性')

        for input_excel_label in self.input_excel_headers:
            if input_excel_label.label != input_excel_label.parent_label:
                return 1
        return 0

    @property
    def exporter_model(self) -> type[ExporterModelT]:
        if isinstance(self.config, ImporterConfig):
            if self.config.create_importer_model and self.config.update_importer_model:
                raise ConfigError('从导入模型推断导出模型失败, 请手动设置导出模型')
            if self.config.create_importer_model:
                logging.info('从导入模型推断导出模型, 请确认此操作符合预期,使用的是 create_importer_model')
                return cast(type[ExporterModelT], self.config.create_importer_model)
            if self.config.update_importer_model:
                logging.info('从导入模型推断导出模型, 请确认此操作符合预期,使用的是 update_importer_model')
                return cast(type[ExporterModelT], self.config.update_importer_model)
            raise ConfigError('从导入模型推断导出模型失败, 请手动设置导出模型')

        return self.config.exporter_model

    def has_merged_header(self, selected_keys: list[UniqueKey]) -> bool:
        return self._layout.has_merged_header(selected_keys)

    def get_output_parent_excel_headers(self, selected_keys: list[UniqueKey] | None = None) -> list[UniqueLabel]:
        return self._layout.get_output_parent_excel_headers(selected_keys)

    def get_output_child_excel_headers(self, selected_keys: list[UniqueKey] | None = None) -> list[Label]:
        return self._layout.get_output_child_excel_headers(selected_keys)

    def _gen_export_df(self, data: list[dict[str, Any]], keys: list[Key] | None = None) -> tuple[WorksheetTable, bool]:
        if self.excel_mode == ExcelMode.IMPORT:
            logging.info('导出模式为导入模式, 调用导出方法时自动切换为导出模式')

        input_keys = keys or list(
            filter(None, [cast(Key | None, field_meta.parent_key) for field_meta in self.ordered_field_meta])
        )
        model_keys = cast(list[Key], get_model_field_names(self.exporter_model))
        if unrecognized := (set(input_keys) - set(model_keys)):
            logging.warning('导出的列 {%s} 不在模型 {%s} 中', unrecognized, model_keys)

        selected_keys = self._select_output_excel_keys(list(set(input_keys).intersection(set(model_keys))))
        has_merged_header = self.has_merged_header(selected_keys)
        if has_merged_header:
            df = self._export_with_merged_header(data, selected_keys, self.config.data_converter)
        else:
            df = self._export_with_simple_header(data, selected_keys, self.config.data_converter)
        return df, has_merged_header

    def _validate_header(self, input_excel_name: str) -> ValidateHeaderResult:
        if self.excel_mode != ExcelMode.IMPORT:
            raise ConfigError('只支持导入模式调用此方法')
        assert isinstance(self.config, ImporterConfig)
        self._read_dataframe(input_excel_name)
        return self._header_validator.validate(self.input_excel_headers, self._layout, self.config.import_mode)

    def _render_import_result_excel(self) -> str:
        return self._renderer.render_data(
            self.df,
            field_meta_mapping=self.import_result_label_to_field_meta | self.unique_label_to_field_meta,
            has_merged_header=self.input_excel_has_merged_header,
            errors=self.cell_errors,
        )

    def _upload_file(self, output_name: str, content_with_prefix: str) -> UrlStr:
        return self._storage_gateway.upload_excel(output_name, content_with_prefix)

    def _order_errors(self, errors: list[ExcelRowError | ExcelCellError]) -> Iterable[ExcelCellError | ExcelRowError]:
        return self._layout.order_errors(errors)

    def _set_columns(self, df: WorksheetTable) -> WorksheetTable:
        return self._header_parser.apply_columns(df, self.input_excel_headers, self.get_output_parent_excel_headers())

    def _select_output_excel_keys(self, keys: list[Key] | None = None) -> list[UniqueKey]:
        return self._layout.select_output_excel_keys(keys)

    def _read_dataframe(self, input_excel_name: str) -> WorksheetTable:
        assert isinstance(self.config, ImporterConfig)
        if not self.__state_df_has_been_loaded__:
            df = self._storage_gateway.read_excel_table(
                input_excel_name,
                skiprows=HEADER_HINT_LINE_COUNT,
                sheet_name=self.config.sheet_name,
            )
            self.df = df
            self.header_df = df.head(2)
            self.__state_df_has_been_loaded__ = True
        return self.df

    def _generate_export_df(
        self,
        records: list[dict[str, Any]] | None,
        selected_keys: list[UniqueKey],
        data_converter: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> WorksheetTable:
        rows = []
        records = records or []
        for record in records:
            row = {}
            record = data_converter(record) if data_converter else record
            for key, value in flatten(record).items():  # type: ignore[arg-type]
                if key not in selected_keys:
                    continue
                field_meta = self.unique_key_to_field_meta[UniqueKey(key)]
                row[field_meta.unique_label] = field_meta.value_type.deserialize(value, field_meta)
            rows.append(row)

        return WorksheetTable(columns=self.get_output_parent_excel_headers(selected_keys), rows=rows)

    def _export_with_merged_header(
        self,
        records: list[dict[str, Any]] | None,
        selected_keys: list[UniqueKey],
        data_converter: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> WorksheetTable:
        data_df = self._generate_export_df(records, selected_keys, data_converter)
        return data_df.with_prepended_rows([self.get_output_child_excel_headers(selected_keys)])

    def _export_with_simple_header(
        self,
        records: list[dict[str, Any]] | None,
        selected_keys: list[UniqueKey],
        data_converter: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> WorksheetTable:
        return self._generate_export_df(records, selected_keys, data_converter)

    def _add_result_column(self):
        assert self._issue_tracker is not None
        self._issue_tracker.add_result_columns(
            self.df,
            result_unique_label=RESULT_COLUMN.unique_label,
            reason_unique_label=REASON_COLUMN.unique_label,
            extra_header_count_on_import=self.extra_header_count_on_import,
        )
        return self

    def _aggregate_data(self, row_data: dict[UniqueLabel, Any]) -> dict[Key, Any]:
        assert self._row_aggregator is not None
        return self._row_aggregator.aggregate(row_data)

    def _register_row_error(
        self,
        row_index: RowIndex,
        error: ExcelRowError | ExcelCellError | list[ExcelRowError | ExcelCellError] | list[ExcelCellError],
    ):
        assert self._issue_tracker is not None
        self._issue_tracker.register_row_error(row_index, error)

    def _register_cell_errors(self, row_index: RowIndex, errors: list[ExcelCellError]):
        assert self._issue_tracker is not None
        self._issue_tracker.register_cell_errors(row_index, errors, self.df)
        return self

    def _excel_has_merged_header(self) -> bool:
        return self._header_parser.has_merged_header(self.header_df)

    def _extract_header(self) -> list[ExcelHeader]:
        return self._header_parser.extract(self.header_df)

    def _extract_simple_header(self) -> list[ExcelHeader]:
        return self._header_parser._extract_simple(self.header_df)

    def _extract_merged_header(self) -> list[ExcelHeader]:
        return self._header_parser._extract_merged(self.header_df)

    def __setattr__(self, key: str, value: Any):
        if key == 'config' and hasattr(self, 'config'):
            raise ValueError(f'{self.__class__.__name__} 已经被实例化, config 不能被修改')
        object.__setattr__(self, key, value)

    def __repr__(self):
        return f'{self.__class__.__name__}(config={self.config!r})'
