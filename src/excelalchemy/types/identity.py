"""定义了一些用于标识的类型"""


class Label(str):
    """Excel 的列名"""


class UniqueLabel(Label):
    """Excel 唯一的列名"""


class Key(str):
    """Python 模型的键名"""


class UniqueKey(Key):
    """Python 模型唯一的键名"""


class RowIndex(int):
    """Excel 的行索引, 从 0 开始"""


class ColumnIndex(int):
    """Excel 的列索引, 从 0 开始"""


class OptionId(str):
    """选项 ID"""


class Base64Str(str):
    """Base64 编码的字符串"""


class UrlStr(str):
    """URL 字符串"""
