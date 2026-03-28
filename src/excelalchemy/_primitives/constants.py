from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from excelalchemy._primitives.identity import Key, Label, OptionId
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg

HEADER_HINT = dmsg(MessageKey.HEADER_HINT, locale='zh-CN')

EXCEL_COMMENT_FORMAT = {'height': 100, 'width': 300, 'font_size': 7}
CHARACTER_WIDTH = 1.3
DEFAULT_SHEET_NAME = 'Sheet1'
# Connector used when flattening merged workbook headers.
UNIQUE_HEADER_CONNECTOR: str = '·'

# Result workbook status column.
RESULT_COLUMN_LABEL: Label = Label(dmsg(MessageKey.RESULT_COLUMN_LABEL, locale='zh-CN'))
RESULT_COLUMN_KEY: Key = Key('__result__')

# Result workbook reason column.
REASON_COLUMN_LABEL: Label = Label(dmsg(MessageKey.REASON_COLUMN_LABEL, locale='zh-CN'))
REASON_COLUMN_KEY: Key = Key('__reason__')

BACKGROUND_REQUIRED_COLOR = 'FDAFB5'
BACKGROUND_ERROR_COLOR = 'FEC100'
FONT_READ_COLOR = 'FF0000'

# Display separator used for multi-choice workbook cells.
MULTI_CHECKBOX_SEPARATOR = '，'

FIELD_DATA_KEY = Key('fieldData')

# Millisecond to second conversion factor.
MILLISECOND_TO_SECOND = 1000

# Soft option-count limit used for warning logs.
MAX_OPTIONS_COUNT = 100

DEFAULT_FIELD_META_ORDER = -1
type DictStrAny = dict[str, Any]
type DictAny = dict[Any, Any]
type SetStr = set[str]
type ListStr = list[str]
type IntStr = int | str


class CharacterSet(StrEnum):
    CHINESE = 'CHINESE'
    NUMBER = 'NUMBER'
    LOWERCASE_LETTERS = 'LOWERCASE_LETTERS'
    UPPERCASE_LETTERS = 'UPPERCASE_LETTERS'
    SPECIAL_SYMBOLS = 'SPECIAL_SYMBOLS'


class DateFormat(StrEnum):
    YEAR = 'YEAR'
    MONTH = 'MONTH'
    DAY = 'DAY'
    MINUTE = 'MINUTE'


class DataRangeOption(StrEnum):
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
    DataRangeOption.PRE: dmsg(MessageKey.DATE_RANGE_OPTION_PRE_DISPLAY, locale='zh-CN'),
    DataRangeOption.NEXT: dmsg(MessageKey.DATE_RANGE_OPTION_NEXT_DISPLAY, locale='zh-CN'),
    DataRangeOption.NONE: dmsg(MessageKey.DATE_RANGE_OPTION_NONE_DISPLAY, locale='zh-CN'),
}


@dataclass
class Option:
    # For user's usage, the name is the most important symbol
    id: OptionId
    name: str
