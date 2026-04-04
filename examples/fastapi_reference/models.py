"""Schema declarations for the FastAPI reference project."""

from pydantic import BaseModel

from excelalchemy import FieldMeta, Number, String


class EmployeeImporter(BaseModel):
    full_name: String = FieldMeta(label='Full name', order=1, hint='Use the legal name')
    age: Number = FieldMeta(label='Age', order=2)


__all__ = ['EmployeeImporter']
