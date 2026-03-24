"""Excel metadata definitions decoupled from Pydantic internals."""

import copy
import datetime
import logging
from functools import cached_property
from typing import AbstractSet, Any, Callable

from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo, PydanticUndefined

from excelalchemy.const import (
    DATA_RANGE_OPTION_TO_CHINESE,
    DATE_FORMAT_TO_HINT_MAPPING,
    DATE_FORMAT_TO_PYTHON_MAPPING,
    DEFAULT_FIELD_META_ORDER,
    MAX_OPTIONS_COUNT,
    MULTI_CHECKBOX_SEPARATOR,
    UNIQUE_HEADER_CONNECTOR,
    CharacterSet,
    DataRangeOption,
    DateFormat,
    IntStr,
    Option,
)
from excelalchemy.exc import ConfigError, ProgrammaticError
from excelalchemy.types.abstract import ABCValueType, Undefined
from excelalchemy.types.identity import Key, Label, OptionId, UniqueKey, UniqueLabel

EXCEL_FIELD_METADATA_KEY = 'excelalchemy_metadata'


class PatchFieldMeta(BaseModel):
    unique: bool | None = False  # 当前列是否唯一，不用于校验，用于渲染 Excel 表头的注释
    is_primary_key: bool | None = False  # 当前列是否为主键，不用于校验，用于渲染 Excel 表头的注释
    hint: str | None = None  # 当前列的提示信息，不用于校验，用于渲染 Excel 表头的注释
    options: list[Option] | None = None


