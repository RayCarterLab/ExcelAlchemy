from decimal import Decimal
from typing import Annotated, cast

from pendulum import DateTime, today
from pendulum.tz.timezone import Timezone
from pydantic import BaseModel

from excelalchemy import (
    ConfigError,
    DataRangeOption,
    DateCodec,
    DateFormat,
    ExcelAlchemy,
    ExcelCellError,
    ExcelColumn,
    ImporterConfig,
    ValidateResult,
)
from excelalchemy.codecs.date import Date
from tests.support import BaseTestCase, FileRegistry


class TestDateValueType(BaseTestCase):
    async def test_download_and_import_require_explicit_date_format(self):
        """测试导入时，日期格式未指定"""

        class Importer(BaseModel):
            birth_date: Annotated[int, ExcelColumn(codec=Date, label='出生日期', order=6)]

        config = ImporterConfig(Importer, storage=self.storage_gateway)
        alchemy = ExcelAlchemy(config)

        with self.assertRaises(ConfigError):
            alchemy.download_template()

        with self.assertRaises(ConfigError):
            await alchemy.import_data(input_excel_name=FileRegistry.TEST_DATE_INPUT, output_excel_name='result.xlsx')

    async def test_import_rejects_dates_that_do_not_match_month_format(self):
        class Importer(BaseModel):
            birth_date: Annotated[
                int, ExcelColumn(codec=DateCodec.month(), label='出生日期', order=6, date_format=DateFormat.MONTH)
            ]

        alchemy = self.build_alchemy(Importer)

        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_DATE_INPUT_WRONG_RANGE,
            output_excel_name='result.xlsx',
        )
        assert result.result == ValidateResult.DATA_INVALID
        error = alchemy.cell_error_map[self.first_data_row][self.first_data_col][0]
        assert isinstance(error, ExcelCellError)
        assert error.label == '出生日期'
        assert (
            error.message == 'Enter a date in yyyy/mm format'
        )  # may be more accurate to say 'Enter a date in yyyy/mm format, e.g. 2021/01'
        assert (
            repr(error)
            == "ExcelCellError(label=Label('出生日期'), parent_label=None, message='Enter a date in yyyy/mm format')"
        )
        assert str(error) == '【出生日期】Enter a date in yyyy/mm format'

    async def test_import_rejects_dates_that_do_not_match_day_format(self):
        class Importer(BaseModel):
            birth_date: Annotated[
                int, ExcelColumn(codec=DateCodec.day(), label='出生日期', order=6, date_format=DateFormat.DAY)
            ]

        alchemy = self.build_alchemy(Importer)
        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_DATE_INPUT_WRONG_FORMAT,
            output_excel_name='result.xlsx',
        )

        assert result.result == ValidateResult.DATA_INVALID
        error = alchemy.cell_error_map[self.first_data_row][self.first_data_col][0]
        assert isinstance(error, ExcelCellError)
        assert error.label == '出生日期'
        assert error.message == 'Enter a date in yyyy/mm/dd format'

    async def test_serialize_parses_supported_date_inputs(self):
        class Importer(BaseModel):
            birth_date: Annotated[
                int, ExcelColumn(codec=DateCodec.day(), label='出生日期', order=6, date_format=DateFormat.DAY)
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        assert field.excel_codec.parse_input('', field) == ''
        assert field.excel_codec.parse_input('2022-02-02', field) == DateTime(
            2022, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')
        )
        assert field.excel_codec.parse_input('2022-02-02 12:12:12', field) == DateTime(
            2022, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')
        )
        assert field.excel_codec.parse_input('2022-02-02 25:00:00', field) == '2022-02-02 25:00:00'
        assert field.excel_codec.parse_input(
            DateTime(2022, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')), field
        ) == DateTime(2022, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai'))

    async def test_deserialize_formats_supported_runtime_values(self):
        class Importer(BaseModel):
            birth_date: Annotated[
                int, ExcelColumn(codec=DateCodec.day(), label='出生日期', order=6, date_format=DateFormat.DAY)
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        field.excel_codec = cast(Date, field.excel_codec)
        assert field.excel_codec.format_display_value('', field) == ''
        assert field.excel_codec.format_display_value('2022-02-02', field) == '2022-02-02'
        assert field.excel_codec.format_display_value('2022-02-02 12:12:12', field) == '2022-02-02 12:12:12'
        assert field.excel_codec.format_display_value(1682408817000, field) == '2023-04-25'
        assert field.excel_codec.format_display_value(Decimal('1682408817000'), field) == '1682408817000'
        assert (
            field.excel_codec.format_display_value(
                DateTime(2022, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')), field
            )
            == '2022-02-02'
        )

    async def test_validate_day_format_normalizes_to_day_timestamp(self):
        class Importer(BaseModel):
            birth_date: Annotated[
                int, ExcelColumn(codec=DateCodec.day(), label='出生日期', order=6, date_format=DateFormat.DAY)
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(Date, field.excel_codec)

        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, '2022-02-02', field)
        assert (
            field.excel_codec.normalize_import_value(
                DateTime(2022, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')), field
            )
            == 1643731200000
        )

    async def test_validate_month_format_normalizes_to_month_timestamp(self):
        class Importer(BaseModel):
            birth_date: Annotated[
                int, ExcelColumn(codec=DateCodec.month(), label='出生日期', order=6, date_format=DateFormat.MONTH)
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(Date, field.excel_codec)

        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, '2022-02-02', field)
        assert (
            field.excel_codec.normalize_import_value(
                DateTime(2022, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')), field
            )
            == 1643644800000
        )

    async def test_validate_year_format_normalizes_to_year_timestamp(self):
        class Importer(BaseModel):
            birth_date: Annotated[
                int, ExcelColumn(codec=DateCodec.year(), label='出生日期', order=6, date_format=DateFormat.YEAR)
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(Date, field.excel_codec)

        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, '2022-02-02', field)
        assert (
            field.excel_codec.normalize_import_value(
                DateTime(2022, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')), field
            )
            == 1640966400000
        )
        field.date_format = None
        self.assertRaises(ConfigError, field.excel_codec.normalize_import_value, '2022-02-02', field)

    async def test_validate_minute_format_normalizes_to_minute_timestamp(self):
        class Importer(BaseModel):
            birth_date: Annotated[
                int, ExcelColumn(codec=DateCodec.minute(), label='出生日期', order=6, date_format=DateFormat.MINUTE)
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        field.excel_codec = cast(Date, field.excel_codec)

        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, '2022-02-02', field)
        assert (
            field.excel_codec.normalize_import_value(
                DateTime(2022, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')), field
            )
            == 1643775120000
        )

    async def test_validate_respects_date_range_option_constraints(self):
        class Importer(BaseModel):
            birth_date: Annotated[
                int, ExcelColumn(codec=DateCodec.day(), label='出生日期', order=6, date_format=DateFormat.DAY)
            ]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        field.date_range_option = DataRangeOption.NEXT

        self.assertRaises(
            ValueError,
            field.excel_codec.normalize_import_value,
            '2022-02-02',
            field,
        )

        field.date_range_option = DataRangeOption.PRE

        self.assertRaises(
            ValueError,
            field.excel_codec.normalize_import_value,
            DateTime(1970, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')).add(today().year),
            field,
        )

        field.date_range_option = DataRangeOption.NONE
        assert field.excel_codec.normalize_import_value(
            DateTime(1970, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')).add(today().year),
            field,
        )
