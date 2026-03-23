from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Generator, Iterable, TypeVar, cast

from pydantic import BaseModel, MissingError, NoneIsNotAllowedError, ValidationError
from pydantic.error_wrappers import ErrorList, ErrorWrapper
from pydantic.fields import ModelField, UndefinedType

from excelalchemy.const import ImporterCreateModelT, ImporterUpdateModelT
from excelalchemy.exc import ExcelCellError, ProgrammaticError
from excelalchemy.types.abstract import ABCValueType, ComplexABCValueType
from excelalchemy.types.field import FieldMetaInfo, extract_declared_field_metadata
from excelalchemy.types.identity import Key

ModelT = TypeVar('ModelT', bound=BaseModel)


@dataclass(frozen=True)
class PydanticFieldAdapter:
    raw_field: ModelField

    @property
    def name(self) -> str:
        return self.raw_field.name

    @property
    def value_type(self) -> type[Any]:
        return self.raw_field.type_

    @property
    def required(self) -> bool:
        if isinstance(self.raw_field.required, UndefinedType):
            return False
        return bool(self.raw_field.required)

    @property
    def declared_metadata(self) -> FieldMetaInfo:
        return extract_declared_field_metadata(self.raw_field.field_info)

    def runtime_metadata(self) -> FieldMetaInfo:
        declared = self.declared_metadata
        return declared.bind_runtime(
            required=self.required,
            value_type=cast(type[ABCValueType], self.value_type),
            parent_label=declared.label,
            parent_key=Key(self.name),
            key=Key(self.name),
            offset=0,
        )


@dataclass(frozen=True)
    class PydanticModelAdapter:
    model: type[BaseModel]

    def fields(self) -> Iterable[PydanticFieldAdapter]:
        return (PydanticFieldAdapter(field) for field in self.model.__fields__.values())

    def field(self, name: str) -> PydanticFieldAdapter:
        return PydanticFieldAdapter(self.model.__fields__[name])

    def field_names(self) -> list[str]:
        return list(self.model.__fields__.keys())


def extract_pydantic_model(
    model: type[ImporterCreateModelT] | type[ImporterUpdateModelT] | type[BaseModel] | None,
) -> list[FieldMetaInfo]:
    """根据 Pydantic 模型提取 Excel 表头信息."""
    if model is None:
        raise RuntimeError('模型不能为空')
    return list(_extract_pydantic_model(PydanticModelAdapter(model)))


def get_model_field_names(model: type[BaseModel]) -> list[str]:
    return PydanticModelAdapter(model).field_names()


def instantiate_pydantic_model(  # noqa: C901
    data: dict[Key, Any],
    model: type[ModelT],
) -> ModelT | list[ExcelCellError]:
    """实例化 Pydantic 模型, 并返回错误."""
    model_adapter = PydanticModelAdapter(model)
    try:
        result: ModelT | list[ExcelCellError] = model.parse_obj(data)
    except ValidationError as wrapped_error:
        locations_and_errors = list(_flatten_errors(wrapped_error.raw_errors, None))

        if len(locations_and_errors) == 0:
            raise ProgrammaticError('empty ValidationError') from wrapped_error

        result = []

        for loc, error_wrapper in locations_and_errors:
            attr_path = _validate_error_loc(loc)

            match attr_path:
                case (leaf,):
                    leaf_field_def = model_adapter.field(leaf).declared_metadata
                    _handle_error(result, error_wrapper.exc, None, leaf_field_def)

                case (parent, leaf):
                    parent_field = model_adapter.field(parent)
                    parent_field_def = parent_field.declared_metadata
                    nested_model = cast(type[BaseModel], parent_field.value_type)
                    leaf_field_def = PydanticModelAdapter(nested_model).field(leaf).declared_metadata
                    _handle_error(result, error_wrapper.exc, parent_field_def, leaf_field_def)

        if len(result) == 0:
            raise ProgrammaticError('实例化模型失败, 但错误信息为空') from wrapped_error

    return result


def _extract_pydantic_model(model: PydanticModelAdapter) -> Generator[FieldMetaInfo, None, None]:
    for field_adapter in model.fields():
        declared_metadata = field_adapter.declared_metadata
        value_type = field_adapter.value_type

        if issubclass(value_type, ComplexABCValueType):
            for offset, (key, sub_field_info) in enumerate(value_type.model_items()):
                inherited = sub_field_info.inherited_from(declared_metadata)
                yield inherited.bind_runtime(
                    required=field_adapter.required,
                    value_type=cast(type[ABCValueType], value_type),
                    parent_label=declared_metadata.label,
                    parent_key=Key(field_adapter.name),
                    key=key,
                    offset=offset,
                )

        elif issubclass(value_type, ABCValueType):
            yield field_adapter.runtime_metadata()

        else:
            raise ProgrammaticError(f'字段定义必须是 ValueType 的子类, 或 ComplexValueType 的子类, 不支持 {value_type}')


def _handle_error(
    error_container: list[ExcelCellError],
    exc: Exception,
    parent_field_def: FieldMetaInfo | None,
    leaf_field_def: FieldMetaInfo,
) -> None:
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


def _validate_error_loc(raw_loc: tuple[int | str, ...]) -> tuple[str] | tuple[str, str]:
    if len(raw_loc) > 2:
        raise ProgrammaticError('too deep nested fields (>2) from ill-formed model')

    for loc_node in raw_loc:
        if not isinstance(loc_node, str):
            raise ProgrammaticError('unsupported list element from ill-formed model')

    return cast(tuple[str] | tuple[str, str], raw_loc)
