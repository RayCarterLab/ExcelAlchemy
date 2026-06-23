import re
from collections.abc import Generator, Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import UnionType
from typing import Any, Union, cast, get_args, get_origin

from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from excelalchemy.adapters.pydantic_fields import extract_declared_field_metadata
from excelalchemy.codecs.field_codec import CompositeExcelFieldCodec, ExcelFieldCodec, UnspecifiedFieldCodec
from excelalchemy.errors import ExcelCellError, ExcelRowError, ProgrammaticError
from excelalchemy.field_metadata import FieldMetaInfo
from excelalchemy.messages import MessageKey, UserMessage
from excelalchemy.messages import display_message as dmsg
from excelalchemy.messages import message as msg
from excelalchemy.messages import user_message as umsg
from excelalchemy.primitives.identity import Key, Label

type ExcelValidationIssue = ExcelCellError | ExcelRowError
type ExcelValidationIssues = list[ExcelValidationIssue]


@dataclass(frozen=True, slots=True)
class ValidationMessageNormalizationPolicy:
    """Rules used to map Pydantic validation text into Excel-facing messages."""

    required_message: str = 'Field required'
    stripped_prefixes: tuple[str, ...] = ('Value error, ', 'Assertion failed, ')
    min_items_pattern: str = r'^Value should have at least (\d+) items after validation, not \d+$'
    max_items_pattern: str = r'^Value should have at most (\d+) items after validation, not \d+$'
    min_length_pattern: str = r'^String should have at least (\d+) characters$'
    max_length_pattern: str = r'^String should have at most (\d+) characters$'
    valid_dictionary_message: str = 'Input should be a valid dictionary'
    capitalize_unmapped_lowercase: bool = True


VALIDATION_MESSAGE_NORMALIZATION_POLICY = ValidationMessageNormalizationPolicy()

_MIN_ITEMS_PATTERN = re.compile(VALIDATION_MESSAGE_NORMALIZATION_POLICY.min_items_pattern)
_MAX_ITEMS_PATTERN = re.compile(VALIDATION_MESSAGE_NORMALIZATION_POLICY.max_items_pattern)
_MIN_LENGTH_PATTERN = re.compile(VALIDATION_MESSAGE_NORMALIZATION_POLICY.min_length_pattern)
_MAX_LENGTH_PATTERN = re.compile(VALIDATION_MESSAGE_NORMALIZATION_POLICY.max_length_pattern)


@dataclass(frozen=True)
class NormalizedValidationMessage:
    message: str
    message_key: MessageKey | None = None
    detail: Mapping[str, object] | None = None
    display_message: str | None = None

    @classmethod
    def from_key(cls, key: MessageKey, **detail: object) -> 'NormalizedValidationMessage':
        return cls(msg(key, **cast(Any, detail)), key, detail or None, dmsg(key, **cast(Any, detail)))

    @classmethod
    def from_user_message(cls, message: UserMessage) -> 'NormalizedValidationMessage':
        return cls(
            str(message),
            message.message_key,
            None,
            message.display(),
        )


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
        display_message=normalized.display_message,
    )
    if normalized.detail:
        error.detail.update(normalized.detail)
    return error


def _build_row_error(normalized: NormalizedValidationMessage) -> ExcelRowError:
    error = ExcelRowError(
        normalized.message,
        message_key=normalized.message_key,
        display_message=normalized.display_message,
    )
    if normalized.detail:
        error.detail.update(normalized.detail)
    return error


def _normalize_validation_message(
    message: object,
    field_def: FieldMetaInfo | None = None,
    *,
    excel_codec: type[ExcelFieldCodec] | None = None,
) -> NormalizedValidationMessage:
    if isinstance(message, UserMessage):
        if message.message_key == MessageKey.INVALID_INPUT and field_def is not None and excel_codec is not None:
            expected = excel_codec.expected_input_message(field_def)
            if expected is not None:
                return _normalize_validation_message(expected, field_def, excel_codec=excel_codec)
        return NormalizedValidationMessage.from_user_message(message)

    normalized = str(message).strip()
    if normalized == VALIDATION_MESSAGE_NORMALIZATION_POLICY.required_message:
        return NormalizedValidationMessage.from_key(MessageKey.THIS_FIELD_IS_REQUIRED)

    for prefix in VALIDATION_MESSAGE_NORMALIZATION_POLICY.stripped_prefixes:
        if normalized.startswith(prefix):
            normalized = normalized.removeprefix(prefix)
            break

    normalized_message = _normalize_constraint_message(normalized, field_def, excel_codec=excel_codec)
    if normalized_message is not None:
        return normalized_message

    if normalized == msg(MessageKey.INVALID_INPUT) and field_def is not None and excel_codec is not None:
        expected = excel_codec.expected_input_message(field_def)
        if expected is not None:
            return _normalize_validation_message(expected, field_def, excel_codec=excel_codec)

    if VALIDATION_MESSAGE_NORMALIZATION_POLICY.capitalize_unmapped_lowercase and normalized and normalized[0].islower():
        normalized = normalized[0].upper() + normalized[1:]

    return NormalizedValidationMessage(normalized)


