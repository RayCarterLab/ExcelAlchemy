"""Minimal example that uses Annotated + ExcelMeta declarations."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

from excelalchemy import Email, ExcelAlchemy, ExcelMeta, ImporterConfig, Number


class EmployeeImporter(BaseModel):
    full_name: Annotated[str, Field(min_length=2), ExcelMeta(label='Full name', order=1, hint='Use the legal name')]
    age: Annotated[Number, Field(ge=18), ExcelMeta(label='Age', order=2)]
    work_email: Annotated[
        Email,
        Field(min_length=8),
        ExcelMeta(label='Work email', order=3, hint='Use your company email address'),
    ]


def main() -> None:
    alchemy = ExcelAlchemy(ImporterConfig.for_create(EmployeeImporter, locale='en'))
    template = alchemy.download_template_artifact(filename='employee-template.xlsx')
    print(f'Generated template: {template.filename} ({len(template.as_bytes())} bytes)')


if __name__ == '__main__':
    main()