class FieldMetaInfo:
    """Excel field metadata independent from any validation backend."""

    def __init__(
        self,
        *,
        label: str | Label,
        is_primary_key: bool = False,
        unique: bool = False,
        ignore_import: bool = False,
        required: bool | None = None,
        order: int = DEFAULT_FIELD_META_ORDER,
        character_set: set[CharacterSet] | None = None,
        fraction_digits: int | None = None,
        timezone: datetime.timezone | None = None,
        date_format: DateFormat | None = None,
        date_range_option: DataRangeOption | None = None,
        options: list[Option] | None = None,
        unit: str | None = None,
        hint: str | None = None,
        ge: float | None = None,
        le: float | None = None,
        max_digits: int | None = None,
        decimal_places: int | None = None,
        min_items: int | None = None,
        max_items: int | None = None,
        unique_items: bool | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
    ) -> None:
        self.label = Label(label)
        self.is_primary_key = is_primary_key
        self.parent_label: Label | None = None

        self.key: Key | None = None
        self.parent_key: Key | None = None

        self.offset = DEFAULT_FIELD_META_ORDER
        self.value_type: type[ABCValueType] = Undefined
        self.unique = unique or is_primary_key

        self.required = required
        self.ignore_import = ignore_import
        self.order = order

        self.character_set = character_set or set(CharacterSet)
        self.fraction_digits = fraction_digits
        self.timezone = timezone or datetime.timezone(datetime.timedelta(hours=8), 'CST')
        self.date_format = date_format
        self.date_range_option = date_range_option
        self.options = options
        self.unit = unit
        self.hint = hint

        self.importer_ge = ge
        self.importer_le = le
        self.importer_max_digits = max_digits
        self.importer_decimal_places = decimal_places
        self.importer_min_length = min_length
        self.importer_max_length = max_length
        self.importer_min_items = min_items
        self.importer_max_items = max_items
        self.importer_unique_items = unique_items

    def clone(self) -> 'FieldMetaInfo':
        return copy.copy(self)

    def inherited_from(self, parent: 'FieldMetaInfo') -> 'FieldMetaInfo':
        runtime = self.clone()
        runtime.order = parent.order
        runtime.character_set = runtime.character_set or parent.character_set
        runtime.fraction_digits = runtime.fraction_digits or parent.fraction_digits
        runtime.timezone = runtime.timezone or parent.timezone
        runtime.date_format = runtime.date_format or parent.date_format
        runtime.date_range_option = runtime.date_range_option or parent.date_range_option
        runtime.unit = runtime.unit or parent.unit
        return runtime

    def bind_runtime(
        self,
        *,
        required: bool,
        value_type: type[ABCValueType],
        parent_label: Label,
        parent_key: Key,
        key: Key,
        offset: int,
    ) -> 'FieldMetaInfo':
        runtime = self.clone()
        runtime.required = required
        runtime.value_type = value_type
        runtime.parent_label = parent_label
        runtime.parent_key = parent_key
        runtime.key = key
        runtime.offset = offset
        return runtime

    def set_is_primary_key(self, is_primary_key: bool | None) -> None:
        if is_primary_key is None:
            return
        self.is_primary_key = is_primary_key
        if self.is_primary_key:
            self.unique = True
            self.required = True

    def set_unique(self, unique: bool | None) -> None:
        if unique is None:
            return
        self.unique = unique
        if self.unique:
            self.required = True

    def validate_state(self) -> None:
        if self.is_primary_key and not self.unique:
            raise ValueError('主键必须唯一')
        if (self.is_primary_key or self.unique) and self.required is False:
            raise ValueError('主键或唯一字段必须必填')

    def exchange_option_ids_to_names(self, option_ids: list[str] | list[OptionId]) -> list[str]:
        option_names: list[str] = []

        for option_id in option_ids:
            option_id = OptionId(option_id)
            try:
                option_names.append(self.options_id_map[option_id].name)
            except KeyError:
                logging.warning('找不到选项id %s，将返回原值', option_id)
                option_names.append(option_id)

        return option_names

    def exchange_names_to_option_ids_with_errors(self, names: list[str]) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        result: list[str] = []
        for name in names:
            option = self.options_name_map.get(name)
            if option is None:
                errors.append('选项不存在，请参照表头的注释填写')
            else:
                result.append(option.id)
        return result, errors

    @property
    def unique_label(self) -> UniqueLabel:
        if self.parent_label is None:
            raise RuntimeError('运行时 parent_label 不能为空')
        label = (
            f'{self.parent_label}{UNIQUE_HEADER_CONNECTOR}{self.label}'
            if self.parent_label != self.label
            else self.label
        )
        return UniqueLabel(label)

    @property
    def unique_key(self) -> UniqueKey:
        if self.parent_key is None:
            raise RuntimeError('运行时 parent_key 不能为空')
        if self.key is None:
            raise RuntimeError('运行时 key 不能为空')
        key = f'{self.parent_key}{UNIQUE_HEADER_CONNECTOR}{self.key}' if self.parent_key != self.key else self.key
        return UniqueKey(key)

    @cached_property
    def options_id_map(self) -> dict[OptionId, Option]:
        if self.options is None:
            return {}
        if len(self.options) > MAX_OPTIONS_COUNT:
            logging.warning(
                '您为字段【%s】指定了 %s 个选项, 请考虑此数量是否合理，options 设计的本意不是为了处理大量数据',
                self.label,
                len(self.options),
            )
        return {option.id: option for option in self.options}

    @cached_property
    def options_name_map(self) -> dict[str, Option]:
        if self.options is None:
            return {}
        if len(self.options) > MAX_OPTIONS_COUNT:
            logging.warning(
                '您为字段【%s】指定了 %s 个选项, 请考虑此数量是否合理，options 设计的本意不是为了处理大量数据',
                self.label,
                len(self.options),
            )
        return {option.name: option for option in self.options}

    @property
    def comment_required(self) -> str:
        return f"必填性：{'必填' if self.required else '选填'}"

    @property
    def comment_date_format(self) -> str:
        if self.date_format is None:
            return ''
        return f'格式：日期（{DATE_FORMAT_TO_HINT_MAPPING[self.date_format]}）'

    @property
    def comment_date_range_option(self) -> str:
        if self.date_range_option is None:
            return '范围：无限制'
        return f'范围：{DATA_RANGE_OPTION_TO_CHINESE[self.date_range_option]}'

    @property
    def comment_hint(self) -> str:
        if self.hint is None:
            return ''
        return f'提示：{self.hint}'

    @property
    def comment_options(self) -> str:
        if self.options is None:
            return ''
        return f'选项：{MULTI_CHECKBOX_SEPARATOR.join(x.name for x in self.options)}'

    @property
    def comment_fraction_digits(self) -> str:
        return f'小数位数：{self.fraction_digits or 0}'

    @property
    def comment_unit(self) -> str:
        return f'单位：{self.unit or "无"}'

    @property
    def comment_unique(self) -> str:
        return f"唯一性：{'唯一' if self.unique else '非唯一'}"

    @property
    def comment_max_length(self) -> str:
        return f'最大长度：{self.importer_max_length or "无限制"}'

    @property
    def must_date_format(self) -> DateFormat:
        if self.date_format is None:
            raise ConfigError('运行时 date_format 不能为空')
        return self.date_format

    @property
    def python_date_format(self) -> str:
        return DATE_FORMAT_TO_PYTHON_MAPPING[self.must_date_format]

    def __repr__(self) -> str:
        return (
            f'FieldMeta(label={self.label!r}, '
            f'order={self.order!r}, '
            f'value_type={self.value_type.__name__!r}, '
            f'required={self.required!r}, '
            f'unique={self.unique!r}, '
            f'comment_required={self.comment_required!r}, '
            f'comment_unique={self.comment_unique!r})'
        )

    __str__ = __repr__


