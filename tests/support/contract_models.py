import datetime
from typing import Annotated, Any

from pydantic import BaseModel

from excelalchemy import (
    DateCodec,
    DateFormat,
    DateRangeCodec,
    EmailCodec,
    ExcelCellError,
    ExcelColumn,
    Label,
    MultiChoiceCodec,
    NumberCodec,
    NumberRangeCodec,
    Option,
    OptionId,
    PhoneNumberCodec,
    SingleChoiceCodec,
    UrlCodec,
)
from excelalchemy.messages import MessageKey
from excelalchemy.messages import display_message as dmsg

COMMON_OPTIONS = [
    Option(id=OptionId('1'), name='选项1'),
    Option(id=OptionId('2'), name='选项2'),
    Option(id=OptionId('3'), name='选项3'),
]

ORGANIZATION_OPTIONS = [
    Option(id=OptionId('1'), name='腾讯'),
    Option(id=OptionId('2'), name='阿里巴巴'),
    Option(id=OptionId('3'), name='百度'),
]

STAFF_OPTIONS = [
    Option(id=OptionId('1'), name='张三'),
    Option(id=OptionId('2'), name='李四'),
    Option(id=OptionId('3'), name='王五'),
]

TREE_OPTIONS = [
    Option(id=OptionId('1'), name='研发部'),
    Option(id=OptionId('2'), name='市场部'),
    Option(id=OptionId('3'), name='销售部'),
]

BOSS_OPTIONS = [
    Option(id=OptionId('1'), name='马云'),
    Option(id=OptionId('2'), name='马化腾'),
    Option(id=OptionId('3'), name='李彦宏'),
]

MULTI_ORGANIZATION_CODEC = MultiChoiceCodec(
    entity_name_plural='organizations',
    hint=dmsg(MessageKey.MULTI_ORGANIZATION_HINT),
    include_options_in_comment=False,
    include_mode_in_comment=False,
    separator='、',
)
MULTI_STAFF_CODEC = MultiChoiceCodec(
    entity_name_plural='staff members',
    hint=dmsg(MessageKey.MULTI_STAFF_HINT),
    include_options_in_comment=False,
    include_mode_in_comment=False,
    separator='、',
)
MULTI_TREE_NODE_CODEC = MultiChoiceCodec(
    entity_name_plural='tree nodes',
    hint=dmsg(MessageKey.MULTI_TREE_HINT),
    include_options_in_comment=False,
    include_mode_in_comment=False,
)
SINGLE_TREE_NODE_CODEC = SingleChoiceCodec(
    entity_name='tree node',
    hint=dmsg(MessageKey.SINGLE_TREE_HINT),
    include_options_in_comment=False,
    include_mode_in_comment=False,
)
SINGLE_ORGANIZATION_CODEC = SingleChoiceCodec(
    entity_name='organization',
    hint=dmsg(MessageKey.SINGLE_ORGANIZATION_HINT),
    include_options_in_comment=False,
    include_mode_in_comment=False,
)
SINGLE_STAFF_CODEC = SingleChoiceCodec(
    entity_name='staff member',
    hint=dmsg(MessageKey.SINGLE_STAFF_HINT),
    include_options_in_comment=False,
    include_mode_in_comment=False,
)


class SimpleContractImporter(BaseModel):
    age: Annotated[float, ExcelColumn(label='年龄', order=1)]
    name: Annotated[str, ExcelColumn(label='姓名', order=2)]
    address: Annotated[str | None, ExcelColumn(label='地址', order=4)]
    is_active: Annotated[bool, ExcelColumn(label='是否启用', order=5)]
    birth_date: Annotated[
        int, ExcelColumn(codec=DateCodec.year(), label='出生日期', order=6, date_format=DateFormat.YEAR)
    ]
    email: Annotated[str, ExcelColumn(codec=EmailCodec(), label='邮箱', order=7)]
    price: Annotated[float, ExcelColumn(codec=NumberCodec(fraction_digits=2), label='价格', order=8)]
    web: Annotated[str, ExcelColumn(codec=UrlCodec(), label='网址', order=9)]
    hobby: Annotated[
        list[str],
        ExcelColumn(
            codec=MultiChoiceCodec(),
            label='爱好',
            order=10,
            options=[
                Option(id=OptionId('1'), name='篮球'),
                Option(id=OptionId('2'), name='足球'),
                Option(id=OptionId('3'), name='乒乓球'),
            ],
        ),
    ]
    company: Annotated[
        list[str], ExcelColumn(codec=MULTI_ORGANIZATION_CODEC, label='公司', order=11, options=ORGANIZATION_OPTIONS)
    ]
    manager: Annotated[list[str], ExcelColumn(codec=MULTI_STAFF_CODEC, label='经理', order=12, options=STAFF_OPTIONS)]
    department: Annotated[
        list[str], ExcelColumn(codec=MULTI_TREE_NODE_CODEC, label='部门', order=13, options=TREE_OPTIONS)
    ]
    team: Annotated[str, ExcelColumn(codec=SINGLE_TREE_NODE_CODEC, label='团队', order=14, options=TREE_OPTIONS)]
    phone: Annotated[str, ExcelColumn(codec=PhoneNumberCodec(), label='电话', order=15)]
    radio: Annotated[str, ExcelColumn(codec=SingleChoiceCodec(), label='单选', order=16, options=COMMON_OPTIONS)]
    boss: Annotated[str, ExcelColumn(codec=SINGLE_ORGANIZATION_CODEC, label='老板', order=17, options=BOSS_OPTIONS)]
    leader: Annotated[str, ExcelColumn(codec=SINGLE_STAFF_CODEC, label='领导', order=18, options=STAFF_OPTIONS)]


class MergedContractImporter(SimpleContractImporter):
    max_stay_date: Annotated[
        dict[str, object],
        ExcelColumn(codec=DateRangeCodec.year(), label='最大停留日期', order=19, date_format=DateFormat.YEAR),
    ]
    salary: Annotated[dict[str, object], ExcelColumn(codec=NumberRangeCodec(), label='工资', order=20)]


def sample_simple_export_row() -> dict[str, Any]:
    return {
        'age': 18,
        'name': '张三',
        'address': '北京市朝阳区',
        'is_active': True,
        'birth_date': datetime.datetime(2021, 1, 1),
        'email': 'noreply@example.com',
        'price': 100,
        'web': 'https://www.baidu.com',
        'hobby': ['1', '2'],
        'company': ['1', '2'],
        'manager': ['1', '2'],
        'department': ['1', '2'],
        'team': '1',
        'phone': '13800138000',
        'radio': '1',
        'boss': '1',
        'leader': '1',
    }


def sample_merged_export_row() -> dict[str, Any]:
    return sample_simple_export_row() | {
        'max_stay_date': {'start': '2020-01-01', 'end': '2021-01-02'},
        'salary': {'start': 1000, 'end': 2000},
    }


async def creator(data: dict[str, Any], context: dict[str, Any] | None) -> dict[str, Any]:
    if context:
        data['company_id'] = context.get('company_id')
    return data


async def updater(data: dict[str, Any], context: dict[str, Any] | None) -> dict[str, Any]:
    if context:
        data['company_id'] = context.get('company_id')
    return data


async def failing_creator(data: dict[str, Any], context: dict[str, Any] | None) -> dict[str, Any]:
    raise ExcelCellError(label=Label('姓名'), message='Simulated failure')
