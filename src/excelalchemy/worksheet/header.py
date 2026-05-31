"""Normalized worksheet header record."""

from pydantic import BaseModel
from pydantic.fields import Field

from excelalchemy.policies import WORKBOOK_UNIQUE_LABEL_SEPARATOR
from excelalchemy.primitives.identity import Label, UniqueLabel


class ExcelHeader(BaseModel):
    """Normalized worksheet header extracted from user input."""

    label: Label = Field(description='Worksheet header label.')
    parent_label: Label = Field(
        description='Parent worksheet header label. Falls back to the label itself for flat headers.'
    )
    offset: int = Field(default=0, description='Child-column offset under a merged parent header.')

    @property
    def unique_label(self) -> UniqueLabel:
        """Return the fully qualified worksheet header label."""
        label = (
            f'{self.parent_label}{WORKBOOK_UNIQUE_LABEL_SEPARATOR}{self.label}'
            if self.parent_label != self.label
            else self.label
        )
        return UniqueLabel(label)
