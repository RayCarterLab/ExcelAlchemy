"""Schema declarations for the FastAPI reference project."""

from typing import Annotated

from pydantic import BaseModel

from excelalchemy import ExcelColumn


class EmployeeImporter(BaseModel):
    full_name: Annotated[str, ExcelColumn(label='Full name', order=1, hint='Use the legal name')]
    age: Annotated[float, ExcelColumn(label='Age', order=2)]


__all__ = ['EmployeeImporter']
