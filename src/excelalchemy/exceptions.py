"""Public exception types raised by ExcelAlchemy."""

from excelalchemy._primitives.constants import UNIQUE_HEADER_CONNECTOR
from excelalchemy._primitives.identity import Label, UniqueLabel
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import message as msg


class ExcelCellError(Exception):
    """Cell-level import error tied to a specific workbook header."""

    message = msg(MessageKey.EXCEL_IMPORT_ERROR)
    label: Label
    parent_label: Label | None
    detail: dict[str, object]

    def __init__(
        self,
        message: str,
        label: Label,
        parent_label: Label | None = None,
        **kwargs: object,
    ):
        super().__init__(message, label, parent_label)
        self.message = message or self.message
        self.label = label
        self.parent_label = parent_label
        self.detail = kwargs or {}
        self._validate()

    def __str__(self) -> str:
        return f'【{self.label}】{self.message}'

    def __repr__(self) -> str:
        return f"{type(self).__name__}(label=Label('{self.label}'), message='{self.message}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExcelCellError):
            return NotImplemented
        return str(self) == str(other)

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


class ExcelRowError(Exception):
    """Row-level import error not tied to a single workbook cell."""

    message = msg(MessageKey.EXCEL_ROW_IMPORT_ERROR)

    def __init__(
        self,
        message: str,
        **kwargs: object,
    ):
        super().__init__(message)
        self.message = message or self.message
        self.detail = kwargs or {}

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{type(self).__name__}(message='{self.message}')"


class ProgrammaticError(Exception): ...


class ConfigError(Exception): ...
