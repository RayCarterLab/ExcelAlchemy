import re
from collections.abc import Generator, Iterable, Mapping
from dataclasses import dataclass
from types import UnionType
from typing import Union, cast, get_args, get_origin

from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from excelalchemy._primitives.identity import Key, Label
from excelalchemy.codecs.base import CompositeExcelFieldCodec, ExcelFieldCodec
from excelalchemy.exceptions import ExcelCellError, ExcelRowError, ProgrammaticError
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo, extract_declared_field_metadata

type ExcelValidationIssue = ExcelCellError | ExcelRowError
type ExcelValidationIssues = list[ExcelValidationIssue]

_MIN_ITEMS_PATTERN = re.compile(r'^Value should have at least (\d+) items after validation, not \d+$')
_MAX_ITEMS_PATTERN = re.compile(r'^Value should have at most (\d+) items after validation, not \d+$')


@dataclass(frozen=True)
class NormalizedValidationMessage:
    message: str
    message_key: MessageKey | None = None
    detail: Mapping[str, object] | None = None


def _build_cell_error(
    *,
    label: Label,
    normalized: NormalizedValidationMessage,
    parent_label: Label | None = None,
) -> ExcelCellError:
    error = ExcelCellError(
        label=label,
        parent_label=parent_label,
        message=normalized.message,
        message_key=normalized.message_key,
    )
    if normalized.detail:
        error.detail.update(normalized.detail)
    return error


def _build_row_error(normalized: NormalizedValidationMessage) -> ExcelRowError:
    error = ExcelRowError(
        normalized.message,
        message_key=normalized.message_key,
    )
    if normalized.detail:
        error.detail.update(normalized.detail)
    return error


def _normalize_validation_message(
    message: str,
    field_def: FieldMetaInfo | None = None,
    *,
    excel_codec: type[ExcelFieldCodec] | None = None,
) -> NormalizedValidationMessage:
    normalized = message.strip()
    if normalized == 'Field required':
        return NormalizedValidationMessage(msg(MessageKey.THIS_FIELD_IS_REQUIRED), MessageKey.THIS_FIELD_IS_REQUIRED)

    for prefix in ('Value error, ', 'Assertion failed, '):
        if normalized.startswith(prefix):
            normalized = normalized.removeprefix(prefix)
            break

    normalized_message = _normalize_constraint_message(normalized, field_def, excel_codec=excel_codec)
    if normalized_message is not None:
        return normalized_message

    if normalized == msg(MessageKey.INVALID_INPUT) and field_def is not None and excel_codec is not None:
        expected = excel_codec.expected_input_message(field_def)
        if expected is not None:
            return NormalizedValidationMessage(expected)

    if normalized and normalized[0].islower():
        normalized = normalized[0].upper() + normalized[1:]

    return NormalizedValidationMessage(normalized)


def _normalize_constraint_message(
    message: str,
    field_def: FieldMetaInfo | None,
    *,
    excel_codec: type[ExcelFieldCodec] | None = None,
) -> NormalizedValidationMessage | None:
    if field_def is None:
        return None

    constraints = field_def.constraints

    if (match := _MIN_ITEMS_PATTERN.match(message)) is not None:
        if constraints.min_length is not None:
            return NormalizedValidationMessage(
                msg(MessageKey.MIN_LENGTH_CHARACTERS, min_length=constraints.min_length),
                MessageKey.MIN_LENGTH_CHARACTERS,
                {'min_length': constraints.min_length},
            )
        min_items = int(match.group(1))
        return NormalizedValidationMessage(
            msg(MessageKey.MIN_ITEMS_REQUIRED, min_items=min_items),
            MessageKey.MIN_ITEMS_REQUIRED,
            {'min_items': min_items},
        )

    if (match := _MAX_ITEMS_PATTERN.match(message)) is not None:
        if constraints.max_length is not None:
            return NormalizedValidationMessage(
                msg(MessageKey.MAX_LENGTH_CHARACTERS, max_length=constraints.max_length),
                MessageKey.MAX_LENGTH_CHARACTERS,
                {'max_length': constraints.max_length},
            )
        max_items = int(match.group(1))
        return NormalizedValidationMessage(
            msg(MessageKey.MAX_ITEMS_ALLOWED, max_items=max_items),
            MessageKey.MAX_ITEMS_ALLOWED,
            {'max_items': max_items},
        )

    if message == 'Input should be a valid dictionary':
        if (
            excel_codec is not None
            and issubclass(excel_codec, CompositeExcelFieldCodec)
            and (expected := excel_codec.expected_input_message(field_def)) is not None
        ):
            return NormalizedValidationMessage(expected)
        return NormalizedValidationMessage(
            msg(MessageKey.ENTER_VALUE_EXPECTED_FORMAT), MessageKey.ENTER_VALUE_EXPECTED_FORMAT
        )

    return None


def _resolve_excel_codec_type(annotation: object) -> type[ExcelFieldCodec]:
    if isinstance(annotation, type):
        if issubclass(annotation, ExcelFieldCodec):
            return annotation
        unsupported = repr(cast(object, annotation))
    else:
        unsupported = str(annotation)
    raise ProgrammaticError(msg(MessageKey.VALUE_TYPE_DECLARATION_UNSUPPORTED, value_type=unsupported))


