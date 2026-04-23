"""Public exception types raised by ExcelAlchemy."""

from excelalchemy._primitives.constants import UNIQUE_HEADER_CONNECTOR
from excelalchemy._primitives.identity import Label, UniqueLabel
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import message as msg


class ExcelAlchemyError(Exception):
    """Base error type for public ExcelAlchemy exceptions."""

    default_message = ''
    message: str
    message_key: MessageKey | None
    detail: dict[str, object]

    def __init__(
        self,
        message: str = '',
        *,
        message_key: MessageKey | None = None,
        **kwargs: object,
    ) -> None:
        resolved_message = message or self.default_message
        super().__init__(resolved_message)
        self.message = resolved_message
        self.message_key = message_key
        self.detail = kwargs or {}

    def __str__(self) -> str:
        return self.message

    @property
    def display_message(self) -> str:
        return self.message

    @property
    def code(self) -> str:
        if self.message_key is not None:
            return self.message_key.value
        return type(self).__name__

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            'type': type(self).__name__,
            'code': self.code,
            'message': self.message,
            'display_message': self.display_message,
        }
        if self.message_key is not None:
            payload['message_key'] = self.message_key.value
        if self.detail:
            payload['detail'] = dict(self.detail)
        return payload


class ExcelCellError(ExcelAlchemyError):
    """Cell-level import error tied to a specific workbook header."""

    default_message = msg(MessageKey.EXCEL_IMPORT_ERROR)
    label: Label
    parent_label: Label | None

    def __init__(
        self,
        message: str,
        label: Label,
        parent_label: Label | None = None,
        *,
        message_key: MessageKey | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(message, message_key=message_key, **kwargs)
        self.label = label
        self.parent_label = parent_label
        self._validate()

    def __str__(self) -> str:
        return f'【{self.label}】{self.message}'

    @property
    def display_message(self) -> str:
        return str(self)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(label=Label('{self.label}'), "
            f"parent_label={self.parent_label!r}, message='{self.message}')"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExcelCellError):
            return NotImplemented
        return (
            self.message,
            self.label,
            self.parent_label,
            self.detail,
        ) == (
            other.message,
            other.label,
            other.parent_label,
            other.detail,
        )

    @property
    def unique_label(self) -> UniqueLabel:
        label = (
            f'{self.parent_label}{UNIQUE_HEADER_CONNECTOR}{self.label}'
            if (self.parent_label and self.parent_label != self.label)
            else self.label
        )
        return UniqueLabel(label)

    def _validate(self) -> None:
        if not self.label:
            raise ValueError(msg(MessageKey.LABEL_CANNOT_BE_EMPTY))

    def to_dict(self) -> dict[str, object]:
        payload = super().to_dict()
        payload['label'] = str(self.label)
        payload['field_label'] = str(self.label)
        payload['parent_label'] = None if self.parent_label is None else str(self.parent_label)
        payload['unique_label'] = str(self.unique_label)
        return payload


class ExcelRowError(ExcelAlchemyError):
    """Row-level import error not tied to a single workbook cell."""

    default_message = msg(MessageKey.EXCEL_ROW_IMPORT_ERROR)

    def __init__(
        self,
        message: str,
        *,
        message_key: MessageKey | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(message, message_key=message_key, **kwargs)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(message='{self.message}', detail={self.detail!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExcelRowError):
            return NotImplemented
        return (self.message, self.detail) == (other.message, other.detail)


class ProgrammaticError(ExcelAlchemyError):
    """Raised when a declaration or library usage pattern is unsupported."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(message='{self.message}', detail={self.detail!r})"


class ConfigError(ExcelAlchemyError):
    """Raised when runtime configuration is missing or inconsistent."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(message='{self.message}', detail={self.detail!r})"


class WorksheetNotFoundError(ExcelAlchemyError):
    """Raised when the configured worksheet does not exist in the workbook."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(message='{self.message}', detail={self.detail!r})"