def _normalize_pydantic_error(
    error: Mapping[str, object],
    field_def: FieldMetaInfo | None = None,
    *,
    excel_codec: type[ExcelFieldCodec] | None = None,
) -> NormalizedValidationMessage:
    normalized_message = _normalize_constraint_error(error, field_def, excel_codec=excel_codec)
    if normalized_message is not None:
        return normalized_message
    return _normalize_validation_message(error.get('msg', ''), field_def, excel_codec=excel_codec)


def _normalize_constraint_error(
    error: Mapping[str, object],
    field_def: FieldMetaInfo | None,
    *,
    excel_codec: type[ExcelFieldCodec] | None = None,
) -> NormalizedValidationMessage | None:
    if field_def is None:
        return None

    error_type = error.get('type')
    ctx = error.get('ctx')
    if not isinstance(ctx, Mapping):
        return None

    ctx = cast(Mapping[object, object], ctx)
    field_type = ctx.get('field_type')
    constraints = field_def.constraints
    if error_type == 'too_short' and field_type == 'List':
        min_items = _int_from_context(ctx, 'min_length') or constraints.min_items
        if min_items is not None:
            return NormalizedValidationMessage.from_key(MessageKey.MIN_ITEMS_REQUIRED, min_items=min_items)

    if error_type == 'too_long' and field_type == 'List':
        max_items = _int_from_context(ctx, 'max_length') or constraints.max_items
        if max_items is not None:
            return NormalizedValidationMessage.from_key(MessageKey.MAX_ITEMS_ALLOWED, max_items=max_items)

    if error_type == 'string_too_short':
        min_length = _int_from_context(ctx, 'min_length') or constraints.min_length
        if min_length is not None:
            return NormalizedValidationMessage.from_key(MessageKey.MIN_LENGTH_CHARACTERS, min_length=min_length)

    if error_type == 'string_too_long':
        max_length = _int_from_context(ctx, 'max_length') or constraints.max_length
        if max_length is not None:
            return NormalizedValidationMessage.from_key(MessageKey.MAX_LENGTH_CHARACTERS, max_length=max_length)

    return _normalize_constraint_message(str(error.get('msg', '')), field_def, excel_codec=excel_codec)


def _int_from_context(ctx: Mapping[object, object], key: str) -> int | None:
    value = ctx.get(key)
    if isinstance(value, int):
        return value
    return None


def _normalize_constraint_message(
    message: str,
    field_def: FieldMetaInfo | None,
    *,
    excel_codec: type[ExcelFieldCodec] | None = None,
) -> NormalizedValidationMessage | None:
    if field_def is None:
        return None

    constraints = field_def.constraints

    if (match := _MIN_LENGTH_PATTERN.match(message)) is not None:
        min_length = constraints.min_length or int(match.group(1))
        return NormalizedValidationMessage.from_key(MessageKey.MIN_LENGTH_CHARACTERS, min_length=min_length)

    if (match := _MAX_LENGTH_PATTERN.match(message)) is not None:
        max_length = constraints.max_length or int(match.group(1))
        return NormalizedValidationMessage.from_key(MessageKey.MAX_LENGTH_CHARACTERS, max_length=max_length)

    if (match := _MIN_ITEMS_PATTERN.match(message)) is not None:
        if constraints.min_length is not None:
            return NormalizedValidationMessage.from_key(
                MessageKey.MIN_LENGTH_CHARACTERS,
                min_length=constraints.min_length,
            )
        min_items = int(match.group(1))
        return NormalizedValidationMessage.from_key(MessageKey.MIN_ITEMS_REQUIRED, min_items=min_items)

    if (match := _MAX_ITEMS_PATTERN.match(message)) is not None:
        if constraints.max_length is not None:
            return NormalizedValidationMessage.from_key(
                MessageKey.MAX_LENGTH_CHARACTERS,
                max_length=constraints.max_length,
            )
        max_items = int(match.group(1))
        return NormalizedValidationMessage.from_key(MessageKey.MAX_ITEMS_ALLOWED, max_items=max_items)

    if message == VALIDATION_MESSAGE_NORMALIZATION_POLICY.valid_dictionary_message:
        if (
            excel_codec is not None
            and issubclass(excel_codec, CompositeExcelFieldCodec)
            and (expected := excel_codec.expected_input_message(field_def)) is not None
        ):
            return _normalize_validation_message(expected, field_def, excel_codec=excel_codec)
        return NormalizedValidationMessage.from_key(MessageKey.ENTER_VALUE_EXPECTED_FORMAT)

    return None


