"""Example schema that focuses on date, range, and money workbook fields."""

from typing import Annotated

from pydantic import BaseModel

from excelalchemy import (
    DataRangeOption,
    DateCodec,
    DateFormat,
    DateRangeCodec,
    ExcelAlchemy,
    ExcelColumn,
    ImporterConfig,
    MoneyCodec,
    NumberRangeCodec,
)


class CompensationImporter(BaseModel):
    start_date: Annotated[
        int,
        ExcelColumn(
            codec=DateCodec.day(),
            label='Start date',
            order=1,
            date_format=DateFormat.DAY,
            hint='Expected format: yyyy/mm/dd',
        ),
    ]
    probation_window: Annotated[
        dict[str, object],
        ExcelColumn(
            codec=DateRangeCodec.day(),
            label='Probation window',
            order=2,
            date_format=DateFormat.DAY,
            date_range_option=DataRangeOption.NONE,
            hint='Enter the probation start and end dates',
        ),
    ]
    salary_band: Annotated[
        dict[str, object],
        ExcelColumn(codec=NumberRangeCodec(), label='Salary band', order=3, fraction_digits=2, unit='USD'),
    ]
    signing_bonus: Annotated[
        float,
        ExcelColumn(
            codec=MoneyCodec(), label='Signing bonus', order=4, unit='USD', hint='Use plain numbers without separators'
        ),
    ]


def main() -> None:
    alchemy = ExcelAlchemy(ImporterConfig.for_create(CompensationImporter, locale='en'))
    template = alchemy.download_template_artifact(filename='compensation-template.xlsx')
    print(f'Generated template: {template.filename} ({len(template.as_bytes())} bytes)')
    print('Fields: Start date, Probation window, Salary band, Signing bonus')


if __name__ == '__main__':
    main()
