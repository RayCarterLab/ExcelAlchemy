import itertools
import logging
from collections import defaultdict
from decimal import Decimal
from functools import cached_property
from itertools import chain
from os import PathLike
from typing import Any, Awaitable, Callable, Generator, Iterable, Type, cast

import pandas
from pandas import DataFrame, concat
from pydantic import BaseModel

from excelalchemy.const import (
    DEFAULT_FIELD_META_ORDER,
    REASON_COLUMN_KEY,
    REASON_COLUMN_LABEL,
    RESULT_COLUMN_KEY,
    RESULT_COLUMN_LABEL,
    ContextT,
    CreateModelT,
    ExporterModelT,
    ImporterCreateModelT,
    ImporterUpdateModelT,
    UpdateModelT,
)
from excelalchemy.core.abstract import ABCExcelAlchemy
from excelalchemy.core.writer import render_data_excel, render_merged_header_excel, render_simple_header_excel
from excelalchemy.exc import ConfigError, ExcelCellError, ExcelRowError
from excelalchemy.helper.pydantic import extract_pydantic_model, get_model_field_names, instantiate_pydantic_model
from excelalchemy.types.abstract import SystemReserved
from excelalchemy.types.alchemy import ExcelMode, ExporterConfig, ImporterConfig, ImportMode
from excelalchemy.types.field import FieldMetaInfo
from excelalchemy.types.header import ExcelHeader
from excelalchemy.types.identity import Base64Str, ColumnIndex, Key, Label, RowIndex, UniqueKey, UniqueLabel, UrlStr
from excelalchemy.types.result import ImportResult, ValidateHeaderResult, ValidateResult, ValidateRowResult
from excelalchemy.util.file import (
    flatten,
    read_file_from_minio_object,
    remove_excel_prefix,
    upload_file_from_minio_object,
)

HEADER_HINT_LINE_COUNT = 1  # HEADER_HINT 占用的行数

# 导入结果的字段元数据, 依据产品定义，占两列
# 1. 导入结果结果列
RESULT_COLUMN = FieldMetaInfo(label=RESULT_COLUMN_LABEL)
RESULT_COLUMN.parent_label = RESULT_COLUMN.label
RESULT_COLUMN.key = RESULT_COLUMN.parent_key = RESULT_COLUMN_KEY
RESULT_COLUMN.value_type = SystemReserved

# 2. 导入结果错误信息列
REASON_COLUMN = FieldMetaInfo(label=REASON_COLUMN_LABEL)
REASON_COLUMN.parent_label = REASON_COLUMN.label
REASON_COLUMN.key = REASON_COLUMN.parent_key = REASON_COLUMN_KEY
REASON_COLUMN.value_type = SystemReserved