def _resolve_excel_codec_type(annotation: object) -> type[ExcelFieldCodec]:
    python_codec = _default_excel_codec_for_python_type(annotation)
    if python_codec is not None:
        return python_codec

    unsupported = repr(cast(object, annotation)) if isinstance(annotation, type) else str(annotation)
    raise ProgrammaticError(msg(MessageKey.VALUE_TYPE_DECLARATION_UNSUPPORTED, value_type=unsupported))


def _default_excel_codec_for_python_type(annotation: object) -> type[ExcelFieldCodec] | None:
    if annotation is str:
        from excelalchemy.codecs.text import TextFieldCodec

        return TextFieldCodec
    if annotation is int or annotation is float or annotation is Decimal:
        from excelalchemy.codecs.number import NumberFieldCodec

        return NumberFieldCodec
    if annotation is bool:
        from excelalchemy.codecs.boolean import BooleanFieldCodec

        return BooleanFieldCodec
    return None


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
        declared_codec = self.declared_metadata.excel_codec
        if declared_codec is not UnspecifiedFieldCodec:
            return declared_codec

        annotation = self.annotation
        origin = get_origin(annotation)
        if origin in (UnionType, Union):
            args = [arg for arg in get_args(annotation) if arg is not type(None)]
            if len(args) != 1:
                raise ProgrammaticError(msg(MessageKey.UNSUPPORTED_FIELD_TYPE_DECLARATION, annotation=annotation))
            return _resolve_excel_codec_type(args[0])

        return _resolve_excel_codec_type(annotation)

    @property
    def allows_none(self) -> bool:
        return any(arg is type(None) for arg in get_args(self.annotation))

    @property
    def required(self) -> bool:
        declared = self.declared_metadata
        declared_meta = declared.declared

        if declared_meta.is_primary_key or declared_meta.unique:
            if declared_meta.required is False:
                raise ProgrammaticError(
                    msg(MessageKey.PRIMARY_KEY_AND_UNIQUE_MUST_BE_REQUIRED),
                    message_key=MessageKey.PRIMARY_KEY_AND_UNIQUE_MUST_BE_REQUIRED,
                )
            return True
        if declared_meta.effective_required is not None:
            return bool(declared_meta.effective_required)
        return self.raw_field.is_required()

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
            if self.allows_none:
                return None
            raise ValueError(umsg(MessageKey.THIS_FIELD_IS_REQUIRED))

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

    def field_for_validation_location(self, location: str) -> PydanticFieldAdapter | None:
        field_name = self._field_name_for_validation_location(location)
        if field_name is None:
            return None
        return self.field(field_name)

    def _field_name_for_validation_location(self, location: str) -> str | None:
        if location in self.model.model_fields:
            return location

        for name, field_info in self.model.model_fields.items():
            if location in _validation_locations_for_field(field_info):
                return name

        return None

    def field_names(self) -> list[str]:
        return list(self.model.model_fields.keys())


def _validation_locations_for_field(field_info: FieldInfo) -> set[str]:
    locations: set[str] = set()
    if isinstance(field_info.alias, str):
        locations.add(field_info.alias)
    _collect_validation_alias_locations(field_info.validation_alias, locations)
    return locations


def _collect_validation_alias_locations(alias: object, locations: set[str]) -> None:
    if isinstance(alias, str):
        locations.add(alias)
        return

    choices = getattr(alias, 'choices', None)
    if isinstance(choices, (list, tuple)):
        for choice in cast(Iterable[object], choices):
            _collect_validation_alias_locations(choice, locations)
        return

    path = getattr(alias, 'path', None)
    if isinstance(path, (list, tuple)) and path and isinstance(path[0], str):
        locations.add(path[0])


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
    raw_messages = [arg for arg in exc.args if str(arg)] or [umsg(MessageKey.INVALID_INPUT)]
    messages = [_normalize_validation_message(message, field_def, excel_codec=excel_codec) for message in raw_messages]
    error_container.extend(_build_cell_error(label=field_def.label, normalized=normalized) for normalized in messages)


def _model_validate[ModelT: BaseModel](
    data: dict[str, object],
    model: type[ModelT],
    model_adapter: PydanticModelAdapter,
    failed_fields: set[str],
) -> ModelT | list[ExcelCellError | ExcelRowError]:
    try:
        return model.model_validate(data, by_alias=False, by_name=True)
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
            normalized = _normalize_pydantic_error(error)
            mapped.append(_build_row_error(normalized))
            continue

        field_name = loc[0]
        if not isinstance(field_name, str):
            normalized = _normalize_pydantic_error(error)
            mapped.append(_build_row_error(normalized))
            continue
        if field_name in failed_fields:
            continue

        field_adapter = model_adapter.field_for_validation_location(field_name)
        if field_adapter is None:
            normalized = _normalize_pydantic_error(error)
            mapped.append(_build_row_error(normalized))
            continue

        normalized = _normalize_pydantic_error(
            error,
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
