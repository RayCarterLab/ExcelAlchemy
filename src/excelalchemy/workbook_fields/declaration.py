"""User-declared workbook field semantics."""

from dataclasses import dataclass

from excelalchemy.messages import MessageKey
from excelalchemy.messages import display_message as dmsg
from excelalchemy.primitives.identity import Label


@dataclass(slots=True, frozen=True)
class DeclaredFieldMeta:
    """Static workbook field declaration supplied by user code."""

    label: Label
    is_primary_key: bool
    unique: bool
    ignore_import: bool
    required: bool | None
    order: int

    @property
    def effective_required(self) -> bool | None:
        if self.is_primary_key or self.unique:
            return True
        return self.required

    @property
    def comment_required(self) -> str:
        value_key = (
            MessageKey.COMMENT_REQUIRED_VALUE_REQUIRED
            if self.effective_required
            else MessageKey.COMMENT_REQUIRED_VALUE_OPTIONAL
        )
        return dmsg(MessageKey.COMMENT_REQUIRED, value=dmsg(value_key))

    @property
    def comment_unique(self) -> str:
        value_key = (
            MessageKey.COMMENT_UNIQUE_VALUE_UNIQUE if self.unique else MessageKey.COMMENT_UNIQUE_VALUE_NON_UNIQUE
        )
        return dmsg(MessageKey.COMMENT_UNIQUE, value=dmsg(value_key))


__all__ = ['DeclaredFieldMeta']
