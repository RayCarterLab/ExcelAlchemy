import logging
from collections.abc import Sequence
from typing import cast

from pydantic import BaseModel

from excelalchemy._primitives.constants import (
    REASON_COLUMN_KEY,
    RESULT_COLUMN_KEY,
)
from excelalchemy._primitives.header_models import ExcelHeader
from excelalchemy._primitives.identity import ColumnIndex, DataUrlStr, Label, RowIndex, UniqueKey, UniqueLabel, UrlStr
from excelalchemy._primitives.payloads import DataConverter, ExportRowPayload
from excelalchemy.artifacts import ExcelArtifact
from excelalchemy.codecs.base import SystemReserved
from excelalchemy.config import ExcelMode, ExporterConfig, ImporterConfig, ImportMode
from excelalchemy.core.abstract import ABCExcelAlchemy
from excelalchemy.core.headers import ExcelHeaderParser, ExcelHeaderValidator
from excelalchemy.core.import_session import ImportSession, ImportSessionSnapshot, build_import_result_field_meta
from excelalchemy.core.rendering import ExcelRenderer
from excelalchemy.core.schema import ExcelSchemaLayout
from excelalchemy.core.storage import build_storage_gateway
from excelalchemy.core.storage_protocol import ExcelStorage
from excelalchemy.core.table import WorksheetTable
from excelalchemy.exceptions import ConfigError, ExcelCellError, ExcelRowError
from excelalchemy.helper.pydantic import get_model_field_names
from excelalchemy.i18n.messages import MessageKey, use_display_locale
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.i18n.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo
from excelalchemy.results import ImportResult
from excelalchemy.util.file import flatten

HEADER_HINT_LINE_COUNT = 1

RESULT_COLUMN = FieldMetaInfo(label=dmsg(MessageKey.RESULT_COLUMN_LABEL, locale='zh-CN'))
RESULT_COLUMN.parent_label = RESULT_COLUMN.label
RESULT_COLUMN.key = RESULT_COLUMN.parent_key = RESULT_COLUMN_KEY
RESULT_COLUMN.excel_codec = SystemReserved

REASON_COLUMN = FieldMetaInfo(label=dmsg(MessageKey.REASON_COLUMN_LABEL, locale='zh-CN'))
REASON_COLUMN.parent_label = REASON_COLUMN.label
REASON_COLUMN.key = REASON_COLUMN.parent_key = REASON_COLUMN_KEY
REASON_COLUMN.excel_codec = SystemReserved


