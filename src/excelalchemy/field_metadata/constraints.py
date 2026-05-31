"""Importer-side field constraint hints."""

from dataclasses import dataclass

from excelalchemy.messages import MessageKey
from excelalchemy.messages import display_message as dmsg


@dataclass(slots=True, frozen=True)
class ImportConstraints:
    """Importer-side validation hints mirrored from Pydantic constraints."""

    ge: float | None = None
    le: float | None = None
    max_digits: int | None = None
    decimal_places: int | None = None
    min_items: int | None = None
    max_items: int | None = None
    unique_items: bool | None = None
    min_length: int | None = None
    max_length: int | None = None

    @property
    def comment_max_length(self) -> str:
        return dmsg(
            MessageKey.COMMENT_MAX_LENGTH,
            value=self.max_length or dmsg(MessageKey.COMMENT_MAX_LENGTH_VALUE_UNLIMITED),
        )


__all__ = ['ImportConstraints']