@dataclass(frozen=True)
class PydanticFieldAdapter:
    """Provide a stable view over one Pydantic field."""

    name: str
    raw_field: FieldInfo

    @property
    def annotation(self) -> object:
        return self.raw_field.annotation

    @property
    def excel_codec(self) -> type[ExcelFieldCodec]:
        annotation = self.annotation
        origin = get_origin(annotation)
        if origin in (UnionType, Union):
            args = [arg for arg in get_args(annotation) if arg is not type(None)]
            if len(args) != 1:
                raise ProgrammaticError(msg(MessageKey.UNSUPPORTED_FIELD_TYPE_DECLARATION, annotation=annotation))
            return _resolve_excel_codec_type(args[0])

        return _resolve_excel_codec_type(annotation)

    @property
    def value_type(self) -> type[ExcelFieldCodec]:
        """Backward-compatible alias for excel_codec."""
        return self.excel_codec

    @property
    def allows_none(self) -> bool:
        return any(arg is type(None) for arg in get_args(self.annotation))

    @property
    def required(self) -> bool:
        declared = self.declared_metadata
        declared_meta = declared.declared

        if declared_meta.effective_required is not None:
            return bool(declared_meta.effective_required)
        if declared_meta.is_primary_key or declared_meta.unique:
            return True
        if self.raw_field.default is not PydanticUndefined or self.raw_field.default_factory is not None:
            return False
        return not self.allows_none

    @property
    def declared_metadata(self) -> FieldMetaInfo:
        return extract_declared_field_metadata(self.raw_field)

    def runtime_metadata(self) -> FieldMetaInfo:
        declared = self.declared_metadata
        declared_meta = declared.declared
        return declared.bind_runtime(
            required=self.required,
            excel_codec=self.excel_codec,
            parent_label=declared_meta.label,
            parent_key=Key(self.name),
            key=Key(self.name),
            offset=0,
        )

    def validate_value(self, raw_value: object) -> object:
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
        raise ProgrammaticError(msg(MessageKey.MODEL_CANNOT_BE_NONE), message_key=MessageKey.MODEL_CANNOT_BE_NONE)
    return list(_extract_pydantic_model(PydanticModelAdapter(model)))


def get_model_field_names(model: type[BaseModel]) -> list[str]:
    return PydanticModelAdapter(model).field_names()


def instantiate_pydantic_model[ModelT: BaseModel](
    data: Mapping[str, object],
    model: type[ModelT],
) -> ModelT | ExcelValidationIssues:
    """Instantiate a Pydantic model and return mapped Excel errors when validation fails."""
    model_adapter = PydanticModelAdapter(model)
    normalized_data: dict[str, object] = {}
    errors: ExcelValidationIssues = []
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
            _handle_error(errors, exc, field_adapter.declared_metadata, excel_codec=field_adapter.excel_codec)

    model_instance_or_errors = _model_validate(normalized_data, model, model_adapter, failed_fields)
    if isinstance(model_instance_or_errors, list):
        return [*errors, *model_instance_or_errors]

    if errors:
        return errors

    return model_instance_or_errors


def _extract_pydantic_model(model: PydanticModelAdapter) -> Generator[FieldMetaInfo, None, None]:
    for field_adapter in model.fields():
        declared_metadata = field_adapter.declared_metadata
        declared_meta = declared_metadata.declared
        excel_codec = field_adapter.excel_codec

        if issubclass(excel_codec, CompositeExcelFieldCodec):
            for offset, (key, sub_field_info) in enumerate(excel_codec.column_items()):
                inherited = sub_field_info.inherited_from(declared_metadata)
                yield inherited.bind_runtime(
                    required=field_adapter.required,
                    excel_codec=excel_codec,
                    parent_label=declared_meta.label,
                    parent_key=Key(field_adapter.name),
                    key=key,
                    offset=offset,
                )
        else:
            yield field_adapter.runtime_metadata()


def _handle_error(
    error_container: ExcelValidationIssues,
    exc: Exception,
    field_def: FieldMetaInfo,
    *,
    excel_codec: type[ExcelFieldCodec] | None = None,
) -> None:
    raw_messages = [str(arg) for arg in exc.args if str(arg)] or [str(exc) or msg(MessageKey.INVALID_INPUT)]
    messages = [_normalize_validation_message(message, field_def, excel_codec=excel_codec) for message in raw_messages]
    error_container.extend(_build_cell_error(label=field_def.label, normalized=normalized) for normalized in messages)


def _model_validate[ModelT: BaseModel](
    data: dict[str, object],
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
    mapped: ExcelValidationIssues = []
    for error in exc.errors():
        loc = error.get('loc', ())
        if not loc:
            normalized = _normalize_validation_message(str(error['msg']))
            mapped.append(_build_row_error(normalized))
            continue

        field_name = loc[0]
        if not isinstance(field_name, str):
            normalized = _normalize_validation_message(str(error['msg']))
            mapped.append(_build_row_error(normalized))
            continue
        if field_name in failed_fields:
            continue

        field_adapter = model_adapter.field(field_name)
        normalized = _normalize_validation_message(
            str(error['msg']),
            field_adapter.declared_metadata,
            excel_codec=field_adapter.excel_codec,
        )
        if len(loc) > 1 and isinstance(loc[1], str):
            mapped.append(_nested_excel_error(field_adapter, loc[1], normalized))
            continue

        mapped.append(_build_cell_error(label=field_adapter.declared_metadata.declared.label, normalized=normalized))

    return mapped


def _nested_excel_error(
    field_adapter: PydanticFieldAdapter,
    child_key: str,
    normalized: NormalizedValidationMessage,
) -> ExcelCellError:
    declared_metadata = field_adapter.declared_metadata
    declared_meta = declared_metadata.declared
    excel_codec = field_adapter.excel_codec
    if issubclass(excel_codec, CompositeExcelFieldCodec):
        for key, sub_field_info in excel_codec.column_items():
            if key == child_key:
                return _build_cell_error(
                    label=sub_field_info.label, parent_label=declared_meta.label, normalized=normalized
                )

    return _build_cell_error(label=declared_meta.label, normalized=normalized)
