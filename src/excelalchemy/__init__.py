"""A Python Library for Reading and Writing Excel Files"""

__version__ = '2.0.0rc1'
from excelalchemy.const import CharacterSet, DataRangeOption, DateFormat, Option
from excelalchemy.core.alchemy import ExcelAlchemy
from excelalchemy.core.storage_protocol import ExcelStorage
from excelalchemy.exc import ConfigError, ExcelCellError, ProgrammaticError
from excelalchemy.helper.pydantic import extract_pydantic_model
from excelalchemy.types.alchemy import ExporterConfig, ImporterConfig, ImportMode
from excelalchemy.types.field import FieldMeta, PatchFieldMeta
from excelalchemy.types.identity import ColumnIndex, Key, Label, OptionId, RowIndex, UniqueKey, UniqueLabel
from excelalchemy.types.result import ImportResult, ValidateHeaderResult, ValidateResult, ValidateRowResult
from excelalchemy.types.value.boolean import Boolean
from excelalchemy.types.value.date import Date
from excelalchemy.types.value.date_range import DateRange
from excelalchemy.types.value.email import Email
from excelalchemy.types.value.money import Money
from excelalchemy.types.value.multi_checkbox import MultiCheckbox
from excelalchemy.types.value.number import Number
from excelalchemy.types.value.number_range import NumberRange
from excelalchemy.types.value.organization import MultiOrganization, SingleOrganization
from excelalchemy.types.value.phone_number import PhoneNumber
from excelalchemy.types.value.radio import Radio
from excelalchemy.types.value.staff import MultiStaff, SingleStaff
from excelalchemy.types.value.string import String
from excelalchemy.types.value.tree import MultiTreeNode, SingleTreeNode
from excelalchemy.types.value.url import Url
from excelalchemy.util.file import flatten

__all__ = [
    'Boolean',
    'ColumnIndex',
    'Date',
    'DateFormat',
    'DateRange',
    'DataRangeOption',
    'Email',
    'ExcelStorage',
    'ExcelAlchemy',
    'ExcelCellError',
    'ExporterConfig',
    'FieldMeta',
    'ImportMode',
    'ImportResult',
    'ImporterConfig',
    'Key',
    'Label',
    'Money',
    'MultiCheckbox',
    'MultiOrganization',
    'MultiStaff',
    'MultiTreeNode',
    'Number',
    'NumberRange',
    'Option',
    'OptionId',
    'PatchFieldMeta',
    'PhoneNumber',
    'ProgrammaticError',
    'ConfigError',
    'Radio',
    'RowIndex',
    'SingleOrganization',
    'SingleStaff',
    'SingleTreeNode',
    'String',
    'UniqueKey',
    'UniqueLabel',
    'Url',
    'ValidateHeaderResult',
    'ValidateResult',
    'ValidateRowResult',
    'extract_pydantic_model',
    'flatten',
]
