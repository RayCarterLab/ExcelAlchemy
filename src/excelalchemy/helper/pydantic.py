from collections.abc import Sequence
from typing import Any, Generator, Iterable, TypeVar, cast

from pydantic import BaseModel, MissingError, NoneIsNotAllowedError, ValidationError
from pydantic.error_wrappers import ErrorList, ErrorWrapper
from pydantic.fields import ModelField, UndefinedType

from excelalchemy.const import ImporterCreateModelT, ImporterUpdateModelT
from excelalchemy.exc import ExcelCellError, ProgrammaticError
from excelalchemy.types.abstract import ABCValueType, ComplexABCValueType
from excelalchemy.types.field import FieldMetaInfo
from excelalchemy.types.identity import Key

ModelT = TypeVar('ModelT', bound=BaseModel)


def extract_pydantic_model(
    model: type[ImporterCreateModelT] | type[ImporterUpdateModelT] | type[BaseModel] | None,
) -> list[FieldMetaInfo]:
    """根据 Pydantic 模型提取 Excel 表头信息
    包含是否必填、值类型、注释等信息
    """
    if model is None:
        raise RuntimeError('模型不能为空')
    return list(_extract_pydantic_model(model))


def instantiate_pydantic_model(  # noqa: C901
    data: dict[Key, Any],
    model: type[ModelT],
) -> ModelT | list[ExcelCellError]:
    """实例化 Pydantic 模型, 并返回错误.

    若实例化成功, 则返回实例化后的模型, 错误信息为 None
    若实例化失败, 则模型返回 None, 错误信息为 ExcelImportError 列表
    若无法取得FieldMeta, 则raise ProgrammaticError
    """
    try:
        result: ModelT | list[ExcelCellError] = model.parse_obj(data)
    except ValidationError as wrapped_error:
        locations_and_errors = list(_flatten_errors(wrapped_error.raw_errors, None))

        if len(locations_and_errors) == 0:
            raise ProgrammaticError('empty ValidationError') from wrapped_error

        result = []

        for loc, e in locations_and_errors:
            attr_path = _validate_error_loc(loc)

            match attr_path:
                case (leaf,):
                    leaf_field_def = _validate_field_meta(model.__fields__[leaf])

                    _handle_error(result, e.exc, None, leaf_field_def)

                case (parent, leaf):
                    parent_field_def = _validate_field_meta(model.__fields__[parent])
                    leaf_field_def = _validate_field_meta(model.__fields__[parent].type_.__fields__[leaf])

                    _handle_error(result, e.exc, parent_field_def, leaf_field_def)

        if len(result) == 0:
            raise ProgrammaticError('实例化模型失败, 但错误信息为空') from wrapped_error

    return result


def _extract_pydantic_model(model: type[BaseModel]) -> Generator[FieldMetaInfo, None, None]:
    for model_field in model.__fields__.values():
        field_info = model_field.field_info
        if not isinstance(field_info, FieldMetaInfo):
            raise ProgrammaticError('字段定义必须是 FieldMeta 的实例')

        type_ = model_field.type_
        if issubclass(type_, ComplexABCValueType):
            for offset, (key, sub_field_info) in enumerate(type_.model_items()):
                sub_field_info = _complete_field_info(sub_field_info, model_field)
                sub_field_info.parent_label, sub_field_info.key, sub_field_info.offset = field_info.label, key, offset
                yield sub_field_info

        elif issubclass(type_, ABCValueType):
            field_info = _complete_field_info(field_info, model_field)
            yield field_info

        else:
            raise ProgrammaticError(f'字段定义必须是 ValueType 的子类, 或 ComplexValueType 的子类, 不支持 {type_}')


def _complete_field_info(field_info: FieldMetaInfo, field: ModelField) -> FieldMetaInfo:
    """补全 FieldMeta 信息"""
    if isinstance(field.required, UndefinedType):
        field_info.required = False
    else:
        field_info.required = field.required
    field_info.value_type = field.type_
    field_info.parent_label = field_info.label
    field_info.parent_key = Key(field.name)
    field_info.key = Key(field.name)
    field_info.offset = 0

    # 不同 ValueType 需要的不同信息, 需要及时补充
    original_field_info = cast(FieldMetaInfo, field.field_info)
    field_info.order = original_field_info.order

    field_info.character_set = field_info.character_set or original_field_info.character_set
    field_info.fraction_digits = field_info.fraction_digits or original_field_info.fraction_digits

    field_info.timezone = field_info.timezone or original_field_info.timezone
    field_info.date_format = field_info.date_format or original_field_info.date_format
    field_info.date_range_option = field_info.date_range_option or original_field_info.date_range_option

    field_info.unit = field_info.unit or original_field_info.unit

    return field_info


def _handle_error(
    error_container: list[ExcelCellError],
    exc: Exception,
    parent_field_def: FieldMetaInfo | None,
    leaf_field_def: FieldMetaInfo,
):
    match exc:
        case NoneIsNotAllowedError() | MissingError():
            error_container.append(
                ExcelCellError(
                    parent_label=parent_field_def and parent_field_def.label,  # type: ignore[arg-type]
                    label=leaf_field_def.label,
                    message='必填项缺失',
                )
            )
        case _:
            error_container.extend(
                [
                    ExcelCellError(
                        parent_label=parent_field_def and parent_field_def.label,  # type: ignore[arg-type]
                        label=leaf_field_def.label,
                        message=arg,
                    )
                    for arg in exc.args
                ]
            )


def _flatten_errors(
    error_list: Sequence[ErrorList],
    loc: tuple[str | int, ...] | None,
) -> Iterable[tuple[tuple[str | int, ...], ErrorWrapper]]:
    for error in error_list:
        if isinstance(error, ErrorWrapper):
            if loc:
                error_loc = loc + error.loc_tuple()
            else:
                error_loc = error.loc_tuple()

            if isinstance(error.exc, ValidationError):
                yield from _flatten_errors(error.exc.raw_errors, error_loc)
            else:
                yield error_loc, error

        else:
            yield from _flatten_errors(error, loc=loc)


def _validate_field_meta(raw_model_field: ModelField) -> FieldMetaInfo:
    field_info = raw_model_field.field_info
    if not isinstance(field_info, FieldMetaInfo):
        raise ProgrammaticError('field definition must be an instance of FieldMeta')

    return field_info


def _validate_error_loc(raw_loc: tuple[int | str, ...]) -> tuple[str] | tuple[str, str]:
    if len(raw_loc) > 2:
        raise ProgrammaticError('too deep nested fields (>2) from ill-formed model')

    for loc_node in raw_loc:
        if not isinstance(loc_node, str):
            raise ProgrammaticError('unsupported list element from ill-formed model')

    return cast(tuple[str] | tuple[str, str], raw_loc)
