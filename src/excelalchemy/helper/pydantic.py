from dataclasses import dataclass
from types import UnionType
from typing import Any, Generator, Iterable, cast, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo, PydanticUndefined

from excelalchemy.exc import ExcelCellError, ProgrammaticError
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import message as msg
from excelalchemy.types.abstract import ABCValueType, ComplexABCValueType
from excelalchemy.types.field import FieldMetaInfo, extract_declared_field_metadata
from excelalchemy.types.identity import Key


@dataclass(frozen=True)
class PydanticFieldAdapter:
    """Provide a stable view over one Pydantic field."""

    name: str
    raw_field: FieldInfo

    @property
    def annotation(self) -> Any:
        return self.raw_field.annotation

    @property
    def value_type(self) -> type[Any]:
        annotation = self.annotation
        origin = get_origin(annotation)
        if origin in (UnionType, getattr(__import__('typing'), 'Union')):
            args = [arg for arg in get_args(annotation) if arg is not type(None)]
            if len(args) != 1:
                raise ProgrammaticError(msg(MessageKey.UNSUPPORTED_FIELD_TYPE_DECLARATION, annotation=annotation))
            return cast(type[Any], args[0])

        return cast(type[Any], annotation)

    @property
    def allows_none(self) -> bool:
        return any(arg is type(None) for arg in get_args(self.annotation))

    @property
    def required(self) -> bool:
        declared = self.declared_metadata

        if declared.is_primary_key or declared.unique:
            return True
        if declared.required is not None:
            return declared.required
        if self.raw_field.default is not PydanticUndefined or self.raw_field.default_factory is not None:
            return False
        if self.allows_none:
            return False
        return True

    @property
    def declared_metadata(self) -> FieldMetaInfo:
        return extract_declared_field_metadata(self.raw_field)

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

    def validate_value(self, raw_value: Any) -> Any:
        if raw_value is None:
            if self.allows_none and not self.required:
                return None
            raise ValueError(msg(MessageKey.THIS_FIELD_IS_REQUIRED))

        return self.value_type.__validate__(raw_value, self.declared_metadata)


@dataclass(frozen=True)
class PydanticModelAdapter:
    """Expose a small, version-friendly API over a Pydantic model class."""

    model: type[BaseModel]

    def fields(self) -> Iterable[PydanticFieldAdapter]:
        return (
            PydanticFieldAdapter(name=name, raw_field=field_info)
            for name, field_info in self.model.model_fields.items()
        )

    def field(self, name: str) -> PydanticFieldAdapter:
        return PydanticFieldAdapter(name=name, raw_field=self.model.model_fields[name])

    def field_names(self) -> list[str]:
        return list(self.model.model_fields.keys())


def extract_pydantic_model(
    model: type[BaseModel] | None,
) -> list[FieldMetaInfo]:
    """根据 Pydantic 模型提取 Excel 表头信息."""
    if model is None:
        raise RuntimeError(msg(MessageKey.MODEL_CANNOT_BE_NONE))
    return list(_extract_pydantic_model(PydanticModelAdapter(model)))


def get_model_field_names(model: type[BaseModel]) -> list[str]:
    return PydanticModelAdapter(model).field_names()


def instantiate_pydantic_model[ModelT: BaseModel](  # noqa: C901
    data: dict[Key, Any],
    model: type[ModelT],
) -> ModelT | list[ExcelCellError]:
    """实例化 Pydantic 模型, 并返回错误."""
    model_adapter = PydanticModelAdapter(model)
    validated_data: dict[str, Any] = {}
    errors: list[ExcelCellError] = []

    for field_adapter in model_adapter.fields():
        raw_value = data.get(Key(field_adapter.name), PydanticUndefined)
        if raw_value is PydanticUndefined:
            if field_adapter.required:
                errors.append(
                    ExcelCellError(
                        label=field_adapter.declared_metadata.label,
                        message=msg(MessageKey.THIS_FIELD_IS_REQUIRED),
                    )
                )
            continue

        try:
            validated_data[field_adapter.name] = field_adapter.validate_value(raw_value)
        except ProgrammaticError:
            raise
        except Exception as exc:
            _handle_error(errors, exc, field_adapter.declared_metadata)

    if errors:
        return errors

    return cast(
        ModelT,
        model.model_construct(
            _fields_set=set(validated_data.keys()),
            **validated_data,
        ),
    )


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
            raise ProgrammaticError(
                msg(MessageKey.VALUE_TYPE_DECLARATION_UNSUPPORTED, value_type=value_type)
            )


def _handle_error(
    error_container: list[ExcelCellError],
    exc: Exception,
    field_def: FieldMetaInfo,
) -> None:
    messages = [str(arg) for arg in exc.args if str(arg)] or [str(exc) or msg(MessageKey.INVALID_INPUT)]
    error_container.extend(
        ExcelCellError(
            label=field_def.label,
            message=message,
        )
        for message in messages
    )
