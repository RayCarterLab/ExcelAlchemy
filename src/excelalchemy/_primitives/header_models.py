"""Internal workbook header models."""

from pydantic import BaseModel
from pydantic.fields import Field

from excelalchemy._primitives.constants import UNIQUE_HEADER_CONNECTOR
from excelalchemy._primitives.identity import Label, UniqueLabel


class ExcelHeader(BaseModel):
    """Normalized workbook header extracted from user input."""

    label: Label = Field(description='Workbook header label.')
    parent_label: Label = Field(
        description='Parent workbook header label. Falls back to the label itself for flat headers.'
    )
    offset: int = Field(default=0, description='Child-column offset under a merged parent header.')

    @property
    def unique_label(self) -> UniqueLabel:
        """Return the fully qualified workbook header label."""
        label = (
            f'{self.parent_label}{UNIQUE_HEADER_CONNECTOR}{self.label}'
            if self.parent_label != self.label
            else self.label
        )
        return UniqueLabel(label)
