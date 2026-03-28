from pendulum import DateTime, today
from pendulum.tz.timezone import Timezone
from pydantic import BaseModel

from excelalchemy import DataRangeOption, DateFormat, DateRange, FieldMeta, ValidateResult
from tests.support import BaseTestCase, FileRegistry


class TestDateRangeValueType(BaseTestCase):
    async def test_import_accepts_valid_date_range_workbook(self):
        class Importer(BaseModel):
            date_range: DateRange = FieldMeta(label='日期范围', order=1)

        alchemy = self.build_alchemy(Importer)
        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_DATE_RANGE_INPUT, output_excel_name='result.xlsx'
        )
        assert result.result == ValidateResult.SUCCESS, '导入失败'

    async def test_import_returns_header_invalid_when_merged_header_loses_trailing_child(self):
        """对于合并的表头，如果后面缺失
            日期范围	｜    （这里合并了表头）｜
            开始日期	｜    （这里缺了一个值）｜
        worksheet reader 不会读到第一行第二列的值，因此 ExcelAlchemy 不会认为有合并得表头
        """

        class Importer(BaseModel):
            date_range: DateRange = FieldMeta(label='日期范围', order=1)

        alchemy = self.build_alchemy(Importer)
        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_DATE_RANGE_MISSING_INPUT_BEFORE, output_excel_name='result.xlsx'
        )
        # ExcelAlchemy 任务需要的表头是 DateRange.model_items（开始日期，结束日期）
        # 但是 Excel 读到的表头是 日期范围
        assert result.result == ValidateResult.HEADER_INVALID, '导入失败'
        assert sorted(result.missing_required) == sorted(['日期范围·开始日期', '日期范围·结束日期'])
        assert result.unrecognized == ['日期范围']

    async def test_import_returns_header_invalid_when_merged_header_loses_leading_child(self):
        """对于合并的表头，如果前面缺失
            日期范围	        ｜   （这里合并了表头）｜
            （这里缺了一个值）	｜    开始日期       ｜
        worksheet reader 能正确读到四个值，因此 ExcelAlchemy 会认为有合并得表头
        """

        class Importer(BaseModel):
            date_range: DateRange = FieldMeta(label='日期范围', order=1)

        alchemy = self.build_alchemy(Importer)
        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_DATE_RANGE_MISSING_INPUT_AFTER, output_excel_name='result.xlsx'
        )
        assert result.result == ValidateResult.HEADER_INVALID, '导入失败'
        assert sorted(result.missing_required) == sorted(['日期范围·结束日期'])
        assert result.unrecognized == ['日期范围']

    async def test_date_range_value_type_exposes_comment_and_boundaries(self):
        class Importer(BaseModel):
            date_range: DateRange = FieldMeta(label='日期范围', order=1, date_format=DateFormat.DAY)

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        value_type = DateRange(
            DateTime(2022, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')),
            end=DateTime(2023, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')),
        )

        assert value_type.start == DateTime(2022, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai'))
        assert value_type.end == DateTime(2023, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai'))
        assert value_type.comment(field) == '必填性：必填\n格式：日期（yyyy/mm/dd）\n提示：开始日期不得晚于结束日期'

    async def test_serialize_parses_supported_date_range_inputs(self):
        class Importer(BaseModel):
            date_range: DateRange = FieldMeta(label='日期范围', order=1, date_format=DateFormat.DAY)

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        value_type = DateRange(
            DateTime(2022, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')),
            end=DateTime(2023, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')),
        )

        assert value_type.serialize(
            {
                'start': '2022/02/02',
                'end': '2023/02/02',
            },
            field,
        ) == {
            'end': DateTime(2023, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')),
            'start': DateTime(2022, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')),
        }

        assert value_type.serialize(DateTime(2023, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')), field) == DateTime(
            2023, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')
        )

        assert value_type.serialize('2023/02/02', field) == DateTime(
            2023, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')
        )

        assert value_type.serialize('2023/02/02 12:12:12', field) == DateTime(
            2023, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')
        )

        assert value_type.serialize('不能解析的值', field) == '不能解析的值'

    async def test_validate_rejects_invalid_date_range_boundaries_and_constraints(self):
        class Importer(BaseModel):
            date_range: DateRange = FieldMeta(label='日期范围', order=1, date_format=DateFormat.DAY)

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        value_type = DateRange(
            DateTime(2022, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')),
            end=DateTime(2023, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')),
        )

        self.assertRaises(
            ValueError,
            value_type.__validate__,
            {
                'start': '2022/02/02',
                'end': '2021/02/02',  # validate 只接受时间
            },
            field,
        )

        self.assertRaises(
            ValueError,
            value_type.__validate__,
            {
                'start': DateTime(2023, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')),  # 开始时间晚于结束时间
                'end': DateTime(2022, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')),
            },
            field,
        )

        assert value_type.__validate__(
            {
                'start': DateTime(2022, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')),
                'end': DateTime(2023, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')),
            },
            field,
        ) == {
            'start': 1643731200000,
            'end': 1675267200000,
        }

        field.date_range_option = DataRangeOption.PRE

        self.assertRaises(
            ValueError,
            value_type.__validate__,
            {
                'start': DateTime(1970, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')).add(
                    years=today().year
                ),  # 开始时间晚于结束时间
                'end': DateTime(2023, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')),
            },
            field,
        )

        field.date_range_option = DataRangeOption.NEXT
        self.assertRaises(
            ValueError,
            value_type.__validate__,
            {
                'start': DateTime(1970, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')),
                'end': DateTime(2022, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')).add(
                    years=today().year
                ),  # 开始时间晚于结束时间
            },
            field,
        )

        field.date_range_option = DataRangeOption.NONE
        assert value_type.__validate__(
            {
                'start': DateTime(2022, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')),
                'end': DateTime(2023, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')),
            },
            field,
        ) == {
            'start': 1643731200000,
            'end': 1675267200000,
        }

    async def test_deserialize_formats_supported_date_range_outputs(self):
        class Importer(BaseModel):
            date_range: DateRange = FieldMeta(label='日期范围', order=1, date_format=DateFormat.DAY)

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        value_type = DateRange(
            DateTime(2022, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')),
            end=DateTime(2023, 2, 2, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai')),
        )

        assert value_type.deserialize(None, field) == ''
        assert value_type.deserialize('已经是str', field) == '已经是str'
        assert (
            value_type.deserialize(DateTime(2023, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')), field)
            == '2023-02-02'
        )
        assert (
            value_type.deserialize(
                {
                    'start': DateTime(2022, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')),
                    'end': DateTime(2023, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')),
                },
                field,
            )
            == '2022-02-02 - 2023-02-02'
        )

        assert (
            value_type.deserialize(
                {
                    'start': '无法解析的值',
                    'end': DateTime(2023, 2, 2, 0, 0, 0, tzinfo=Timezone('Asia/Shanghai')),
                },
                field,
            )
            == '无法解析的值 - 2023-02-02'
        )