class ExcelAlchemy[
    ContextT,
    ImportCreateModelT: BaseModel,
    ImportUpdateModelT: BaseModel,
    ExportModelT: BaseModel,
](
    ABCExcelAlchemy[
        ContextT,
        ImportCreateModelT,
        ImportUpdateModelT,
        ExportModelT,
    ]
):
    def __init__(
        self,
        config: ImporterConfig[ContextT, ImportCreateModelT, ImportUpdateModelT] | ExporterConfig[ExportModelT],
    ):
        runtime_config = cast(object, config)
        if not isinstance(runtime_config, (ImporterConfig, ExporterConfig)):
            raise ConfigError(msg(MessageKey.EXPORT_MODE_CONFIG_REQUIRED, config_name=ExporterConfig.__name__))
        self.config = config
        self.locale = config.schema_options.locale
        self._context: ContextT | None = getattr(config.behavior, 'context', None)
        self._last_import_session: ImportSession[ContextT, ImportCreateModelT, ImportUpdateModelT] | None = None

        self.import_result_field_meta = build_import_result_field_meta(locale=self.locale)
        self.import_result_label_to_field_meta = {
            field_meta.unique_label: field_meta for field_meta in self.import_result_field_meta
        }

        self._header_parser = ExcelHeaderParser()
        self._header_validator = ExcelHeaderValidator()
        self._renderer = ExcelRenderer()
        self._storage_gateway: ExcelStorage = build_storage_gateway(config)
        self._layout: ExcelSchemaLayout

        self.__init_from_config__()

    def __init_from_config__(self) -> None:
        model = self.__get_importer_model__()
        with use_display_locale(self.locale):
            self._layout = ExcelSchemaLayout.from_model(model)
        self.__sync_layout_state__()

    def __sync_layout_state__(self) -> None:
        self.field_metas = self._layout.field_metas
        self.unique_label_to_field_meta = self._layout.unique_label_to_field_meta
        self.parent_label_to_field_metas = self._layout.parent_label_to_field_metas
        self.parent_key_to_field_metas = self._layout.parent_key_to_field_metas
        self.unique_key_to_field_meta = self._layout.unique_key_to_field_meta
        self.ordered_field_meta = self._layout.ordered_field_meta

    def __get_importer_model__(self) -> type[ImportCreateModelT] | type[ImportUpdateModelT] | type[ExportModelT]:
        importer_model: type[ImportCreateModelT] | type[ImportUpdateModelT] | type[ExportModelT] | None = None
        if self.excel_mode == ExcelMode.IMPORT:
            if not isinstance(self.config, ImporterConfig):
                raise ConfigError(msg(MessageKey.IMPORT_MODE_CONFIG_REQUIRED, config_name=ImporterConfig.__name__))
            if self.config.behavior.import_mode in (ImportMode.CREATE, ImportMode.CREATE_OR_UPDATE):
                importer_model = self.config.schema_options.create_importer_model
            elif self.config.behavior.import_mode == ImportMode.UPDATE:
                importer_model = self.config.schema_options.update_importer_model
        elif self.excel_mode == ExcelMode.EXPORT:
            if not isinstance(self.config, ExporterConfig):
                raise ConfigError(msg(MessageKey.EXPORT_MODE_CONFIG_REQUIRED, config_name=ExporterConfig.__name__))
            importer_model = self.config.schema_options.exporter_model

        if importer_model is None:
            raise ConfigError(msg(MessageKey.NO_IMPORTER_OR_EXPORTER_MODEL_CONFIGURED))
        return importer_model

    def download_template(self, sample_data: list[ExportRowPayload] | None = None) -> DataUrlStr:
        if self.excel_mode != ExcelMode.IMPORT:
            raise ConfigError(msg(MessageKey.IMPORT_MODE_ONLY_METHOD))

        with use_display_locale(self.locale):
            keys = self._select_output_excel_keys()
            has_merged_header = self.has_merged_header(keys)
            if has_merged_header:
                worksheet_table = self._export_with_merged_header(sample_data, keys)
            else:
                worksheet_table = self._export_with_simple_header(sample_data, keys)
            return self._renderer.render_template(
                worksheet_table,
                self.unique_label_to_field_meta,
                has_merged_header=has_merged_header,
            )

    def download_template_artifact(
        self,
        sample_data: list[ExportRowPayload] | None = None,
        *,
        filename: str = 'template.xlsx',
    ) -> ExcelArtifact:
        return ExcelArtifact.from_data_url(self.download_template(sample_data), filename=filename)

    async def import_data(self, input_excel_name: str, output_excel_name: str) -> ImportResult:
        assert isinstance(self.config, ImporterConfig)
        if self.excel_mode != ExcelMode.IMPORT:
            raise ConfigError(msg(MessageKey.IMPORT_MODE_ONLY_METHOD))

        session = self._new_import_session()
        self._last_import_session = session
        return await session.run(input_excel_name, output_excel_name)

    def export(self, data: list[ExportRowPayload], keys: Sequence[str] | None = None) -> DataUrlStr:
        with use_display_locale(self.locale):
            worksheet_table, has_merged_header = self._gen_export_df(data, keys)
            return self._renderer.render_data(
                worksheet_table,
                field_meta_mapping=self.unique_label_to_field_meta,
                has_merged_header=has_merged_header,
                errors={},
            )

    def export_artifact(
        self,
        data: list[ExportRowPayload],
        keys: Sequence[str] | None = None,
        *,
        filename: str = 'export.xlsx',
    ) -> ExcelArtifact:
        return ExcelArtifact.from_data_url(self.export(data, keys), filename=filename)

    def export_upload(
        self, output_name: str, data: list[ExportRowPayload], keys: Sequence[str] | None = None
    ) -> UrlStr:
        return self._upload_file(output_name, self.export(data, keys))

    def add_context(self, context: ContextT) -> None:
        if self._context is not None:
            logging.warning('An existing conversion context is being replaced')
        self._context = context
        if self._last_import_session is not None:
            self._last_import_session.context = context

    @property
    def context(self) -> ContextT | None:
        return self._context

    @property
    def df(self) -> WorksheetTable:
        """Backward-compatible alias for worksheet_table."""
        if self._last_import_session is None:
            return WorksheetTable()
        return self._last_import_session.worksheet_table

    @property
    def worksheet_table(self) -> WorksheetTable:
        if self._last_import_session is None:
            return WorksheetTable()
        return self._last_import_session.worksheet_table

    @property
    def header_df(self) -> WorksheetTable:
        """Backward-compatible alias for header_table."""
        if self._last_import_session is None:
            return WorksheetTable()
        return self._last_import_session.header_table

    @property
    def header_table(self) -> WorksheetTable:
        if self._last_import_session is None:
            return WorksheetTable()
        return self._last_import_session.header_table

    @property
    def cell_error_map(self) -> dict[RowIndex, dict[ColumnIndex, list[ExcelCellError]]]:
        if self._last_import_session is None:
            return {}
        return self._last_import_session.cell_error_map

    @property
    def row_error_map(self) -> dict[RowIndex, list[ExcelRowError | ExcelCellError]]:
        if self._last_import_session is None:
            return {}
        return self._last_import_session.row_error_map

    @property
    def cell_errors(self) -> dict[RowIndex, dict[ColumnIndex, list[ExcelCellError]]]:
        """Backward-compatible alias for cell_error_map."""
        return self.cell_error_map

    @property
    def row_errors(self) -> dict[RowIndex, list[ExcelRowError | ExcelCellError]]:
        """Backward-compatible alias for row_error_map."""
        return self.row_error_map

    @property
    def last_import_snapshot(self) -> ImportSessionSnapshot | None:
        if self._last_import_session is None:
            return None
        return self._last_import_session.snapshot

    @property
    def input_excel_has_merged_header(self) -> bool:
        return self._require_last_import_session().input_excel_has_merged_header

    @property
    def input_excel_headers(self) -> list[ExcelHeader]:
        return self._require_last_import_session().input_excel_headers

    @property
    def excel_mode(self) -> ExcelMode:
        if isinstance(self.config, ImporterConfig):
            return ExcelMode.IMPORT
        return ExcelMode.EXPORT

    @property
    def extra_header_count_on_import(self) -> int:
        if self.excel_mode != ExcelMode.IMPORT:
            raise ConfigError(msg(MessageKey.IMPORT_MODE_ONLY_PROPERTY))
        return self._require_last_import_session().extra_header_count_on_import

    @property
    def exporter_model(self) -> type[ExportModelT]:
        if isinstance(self.config, ImporterConfig):
            if self.config.schema_options.create_importer_model and self.config.schema_options.update_importer_model:
                raise ConfigError(msg(MessageKey.EXPORTER_MODEL_INFERENCE_CONFLICT))
            if self.config.schema_options.create_importer_model:
                logging.info('Inferring exporter_model from create_importer_model')
                return cast(type[ExportModelT], self.config.schema_options.create_importer_model)
            if self.config.schema_options.update_importer_model:
                logging.info('Inferring exporter_model from update_importer_model')
                return cast(type[ExportModelT], self.config.schema_options.update_importer_model)
            raise ConfigError(msg(MessageKey.EXPORTER_MODEL_CANNOT_BE_INFERRED))

        return self.config.schema_options.exporter_model

    def has_merged_header(self, selected_keys: list[UniqueKey]) -> bool:
        return self._layout.has_merged_header(selected_keys)

    def get_output_parent_excel_headers(self, selected_keys: list[UniqueKey] | None = None) -> list[UniqueLabel]:
        return self._layout.get_output_parent_excel_headers(selected_keys)

    def get_output_child_excel_headers(self, selected_keys: list[UniqueKey] | None = None) -> list[Label]:
        return self._layout.get_output_child_excel_headers(selected_keys)

    def _gen_export_df(
        self, data: list[ExportRowPayload], keys: Sequence[str] | None = None
    ) -> tuple[WorksheetTable, bool]:
        if self.excel_mode == ExcelMode.IMPORT:
            logging.info('Export requested while configured in import mode; continuing with exporter_model inference')

        input_keys = (
            list(keys)
            if keys is not None
            else [
                str(field_meta.parent_key)
                for field_meta in self.ordered_field_meta
                if field_meta.parent_key is not None
            ]
        )
        model_keys = get_model_field_names(self.exporter_model)
        if unrecognized := (set(input_keys) - set(model_keys)):
            logging.warning(
                'Ignoring keys not present in the exporter model: %s (model keys: %s)', unrecognized, model_keys
            )

        selected_keys = self._select_output_excel_keys(list(set(input_keys).intersection(set(model_keys))))
        has_merged_header = self.has_merged_header(selected_keys)
        if has_merged_header:
            worksheet_table = self._export_with_merged_header(data, selected_keys, self.config.behavior.data_converter)
        else:
            worksheet_table = self._export_with_simple_header(
                data,
                selected_keys,
                self.config.behavior.data_converter,
            )
        return worksheet_table, has_merged_header

    def _select_output_excel_keys(self, keys: Sequence[str] | None = None) -> list[UniqueKey]:
        return self._layout.select_output_excel_keys(keys)

    def _generate_export_df(
        self,
        records: list[ExportRowPayload] | None,
        selected_keys: list[UniqueKey],
        data_converter: DataConverter | None = None,
    ) -> WorksheetTable:
        rows: list[dict[UniqueLabel, object]] = []
        records = records or []
        for record in records:
            row: dict[UniqueLabel, object] = {}
            record = data_converter(record) if data_converter else record
            for key, value in flatten(record).items():
                if key not in selected_keys:
                    continue
                field_meta = self.unique_key_to_field_meta[UniqueKey(key)]
                row[field_meta.unique_label] = field_meta.excel_codec.format_display_value(value, field_meta)
            rows.append(row)

        return WorksheetTable(columns=self.get_output_parent_excel_headers(selected_keys), rows=rows)

    def _export_with_merged_header(
        self,
        records: list[ExportRowPayload] | None,
        selected_keys: list[UniqueKey],
        data_converter: DataConverter | None = None,
    ) -> WorksheetTable:
        data_df = self._generate_export_df(records, selected_keys, data_converter)
        return data_df.with_prepended_rows([self.get_output_child_excel_headers(selected_keys)])

    def _export_with_simple_header(
        self,
        records: list[ExportRowPayload] | None,
        selected_keys: list[UniqueKey],
        data_converter: DataConverter | None = None,
    ) -> WorksheetTable:
        return self._generate_export_df(records, selected_keys, data_converter)

    def _new_import_session(self) -> ImportSession[ContextT, ImportCreateModelT, ImportUpdateModelT]:
        assert isinstance(self.config, ImporterConfig)
        return ImportSession(
            config=self.config,
            layout=self._layout,
            storage_gateway=self._storage_gateway,
            header_parser=self._header_parser,
            header_validator=self._header_validator,
            renderer=self._renderer,
            import_result_field_meta=self.import_result_field_meta,
            import_result_label_to_field_meta=self.import_result_label_to_field_meta,
            locale=self.locale,
            context=self._context,
        )

    def _require_last_import_session(self) -> ImportSession[ContextT, ImportCreateModelT, ImportUpdateModelT]:
        if self._last_import_session is None:
            raise ConfigError(msg(MessageKey.WORKSHEET_TABLE_NOT_LOADED))
        return self._last_import_session

    def _upload_file(self, output_name: str, content_with_prefix: DataUrlStr) -> UrlStr:
        return self._storage_gateway.upload_excel(output_name, content_with_prefix)

    def __setattr__(self, key: str, value: object):
        if key == 'config' and hasattr(self, 'config'):
            raise ValueError(msg(MessageKey.CONFIG_ALREADY_INITIALIZED, class_name=self.__class__.__name__))
        object.__setattr__(self, key, value)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(config={self.config!r})'
