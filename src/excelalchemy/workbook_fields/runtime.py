"""Runtime workbook field bindings assigned during schema extraction."""

from dataclasses import dataclass

from excelalchemy.codecs.field_codec import ExcelFieldCodec, UnspecifiedFieldCodec
from excelalchemy.errors import ProgrammaticError
from excelalchemy.messages import MessageKey
from excelalchemy.messages import message as msg
from excelalchemy.policies import WORKBOOK_UNIQUE_KEY_SEPARATOR, WORKBOOK_UNIQUE_LABEL_SEPARATOR
from excelalchemy.primitives.constants import DEFAULT_FIELD_META_ORDER
from excelalchemy.primitives.identity import Key, Label, UniqueKey, UniqueLabel


@dataclass(slots=True, frozen=True)
class RuntimeFieldBinding:
    """Runtime identity assigned after schema extraction flattens the model."""

    parent_label: Label | None = None
    key: Key | None = None
    parent_key: Key | None = None
    offset: int = DEFAULT_FIELD_META_ORDER
    excel_codec: type[ExcelFieldCodec] = UnspecifiedFieldCodec

    def make_unique_label(self, *, label: Label) -> UniqueLabel:
        if self.parent_label is None:
            raise ProgrammaticError(
                msg(MessageKey.PARENT_LABEL_EMPTY_RUNTIME),
                message_key=MessageKey.PARENT_LABEL_EMPTY_RUNTIME,
            )
        unique_label = (
            f'{self.parent_label}{WORKBOOK_UNIQUE_LABEL_SEPARATOR}{label}' if self.parent_label != label else label
        )
        return UniqueLabel(unique_label)

    def make_unique_key(self, *, key: Key | None) -> UniqueKey:
        if self.parent_key is None:
            raise ProgrammaticError(
                msg(MessageKey.PARENT_KEY_EMPTY_RUNTIME),
                message_key=MessageKey.PARENT_KEY_EMPTY_RUNTIME,
            )
        if key is None:
            raise ProgrammaticError(msg(MessageKey.KEY_EMPTY_RUNTIME), message_key=MessageKey.KEY_EMPTY_RUNTIME)
        unique_key = f'{self.parent_key}{WORKBOOK_UNIQUE_KEY_SEPARATOR}{key}' if self.parent_key != key else key
        return UniqueKey(unique_key)


__all__ = ['RuntimeFieldBinding']
