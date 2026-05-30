"""Minimal example that uses Annotated + ExcelColumn declarations."""

from typing import Annotated

from pydantic import BaseModel, Field

from excelalchemy import EmailCodec, ExcelAlchemy, ExcelColumn, ImporterConfig


class EmployeeImporter(BaseModel):
    full_name: Annotated[
        str,
        Field(min_length=2),
        ExcelColumn(label='Full name', order=1, hint='Use the legal name', example_value='Alice Chen'),
    ]
    age: Annotated[float, Field(ge=18), ExcelColumn(label='Age', order=2)]
    work_email: Annotated[
        str,
        Field(min_length=8),
        ExcelColumn(
            codec=EmailCodec(),
            label='Work email',
            order=3,
            hint='Use your company email address',
            example_value='alice.chen@company.com',
        ),
    ]


def main() -> None:
    alchemy = ExcelAlchemy(ImporterConfig.for_create(EmployeeImporter, locale='en'))
    template = alchemy.download_template_artifact(filename='employee-template.xlsx')
    print(f'Generated template: {template.filename} ({len(template.as_bytes())} bytes)')


if __name__ == '__main__':
    main()
