from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Set, TypeVar, Union

from pydantic import BaseModel

from excelalchemy.types.identity import Key, Label, OptionId

HEADER_HINT = """
导入填写须知：
1、填写数据时，请注意查看字段名称上的注释，避免导入失败。
2、表格中可能包含部分只读字段，可能是根据系统规则自动生成或是在编辑时禁止被修改，仅用于导出时查看，导入时不生效。
3、字段名称背景是红色的为必填字段，导入时必须根据注释的提示填写好内容。
4、请不要随意修改列的单元格格式，避免模板校验不通过。
5、导入前请删除示例数据。
"""

EXCEL_COMMENT_FORMAT = {'height': 100, 'width': 300, 'font_size': 7}
CHARACTER_WIDTH = 1.3
DEFAULT_SHEET_NAME = 'Sheet1'
# 连接符
UNIQUE_HEADER_CONNECTOR: str = '·'

# 数据导出结果列
RESULT_COLUMN_LABEL: Label = Label('校验结果\n重新上传前请删除此列')
RESULT_COLUMN_KEY: Key = Key('__result__')

# 数据导出原因列
REASON_COLUMN_LABEL: Label = Label('失败原因\n重新上传前请删除此列')
REASON_COLUMN_KEY: Key = Key('__reason__')

BACKGROUND_REQUIRED_COLOR = 'FDAFB5'
BACKGROUND_ERROR_COLOR = 'FEC100'
FONT_READ_COLOR = 'FF0000'

# 多选分隔符
MULTI_CHECKBOX_SEPARATOR = '，'

FIELD_DATA_KEY = Key('fieldData')

# 毫秒转换为秒
MILLISECOND_TO_SECOND = 1000

# options 最多允许的选项数量
MAX_OPTIONS_COUNT = 100

DEFAULT_FIELD_META_ORDER = -1
DictStrAny = Dict[str, Any]
DictAny = Dict[Any, Any]
SetStr = Set[str]
ListStr = List[str]
IntStr = Union[int, str]
ContextT = TypeVar('ContextT')
ImporterCreateModelT = TypeVar('ImporterCreateModelT', bound=BaseModel)
ImporterUpdateModelT = TypeVar('ImporterUpdateModelT', bound=BaseModel)
ExporterModelT = TypeVar('ExporterModelT', bound=BaseModel)
CreateModelT = TypeVar('CreateModelT', bound=BaseModel)
UpdateModelT = TypeVar('UpdateModelT', bound=BaseModel)


class CharacterSet(str, Enum):
    CHINESE = 'CHINESE'
    NUMBER = 'NUMBER'
    LOWERCASE_LETTERS = 'LOWERCASE_LETTERS'
    UPPERCASE_LETTERS = 'UPPERCASE_LETTERS'
    SPECIAL_SYMBOLS = 'SPECIAL_SYMBOLS'


class DateFormat(str, Enum):
    YEAR = 'YEAR'
    MONTH = 'MONTH'
    DAY = 'DAY'
    MINUTE = 'MINUTE'


class DataRangeOption(str, Enum):
    NONE = 'NONE'
    PRE = 'PRE'
    NEXT = 'NEXT'


DATE_FORMAT_TO_PYTHON_MAPPING = {
    DateFormat.YEAR: '%Y',
    DateFormat.MONTH: '%Y-%m',
    DateFormat.DAY: '%Y-%m-%d',
    DateFormat.MINUTE: '%Y-%m-%d %H:%M',
}
DATE_FORMAT_TO_HINT_MAPPING = {
    DateFormat.YEAR: 'yyyy',
    DateFormat.MONTH: 'yyyy/mm',
    DateFormat.DAY: 'yyyy/mm/dd',
    DateFormat.MINUTE: 'yyyy/mm/dd hh:mm',
}
DATA_RANGE_OPTION_TO_CHINESE = {
    DataRangeOption.PRE: '早于当前时间',
    DataRangeOption.NEXT: '晚于当前时间',
    DataRangeOption.NONE: '无限制',
}


@dataclass
class Option:
    # For user's usage, the name is the most important symbol
    id: OptionId
    name: str
