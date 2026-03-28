from collections.abc import Generator, Iterable, Mapping
from dataclasses import dataclass
from types import UnionType
from typing import Any, Union, cast, get_args, get_origin

from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from excelalchemy._primitives.identity import Key
from excelalchemy.codecs.base import CompositeExcelFieldCodec, ExcelFieldCodec
from excelalchemy.exceptions import ExcelCellError, ExcelRowError, ProgrammaticError
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo, extract_declared_field_metadata


@dataclass(frozen=True)
class PydanticFieldAdapter:
    """Provide a stable view over one Pydantic field."""

    name: str
    raw_field: FieldInfo

    @property
    def annotation(self) -> Any:
        return self.raw_field.annotation

    @property
    def excel_codec(self) -> type[Any]:
        annotation = self.annotation
        origin = get_origin(annotation)
        if origin in (UnionType, Union):
            args = [arg for arg in get_args(annotation) if arg is not type(None)]
            if len(args) != 1:
                raise ProgrammaticError(msg(MessageKey.UNSUPPORTED_FIELD_TYPE_DECLARATION, annotation=annotation))
            return cast(type[Any], args[0])

        return cast(type[Any], annotation)

    @property
    def value_type(self) -> type[Any]:
        """Backward-compatible alias for excel_codec."""
        return self.excel_codec

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
        return not self.allows_none

    @property
    def declared_metadata(self) -> FieldMetaInfo:
        return extract_declared_field_metadata(self.raw_field)

    def runtime_metadata(self) -> FieldMetaInfo:
        declared = self.declared_metadata
        return declared.bind_runtime(
            required=self.required,
            excel_codec=cast(type[ExcelFieldCodec], self.excel_codec),
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

        return self.excel_codec.normalize_import_value(raw_value, self.declared_metadata)


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
    """Extract Excel field metadata from a Pydantic model declaration."""
    if model is None:
        raise RuntimeError(msg(MessageKey.MODEL_CANNOT_BE_NONE))
    return list(_extract_pydantic_model(PydanticModelAdapter(model)))


def get_model_field_names(model: type[BaseModel]) -> list[str]:
    return PydanticModelAdapter(model).field_names()


def instantiate_pydantic_model[ModelT: BaseModel](
    data: Mapping[str, Any],
    model: type[ModelT],
) -> ModelT | list[ExcelCellError | ExcelRowError]:
    """Instantiate a Pydantic model and return mapped Excel errors when validation fails."""
    model_adapter = PydanticModelAdapter(model)
    normalized_data: dict[str, Any] = {}
    errors: list[ExcelCellError | ExcelRowError] = []
    failed_fields: set[str] = set()

    for field_adapter in model_adapter.fields():
        raw_value = data.get(field_adapter.name, PydanticUndefined)
        if raw_value is PydanticUndefined:
            continue

        try:
            normalized_data[field_adapter.name] = field_adapter.validate_value(raw_value)
        except ProgrammaticError:
            raise
        except Exception as exc:
            failed_fields.add(field_adapter.name)
            _handle_error(errors, exc, field_adapter.declared_metadata)

    model_instance_or_errors = _model_validate(normalized_data, model, model_adapter, failed_fields)
    if isinstance(model_instance_or_errors, list):
        return [*errors, *model_instance_or_errors]

    if errors:
        return errors

    return model_instance_or_errors


def _extract_pydantic_model(model: PydanticModelAdapter) -> Generator[FieldMetaInfo, None, None]:
    for field_adapter in model.fields():
        declared_metadata = field_adapter.declared_metadata
        excel_codec = field_adapter.excel_codec

        if issubclass(excel_codec, CompositeExcelFieldCodec):
            for offset, (key, sub_field_info) in enumerate(excel_codec.column_items()):
                inherited = sub_field_info.inherited_from(declared_metadata)
                yield inherited.bind_runtime(
                    required=field_adapter.required,
                    excel_codec=cast(type[ExcelFieldCodec], excel_codec),
                    parent_label=declared_metadata.label,
                    parent_key=Key(field_adapter.name),
                    key=key,
                    offset=offset,
                )

        elif issubclass(excel_codec, ExcelFieldCodec):
            yield field_adapter.runtime_metadata()

        else:
            raise ProgrammaticError(
                msg(MessageKey.VALUE_TYPE_DECLARATION_UNSUPPORTED, value_type=excel_codec)
            )


def _handle_error(
    error_container: list[ExcelCellError | ExcelRowError],
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


def _model_validate[ModelT: BaseModel](
    data: dict[str, Any],
    model: type[ModelT],
    model_adapter: PydanticModelAdapter,
    failed_fields: set[str],
) -> ModelT | list[ExcelCellError | ExcelRowError]:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        return _map_validation_error(exc, model_adapter, failed_fields)


def _map_validation_error(
    exc: ValidationError,
    model_adapter: PydanticModelAdapter,
    failed_fields: set[str],
) -> list[ExcelCellError | ExcelRowError]:
    mapped: list[ExcelCellError | ExcelRowError] = []
    for error in exc.errors():
        loc = error.get('loc', ())
        if not loc:
            mapped.append(ExcelRowError(str(error['msg'])))
            continue

        field_name = loc[0]
        if not isinstance(field_name, str):
            mapped.append(ExcelRowError(str(error['msg'])))
            continue
        if field_name in failed_fields:
            continue

        field_adapter = model_adapter.field(field_name)
        message = str(error['msg'])
        if len(loc) > 1 and isinstance(loc[1], str):
            mapped.append(_nested_excel_error(field_adapter, loc[1], message))
            continue

        mapped.append(ExcelCellError(label=field_adapter.declared_metadata.label, message=message))

    return mapped


def _nested_excel_error(
    field_adapter: PydanticFieldAdapter,
    child_key: str,
    message: str,
) -> ExcelCellError:
    declared_metadata = field_adapter.declared_metadata
    excel_codec = field_adapter.excel_codec
    if issubclass(excel_codec, CompositeExcelFieldCodec):
        for key, sub_field_info in excel_codec.column_items():
            if key == child_key:
                return ExcelCellError(
                    label=sub_field_info.label,
                    parent_label=declared_metadata.label,
                    message=message,
                )

    return ExcelCellError(label=declared_metadata.label, message=message)