class ExcelAlchemy(
    ABCExcelAlchemy[
        ContextT,
        ImporterCreateModelT,
        ImporterUpdateModelT,
        CreateModelT,
        UpdateModelT,
        ExporterModelT,
    ],
):
    def __init__(
        self,
        config: ImporterConfig[ContextT, ImporterCreateModelT, ImporterUpdateModelT] | ExporterConfig[ExporterModelT],
    ):
        self.df = DataFrame()  # 初始化一个空的DataFrame
        self.header_df = DataFrame()  # 初始化一个空的DataFrame
        self.config: (
            ImporterConfig[
                ContextT,
                ImporterCreateModelT,
                ImporterUpdateModelT,
            ]
            | ExporterConfig[ExporterModelT]
        ) = config
        # 每个单元格的错误, 用于标红单元格, 索引与 df 位置对应
        self.cell_errors: dict[RowIndex, dict[ColumnIndex, list[ExcelCellError]]] = {}
        # 行错误, 用于标记错误信息，单元格错误会在行错误中显示，行标索引与 df 位置对应
        self.row_errors: dict[RowIndex, list[ExcelRowError | ExcelCellError]] = defaultdict(list)
        # 固定的两列作为结果列
        self.import_result_field_meta: list[FieldMetaInfo] = [RESULT_COLUMN, REASON_COLUMN]
        self.import_result_label_to_field_meta: dict[UniqueLabel, FieldMetaInfo] = {  # 在导出验证结果时，补充结果列
            x.unique_label: x for x in self.import_result_field_meta
        }

        # 下列属性调用 __init_from_config__ 初始化
        self.field_metas: list[FieldMetaInfo] = []
        self.unique_label_to_field_meta: dict[UniqueLabel, FieldMetaInfo] = {}  # 唯一标签到字段元数据的映射
        self.parent_label_to_field_metas: dict[Label, list[FieldMetaInfo]] = {}  # 父标签到字段元数据的映射
        self.parent_key_to_field_metas: dict[Key, list[FieldMetaInfo]] = {}  # 父键到字段元数据的映射

        self.unique_key_to_field_meta: dict[UniqueKey, FieldMetaInfo] = {}  # 唯一键到字段元数据的映射
        self.ordered_field_meta: list[FieldMetaInfo] = []  # 排序后的表头

        # 业务端调用方法初始化·或者从配置文件初始化
        self.context: ContextT | None = None  # 转换器上下文
        self.__state_df_has_been_loaded__ = False  # df 是否已经被加载

        # 初始化·最后调用
        self.__init_from_config__()

    def __init_from_config__(self) -> None:
        """从配置类初始化"""
        self.context = getattr(self.config, 'context', None)
        importer_model = self.__get_importer_model__()
        self.__init_field_meta__(importer_model)

    def __init_field_meta__(self, importer_model: type[BaseModel]) -> None:
        """从配置类初始化"""
        self.field_metas = extract_pydantic_model(importer_model)
        self._check_field_meta_order(self.field_metas)
        if len(self.field_metas) == 0:
            raise ConfigError(f'没有从模型 {importer_model.__name__} 中提取到字段元数据，请检查模型是否定义了字段')
        self.ordered_field_meta: list[FieldMetaInfo] = self._sort_field_meta(self.field_metas)  # type: ignore[no-redef]

        for field_meta in self.ordered_field_meta:
            if field_meta.parent_label is None:
                raise ConfigError('父标签不能为空')
            if field_meta.parent_key is None:
                raise ConfigError('父键不能为空')

            self.parent_label_to_field_metas.setdefault(field_meta.parent_label, []).append(field_meta)
            self.parent_key_to_field_metas.setdefault(field_meta.parent_key, []).append(field_meta)
            self.unique_key_to_field_meta[field_meta.unique_key] = field_meta
            self.unique_label_to_field_meta[field_meta.unique_label] = field_meta

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

    @staticmethod
    def _check_field_meta_order(field_metas: list[FieldMetaInfo]) -> None:
        """检查字段顺序是否有重复"""
        order_to_field_meta: dict[int, set[Label]] = defaultdict(set)
        for field_meta in field_metas:
            assert field_meta.parent_label is not None  # only for mypy, remove this line at runtime if you want
            order_to_field_meta[field_meta.order].add(field_meta.parent_label)
        duplicate_order = [v for k, v in order_to_field_meta.items() if len(v) > 1 and k != DEFAULT_FIELD_META_ORDER]
        if duplicate_order:
            raise ConfigError(f'字段顺序定义有重复：{list(itertools.chain.from_iterable(duplicate_order))}')

    def download_template(self, sample_data: list[dict[str, Any]] | None = None) -> str:
        """下载导入模版"""
        if self.excel_mode != ExcelMode.IMPORT:
            raise ConfigError('只支持导入模式调用此方法')
        keys = self._select_output_excel_keys()
        has_merged_header = self.has_merged_header(keys)
        if has_merged_header:
            df = self._export_with_merged_header(sample_data, keys)
            return render_merged_header_excel(df, self.unique_label_to_field_meta)
        else:
            df = self._export_with_simple_header(sample_data, keys)
            return render_simple_header_excel(df, self.unique_label_to_field_meta)

    async def import_data(self, input_excel_name: str, output_excel_name: str) -> ImportResult:
        """导入数据"""
        assert isinstance(self.config, ImporterConfig)  # only for type check
        if self.excel_mode != ExcelMode.IMPORT:
            raise ConfigError('只支持导入模式调用此方法')

        validate_header = self._validate_header(input_excel_name)  # 验证表头
        if not validate_header.is_valid:
            return ImportResult.from_validate_header_result(validate_header)

        self.df = self.df.iloc[1:]  # 去掉表头
        self._set_columns(self.df)
        self.df = self.df.reset_index(drop=True)  # 重置索引

        all_success, success_count, fail_count = True, 0, 0
        for pandas_row_index, row in self.df.iloc[self.extra_header_count_on_import :].iterrows():
            aggregate_data = self._aggregate_data(cast(dict[UniqueLabel, Any], row.to_dict()))
            success = await self._dml_caller(cast(RowIndex, pandas_row_index), aggregate_data)
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
        """导出数据, keys 控制导出的列, 如果为 None, [] 则导出所有列"""
        df, has_merged_header = self._gen_export_df(data, keys)
        return render_data_excel(
            df,
            errors={},  # 数据导出没有错误
            field_meta_mapping=self.unique_label_to_field_meta,
            has_merged_header=has_merged_header,
        )

    def export_upload(self, output_name: str, data: list[dict[str, Any]], keys: list[Key] | None = None) -> UrlStr:
        """导出数据, keys 控制导出的列, 如果为 None, [] 则导出所有列"""

        content_with_prefix = self.export(data, keys)
        return self._upload_file(output_name, content_with_prefix)

    def add_context(self, context: ContextT) -> None:
        """添加转换模型上下文"""
        if self.context is not None:
            logging.warning('已经存在旧的转换模型上下文, 旧的上下文将被替换, 请确认此操作符合预期')

        self.context = context

    @cached_property
    def input_excel_has_merged_header(self) -> bool:
        """用户上传的 Excel 是否有合并的表头"""
        if not self.__state_df_has_been_loaded__:
            raise ConfigError('请保证 df 已经初始化')
        return self._excel_has_merged_header()

    @cached_property
    def input_excel_headers(self) -> list[ExcelHeader]:
        """用户上传的 Excel 表头"""
        if not self.__state_df_has_been_loaded__:
            raise ConfigError('请保证 df 已经初始化')
        return self._extract_header()

    @property
    def excel_mode(self) -> ExcelMode:
        if isinstance(self.config, ImporterConfig):
            return ExcelMode.IMPORT

        return ExcelMode.EXPORT

    @property
    def extra_header_count_on_import(self) -> int:
        # 执行导入时，预期额外的表头行数, 有合并单元格为 1, 无合并单元格为 0
        if self.excel_mode != ExcelMode.IMPORT:
            raise ConfigError('只支持导入模式读取此属性')
        for input_excel_label in self.input_excel_headers:
            if input_excel_label.label != input_excel_label.parent_label:
                return 1
        return 0

    @property
    def exporter_model(self) -> Type[ExporterModelT]:
        if isinstance(self.config, ImporterConfig):
            if self.config.create_importer_model and self.config.update_importer_model:
                raise ConfigError('从导入模型推断导出模型失败, 请手动设置导出模型')
            if self.config.create_importer_model:
                logging.info('从导入模型推断导出模型, 请确认此操作符合预期,使用的是 create_importer_model')
                return cast(Type[ExporterModelT], self.config.create_importer_model)
            if self.config.update_importer_model:
                logging.info('从导入模型推断导出模型, 请确认此操作符合预期,使用的是 update_importer_model')
                return cast(Type[ExporterModelT], self.config.update_importer_model)
            raise ConfigError('从导入模型推断导出模型失败, 请手动设置导出模型')

        return self.config.exporter_model

    def has_merged_header(self, selected_keys: list[UniqueKey]) -> bool:
        """检查导出的键是否有合并的表头"""
        for key in selected_keys:
            if self.unique_key_to_field_meta[key].label != self.unique_key_to_field_meta[key].parent_label:
                return True
        return False

    def get_output_parent_excel_headers(self, selected_keys: list[UniqueKey] | None = None) -> list[UniqueLabel]:
        """导出的 Excel 表头"""
        if not selected_keys:
            return [x.unique_label for x in self.ordered_field_meta]
        else:
            return [self.unique_key_to_field_meta[key].unique_label for key in selected_keys]

    def get_output_child_excel_headers(self, selected_keys: list[UniqueKey] | None = None) -> list[Label]:
        """导出的 Excel 表头"""
        if not selected_keys:
            return [x.label for x in self.ordered_field_meta]
        else:
            return [self.unique_key_to_field_meta[key].label for key in selected_keys]

    def _gen_export_df(self, data: list[dict[str, Any]], keys: list[Key] | None = None) -> tuple[DataFrame, bool]:
        """导出数据, keys 控制导出的列, 如果为 None, [] 则导出所有列"""
        if self.excel_mode == ExcelMode.IMPORT:
            logging.info('导出模式为导入模式, 调用导出方法时自动切换为导出模式')

        input_keys = keys or list(filter(None, [x.parent_key for x in self.ordered_field_meta]))
        model_keys = cast(list[Key], get_model_field_names(self.exporter_model))
        if unrecognized := (set(input_keys) - set(model_keys)):
            logging.warning('导出的列 {%s} 不在模型 {%s} 中', unrecognized, model_keys)

        intersection_keys = list(set(input_keys).intersection(set(model_keys)))
        selected_keys = self._select_output_excel_keys(intersection_keys)
        has_merged_header = self.has_merged_header(selected_keys)
        if has_merged_header:
            df = self._export_with_merged_header(data, selected_keys, self.config.data_converter)
        else:
            df = self._export_with_simple_header(data, selected_keys, self.config.data_converter)

        return df, has_merged_header

    def _validate_header(self, input_excel_name: str) -> ValidateHeaderResult:
        """验证表头"""
        if self.excel_mode != ExcelMode.IMPORT:
            raise ConfigError('只支持导入模式调用此方法')
        assert isinstance(self.config, ImporterConfig)  # only for type hint, not for runtime
        self._read_dataframe(input_excel_name)

        required_labels = [x.label for x in self.ordered_field_meta if x.required]
        primary_labels = [x.label for x in self.ordered_field_meta if x.is_primary_key]
        input_labels = [x.label for x in self.input_excel_headers]

        visited = set()
        duplicated = [x for x in input_labels if x in visited or visited.add(x)]  # type: ignore[func-returns-value]
        unrecognized = list(set(input_labels) - set(x.label for x in self.ordered_field_meta))

        missing_primary, missing_required = [], []
        if self.config.import_mode == ImportMode.UPDATE:
            missing_primary = list(set(primary_labels) - set(input_labels))

        missing_required = list(set(required_labels) - set(input_labels) - set(missing_primary))

        return ValidateHeaderResult(
            unrecognized=unrecognized,
            duplicated=duplicated,
            missing_required=missing_required,
            missing_primary=missing_primary,
            is_valid=not (missing_required or unrecognized or duplicated or missing_primary),
        )

    def _render_import_result_excel(self) -> str:
        """执行导入后，渲染数据"""
        content_with_prefix = render_data_excel(
            self.df,
            errors=self.cell_errors,
            field_meta_mapping=self.import_result_label_to_field_meta | self.unique_label_to_field_meta,
            has_merged_header=self.input_excel_has_merged_header,
        )

        return content_with_prefix

    def _upload_file(self, output_name: str, content_with_prefix: str) -> UrlStr:
        """上传文件"""
        assert isinstance(self.config, (ExporterConfig, ImporterConfig))  # only for type check
        if self.config.minio is None:
            raise ConfigError('未配置 minio')
        url = upload_file_from_minio_object(
            self.config.minio,
            self.config.bucket_name,
            output_name,
            remove_excel_prefix(content_with_prefix),
            self.config.url_expires,
        )
        return UrlStr(url)

    def _order_errors(self, errors: list[ExcelRowError | ExcelCellError]) -> Iterable[ExcelCellError | ExcelRowError]:
        """对错误进行排序,依据 ordered_field_meta 的 unique_label 索引排序，ExcelRowError 错误在最后"""
        unique_key_to_index = {field_meta.unique_label: idx for idx, field_meta in enumerate(self.ordered_field_meta)}
        row_errors: list[ExcelRowError] = []
        cell_errors: list[ExcelCellError] = []
        for error in errors:
            if isinstance(error, ExcelRowError):
                row_errors.append(error)
            else:
                cell_errors.append(error)
        cell_errors.sort(key=lambda x: unique_key_to_index.get(x.unique_label, Decimal('Infinity')))
        return chain(cell_errors, row_errors)

    def _set_columns(self, df: DataFrame) -> DataFrame:
        """设置列名"""
        columns = []
        for header in self.input_excel_headers:
            if header.unique_label not in self.get_output_parent_excel_headers():
                raise ConfigError(f'不支持的列名: {header.unique_label}')
            columns.append(header.unique_label)

        df.columns = columns  # type: ignore[assignment]
        return df

    def _select_output_excel_keys(self, keys: list[Key] | None = None) -> list[UniqueKey]:
        """选择出需要导出的键"""
        if not keys:
            # 如果没有指定, 则返回所有的 Key
            return [x.unique_key for x in self.ordered_field_meta]
        selected_field_meta = []
        for key in keys:
            if key in self.unique_key_to_field_meta:
                selected_field_meta.append(self.unique_key_to_field_meta[UniqueKey(key)])
            elif key in self.parent_key_to_field_metas:
                selected_field_meta.extend(self.parent_key_to_field_metas[key])
            else:
                raise ValueError(f'无效的 Key: {key}')
        return [x.unique_key for x in self._sort_field_meta(selected_field_meta)]

    @classmethod
    def _sort_field_meta(cls, field_metas: list[FieldMetaInfo]) -> list[FieldMetaInfo]:
        """排序 FieldMeta
        根据输入的顺序排序，其次根据 offset 排序
        """
        orders: dict[Label, int] = {}
        for idx, field_meta in enumerate(field_metas):
            assert field_meta.parent_label is not None  # only for type check, remove this line is safely at runtime
            if field_meta.order == DEFAULT_FIELD_META_ORDER:
                # 如果没有指定 order, 则使用 pydantic 输入的顺序, 但是 pydantic 不保证每次实例化的类顺序一致
                orders[field_meta.parent_label] = idx
            else:
                orders[field_meta.parent_label] = field_meta.order

        return sorted(
            field_metas,
            key=lambda x: (
                orders.get(cast(Label, x.parent_label), Decimal('Infinity')),
                x.offset,
            ),
        )

    def _read_dataframe(self, input_excel_name: str) -> pandas.DataFrame:
        """读取 DataFrame"""
        assert isinstance(self.config, ImporterConfig)  # only for type check
        if not self.__state_df_has_been_loaded__:
            if self.config.minio is None:
                raise ConfigError('未配置 minio')
            file_object = read_file_from_minio_object(
                self.config.minio,
                self.config.bucket_name,
                input_excel_name,
            )

            df: DataFrame = pandas.read_excel(
                cast(PathLike[str], file_object),  # cast to cheat type check
                sheet_name=self.config.sheet_name,
                skiprows=HEADER_HINT_LINE_COUNT,  # 跳过表头提示行
                header=None,  # 不使用表头, 由程序自行解析
                dtype=str,  # 读取所有数据为字符串
                engine='openpyxl',  # 使用 openpyxl 引擎, 避免 xlrd 引擎读取 xlsx 文件时报错
            )
            file_object.close()
            self.df = df
            self.header_df = df.head(2)  # 只读取前两行, 用于解析表头
            self.__state_df_has_been_loaded__ = True
        return self.df

    def _generate_export_df(
        self,
        records: list[dict[str, Any]] | None,
        selected_keys: list[UniqueKey],
        data_converter: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> DataFrame:
        """生成导出的 DataFrame"""
        rst = []
        if records is None:
            records = []
        for record in records:
            row = {}
            record = data_converter(record) if data_converter else record
            for key, value in flatten(record).items():  # type:ignore[arg-type]
                if key not in selected_keys:
                    continue
                field_meta = self.unique_key_to_field_meta[UniqueKey(key)]
                row[field_meta.unique_label] = field_meta.value_type.deserialize(value, field_meta)
            rst.append(row)

        return DataFrame(columns=self.get_output_parent_excel_headers(selected_keys), data=rst)

    def _export_with_merged_header(
        self,
        records: list[dict[str, Any]] | None,
        selected_keys: list[UniqueKey],
        data_converter: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> DataFrame:
        """导出有合并表头的数据"""
        data_df = self._generate_export_df(records, selected_keys, data_converter)
        # 含有合并的表头需要在起始位置插入一行
        new_row_df = DataFrame(columns=data_df.columns, data=[self.get_output_child_excel_headers(selected_keys)])
        result_df = concat([new_row_df, data_df], ignore_index=True)
        return result_df

    def _export_with_simple_header(
        self,
        records: list[dict[str, Any]] | None,
        selected_keys: list[UniqueKey],
        data_converter: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> DataFrame:
        """导出没有合并表头的数据"""
        return self._generate_export_df(records, selected_keys, data_converter)

    def _add_result_column(self):
        """写入导入结果列，失败原因列"""

        result: list[str] = []
        reason: list[str] = []

        # 遍历数据行, column 不算在 index 中
        for index in self.df.index[self.extra_header_count_on_import :]:
            row_errors = self.row_errors.get(index)
            if not row_errors:
                result.append(str(ValidateRowResult.SUCCESS))
                reason.append('')
            else:
                result.append(str(ValidateRowResult.FAIL))
                raw_reason = []
                for idx, error in enumerate(
                    self._order_errors(row_errors), start=1
                ):  # 给每个错误加上序号，方便用户查看，从1开始
                    raw_reason.append(f'{idx}、{str(error)}')
                reason.append('\n'.join(raw_reason))
        if self.extra_header_count_on_import == 1:  # 有合并表头
            result = [str(RESULT_COLUMN.unique_label)] + result
            reason = [str(REASON_COLUMN.unique_label)] + reason
        self.df.insert(loc=0, column=REASON_COLUMN.unique_label, value=reason)
        self.df.insert(loc=0, column=RESULT_COLUMN.unique_label, value=result)

        return self

    async def _dml_caller(self, row_index: RowIndex, data: dict[Key, Any]) -> bool:
        """调用 DML"""
        if not isinstance(self.config, ImporterConfig):
            raise TypeError('只有 ExcelImporterConfig 才支持 DML')

        is_success = False
        match self.config.import_mode:
            case ImportMode.CREATE:
                is_success = await self._creator_caller(row_index, data)
            case ImportMode.UPDATE:
                is_success = await self._updater_caller(row_index, data)
            case ImportMode.CREATE_OR_UPDATE:
                is_success = await self._creator_or_updater_caller(row_index, data)

        return is_success

    async def _creator_caller(self, row_index: RowIndex, data: dict[Key, Any]) -> bool:
        """调用创建函数, 返回是否创建成功"""
        if not isinstance(self.config, ImporterConfig):
            raise TypeError('只有 ExcelImporterConfig 才支持 DML')
        if self.config.creator is None:
            raise ConfigError('未配置 creator')
        if self.config.create_importer_model is None:
            raise ConfigError('未配置 create_importer_model')
        return await self.__caller_impl__(
            row_index,
            data,
            self.config.create_importer_model,
            self.config.creator,
            self.config.data_converter,
            self.config.exec_formatter,
        )

    async def _updater_caller(self, row_index: RowIndex, data: dict[Key, Any]) -> bool:
        """调用更新函数, 返回是否创建成功"""
        if not isinstance(self.config, ImporterConfig):
            raise TypeError(f'只有 {ImporterConfig.__name__} 才支持 DML')
        if self.config.updater is None:
            raise ConfigError('未配置 updater')
        if self.config.update_importer_model is None:
            raise ConfigError('未配置 update_importer_model')
        return await self.__caller_impl__(
            row_index,
            data,
            self.config.update_importer_model,
            self.config.updater,
            self.config.data_converter,
            self.config.exec_formatter,
        )

    async def __caller_impl__(
        self,
        row_index: RowIndex,
        data: dict[Key, Any],
        importer_model: type[BaseModel],
        dml_func: Callable[[dict[str, Any], ContextT | None], Awaitable[Any]],
        data_converter: Callable[[dict[str, Any]], dict[str, Any]] | None,
        exec_formatter: Callable[[Exception], str],
    ) -> bool:
        """调用 DML 函数"""
        # 第一步： 实例化 pydantic 模型，可能产生错误
        importer_instance_or_errors = instantiate_pydantic_model(data, importer_model)
        if not isinstance(importer_instance_or_errors, importer_model):
            errors: list[ExcelCellError] = importer_instance_or_errors  # type: ignore[assignment]
            self._register_row_error(row_index, errors)
            self._register_cell_errors(row_index, errors)
            return False

        # 第二步： 调用 creator/updater, 可能产生错误
        importer_instance = importer_instance_or_errors
        if data_converter is not None:
            converted_data = data_converter(importer_instance.model_dump(exclude_unset=True))
        else:
            converted_data = importer_instance.model_dump(exclude_unset=True)
        try:
            await dml_func(converted_data, self.context)
        except ExcelCellError as e:
            self.row_errors[row_index].append(e)
            return False
        except Exception as e:
            self.row_errors[row_index].append(ExcelRowError(exec_formatter(e)))
            return False

        return True

    async def _creator_or_updater_caller(self, row_index: RowIndex, data: dict[Key, Any]) -> bool:
        """调用 creator 或者 updater"""
        if not isinstance(self.config, ImporterConfig):
            raise TypeError(f'只有 {ImporterConfig.__name__} 才支持 DML')
        is_data_exists_func = self.config.is_data_exist
        if is_data_exists_func is None:
            raise ConfigError('未配置 is_data_exists')

        converted_data = self.config.data_converter(cast(dict[str, Any], data)) if self.config.data_converter else data
        is_data_exist = await is_data_exists_func(cast(dict[str, Any], converted_data), self.context)
        if is_data_exist:
            return await self._updater_caller(row_index, data)
        else:
            return await self._creator_caller(row_index, data)

    def _aggregate_data(self, row_data: dict[UniqueLabel, Any]) -> dict[Key, Any]:
        """聚合数据

        1、将复合类型的数据聚集到同一个 key 中
        2、将 Label 转换为 Key

        """
        agg_data: dict[Key, Any] = self.__agg_data__(row_data)
        serialized_agg_data: dict[Key, Any] = self.__serialize_agg_data__(agg_data)

        return serialized_agg_data

    def __agg_data__(self, row_data: dict[UniqueLabel, Any]) -> dict[Key, Any]:
        agg_data: dict[Key, Any] = {}
        for unique_label, value in row_data.items():
            field_meta = self.unique_label_to_field_meta[unique_label]

            if field_meta.key is None or field_meta.parent_key is None:
                raise ConfigError(f' {type(field_meta).__name__} 未配置 key/parent_key')

            if pandas.isna(value):
                if self.config.import_mode in {  # type: ignore[union-attr]
                    ImportMode.UPDATE,
                    ImportMode.CREATE_OR_UPDATE,
                }:
                    value = None  # 如果是更新模式，且值为 NaN，表示将该值设置为 None
                else:
                    continue

            if field_meta.parent_key == field_meta.key:
                agg_data[field_meta.key] = value
            else:
                agg_data.setdefault(field_meta.parent_key, {})
                agg_data[field_meta.parent_key][field_meta.key] = value
        return agg_data

    def __serialize_agg_data__(self, agg_data: dict[Key, Any]) -> dict[Key, Any]:
        serialized_agg_data: dict[Key, Any] = {}
        for parent_key, value in agg_data.items():
            field_metas = self.parent_key_to_field_metas[parent_key]
            validator = field_metas[0]
            if value is None:
                serialized_agg_data[parent_key] = None
            else:
                serialized_agg_data[parent_key] = validator.value_type.serialize(value, validator)

        return serialized_agg_data

    def _get_column_index(self, unique_label: UniqueLabel) -> Generator[ColumnIndex, None, None]:
        """获取列索引"""
        if unique_label not in self.unique_label_to_field_meta:
            if unique_label not in self.parent_label_to_field_metas:
                raise ValueError(f'找不到 {unique_label} 对应的字段')

            for sub_field_meta in self.parent_label_to_field_metas[unique_label]:
                yield from self.__get_column_index_impl__(sub_field_meta.unique_label)

        else:
            yield from self.__get_column_index_impl__(unique_label)

    def __get_column_index_impl__(self, unique_label: UniqueLabel) -> Generator[ColumnIndex, None, None]:
        index = self.df.columns.get_loc(unique_label)
        if isinstance(index, int):
            yield ColumnIndex(index)
        else:
            raise ValueError(f'找不到 {unique_label} 对应的列, 推测是 value_type 定义不正确')

    def _register_row_error(
        self,
        row_index: RowIndex,
        error: ExcelRowError | ExcelCellError | list[ExcelRowError | ExcelCellError] | list[ExcelCellError],
    ):
        """注册行错误"""
        if isinstance(error, list):
            self.row_errors[row_index].extend(error)
        else:
            self.row_errors[row_index].append(error)

    def _register_cell_errors(self, row_index: RowIndex, errors: list[ExcelCellError]):
        """注册单元格错误"""
        for error in errors:
            # +len(self.import_result_field_meta) 是因为在 df 中，会往最前面插入导入结果列，所以需要加上这个偏移量
            for index in self._get_column_index(error.unique_label):
                column_index = cast(ColumnIndex, index + len(self.import_result_field_meta))
                self.cell_errors.setdefault(row_index, {}).setdefault(column_index, []).append(error)
        return self

    def _excel_has_merged_header(self) -> bool:
        """判断是否有合并表头

        如果第 0 行有合并单元格，则一定有 nan 值或 Unnamed ，否则没有合并单元格
        """
        return any(pandas.isna(self.header_df.iloc[0])) or any(self.header_df.iloc[0].str.startswith('Unnamed'))

    def _extract_header(self) -> list[ExcelHeader]:
        """提取表头信息"""
        if self._excel_has_merged_header():
            return self._extract_merged_header()
        else:
            return self._extract_simple_header()

    def _extract_simple_header(self) -> list[ExcelHeader]:
        """提取简单表头信息"""
        return [ExcelHeader(label=Label(col), parent_label=Label(col)) for col in self.header_df.iloc[0].tolist()]

    def _extract_merged_header(self) -> list[ExcelHeader]:
        """提取含有合并表头的表头信息"""
        headers: list[ExcelHeader] = []
        header_row_index = 0

        last_header = None
        next_offset = 1
        for column_index, value in self.header_df.iloc[header_row_index].items():
            parent_value = value
            child_value = self.header_df.iloc[header_row_index + 1][column_index]  # type: ignore[call-overload]
            if pandas.isna(parent_value) or parent_value.startswith('Unnamed'):
                if pandas.isna(child_value):
                    raise ValueError('合并表头错误: 子表头不能为空')
                current_header = ExcelHeader(
                    label=Label(child_value),
                    parent_label=Label(last_header),
                    offset=next_offset,
                )
                next_offset += 1
            else:
                if pandas.isna(child_value):
                    child_value = parent_value
                current_header = ExcelHeader(label=Label(child_value), parent_label=Label(value))
                last_header, next_offset = value, 1
            headers.append(current_header)

        return headers

    def __setattr__(self, key: str, value: Any):
        if key == 'config' and hasattr(self, 'config'):
            raise ValueError(f'{self.__class__.__name__} 已经被实例化, config 不能被修改')
        object.__setattr__(self, key, value)

    def __repr__(self):
        return f'{self.__class__.__name__}(config={self.config!r})'