def extract_declared_field_metadata(field_info: FieldInfo) -> FieldMetaInfo:
    metadata = (field_info.json_schema_extra or {}).get(EXCEL_FIELD_METADATA_KEY)
    if not isinstance(metadata, FieldMetaInfo):
        raise ProgrammaticError('字段定义必须是 FieldMeta 的实例')
    return metadata


# pylint: disable=invalid-name
# pylint: disable=too-many-locals
def FieldMeta(
    default: Any = PydanticUndefined,
    *,
    label: str,
    is_primary_key: bool = False,
    unique: bool = False,
    ignore_import: bool = False,
    required: bool | None = None,
    order: int = DEFAULT_FIELD_META_ORDER,
    character_set: set[CharacterSet] | None = None,
    fraction_digits: int | None = None,
    timezone: datetime.timezone | None = None,
    date_format: DateFormat | None = None,
    date_range_option: DataRangeOption | None = None,
    options: list[Option] | None = None,
    unit: str | None = None,
    hint: str | None = None,
    default_factory: Callable[[], Any] | None = None,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    exclude: AbstractSet[IntStr] | Any = None,
    include: AbstractSet[IntStr] | Any = None,
    const: bool | None = None,
    ge: float | None = None,
    le: float | None = None,
    multiple_of: float | None = None,
    allow_inf_nan: bool | None = None,
    max_digits: int | None = None,
    decimal_places: int | None = None,
    min_items: int | None = None,
    max_items: int | None = None,
    unique_items: bool | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    allow_mutation: bool | None = True,
    regex: str | None = None,
    discriminator: str | None = None,
    repr: bool = True,
    **extra: Any,
) -> Any:
    if fraction_digits is not None and not isinstance(fraction_digits, int):
        raise ValueError('fraction_digits 必须是整数')

    metadata = FieldMetaInfo(
        label=label,
        is_primary_key=is_primary_key,
        unique=unique,
        ignore_import=ignore_import,
        required=required,
        order=order,
        character_set=character_set,
        fraction_digits=fraction_digits,
        timezone=timezone,
        date_format=date_format,
        date_range_option=date_range_option,
        options=options,
        unit=unit,
        hint=hint,
        ge=ge,
        le=le,
        max_digits=max_digits,
        decimal_places=decimal_places,
        min_items=min_items,
        max_items=max_items,
        unique_items=unique_items,
        min_length=min_length,
        max_length=max_length,
    )

    json_schema_extra = {EXCEL_FIELD_METADATA_KEY: metadata} | extra
    if include is not None:
        json_schema_extra['include'] = include
    if const is not None:
        json_schema_extra['const'] = const
    if min_items is not None:
        json_schema_extra['min_items'] = min_items
    if max_items is not None:
        json_schema_extra['max_items'] = max_items
    if unique_items is not None:
        json_schema_extra['unique_items'] = unique_items

    field_kwargs: dict[str, Any] = {
        'repr': repr,
        'json_schema_extra': json_schema_extra,
    }
    if default_factory is not None:
        field_kwargs['default_factory'] = default_factory
    if alias is not None:
        field_kwargs['alias'] = alias
    if title is not None:
        field_kwargs['title'] = title
    if description is not None:
        field_kwargs['description'] = description
    if isinstance(exclude, bool):
        field_kwargs['exclude'] = exclude
    if ge is not None:
        field_kwargs['ge'] = ge
    if le is not None:
        field_kwargs['le'] = le
    if multiple_of is not None:
        field_kwargs['multiple_of'] = multiple_of
    if allow_inf_nan is not None:
        field_kwargs['allow_inf_nan'] = allow_inf_nan
    if max_digits is not None:
        field_kwargs['max_digits'] = max_digits
    if decimal_places is not None:
        field_kwargs['decimal_places'] = decimal_places
    if min_length is not None:
        field_kwargs['min_length'] = min_length
    if max_length is not None:
        field_kwargs['max_length'] = max_length
    if regex is not None:
        field_kwargs['pattern'] = regex
    if discriminator is not None:
        field_kwargs['discriminator'] = discriminator
    if allow_mutation is not None and allow_mutation is not True:
        field_kwargs['frozen'] = not allow_mutation

    return Field(default, **field_kwargs)
