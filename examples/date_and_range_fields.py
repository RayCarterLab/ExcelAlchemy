"""Example schema that focuses on date, range, and money workbook fields."""

from pydantic import BaseModel

from excelalchemy import (
    DataRangeOption,
    Date,
    DateFormat,
    DateRange,
    ExcelAlchemy,
    FieldMeta,
    ImporterConfig,
    Money,
    NumberRange,
)


class CompensationImporter(BaseModel):
    start_date: Date = FieldMeta(
        label='Start date',
        order=1,
        date_format=DateFormat.DAY,
        hint='Expected format: yyyy/mm/dd',
    )
    probation_window: DateRange = FieldMeta(
        label='Probation window',
        order=2,
        date_format=DateFormat.DAY,
        date_range_option=DataRangeOption.NONE,
        hint='Enter the probation start and end dates',
    )
    salary_band: NumberRange = FieldMeta(
        label='Salary band',
        order=3,
        fraction_digits=2,
        unit='USD',
    )
    signing_bonus: Money = FieldMeta(
        label='Signing bonus',
        order=4,
        unit='USD',
        hint='Use plain numbers without separators',
    )


def main() -> None:
    alchemy = ExcelAlchemy(ImporterConfig.for_create(CompensationImporter, locale='en'))
    template = alchemy.download_template_artifact(filename='compensation-template.xlsx')
    print(f'Generated template: {template.filename} ({len(template.as_bytes())} bytes)')
    print('Fields: Start date, Probation window, Salary band, Signing bonus')


if __name__ == '__main__':
    main()
