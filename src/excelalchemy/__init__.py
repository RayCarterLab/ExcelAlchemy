"""A Python Library for Reading and Writing Excel Files"""

__version__ = '2.1.0'
from excelalchemy._primitives.constants import CharacterSet, DataRangeOption, DateFormat, Option
from excelalchemy._primitives.deprecation import ExcelAlchemyDeprecationWarning
from excelalchemy._primitives.identity import (
    Base64Str,
    ColumnIndex,
    DataUrlStr,
    Key,
    Label,
    OptionId,
    RowIndex,
    UniqueKey,
    UniqueLabel,
    UrlStr,
)
from excelalchemy.artifacts import ExcelArtifact
from excelalchemy.codecs.base import CompositeExcelFieldCodec, ExcelFieldCodec
from excelalchemy.codecs.boolean import Boolean, BooleanCodec
from excelalchemy.codecs.date import Date, DateCodec
from excelalchemy.codecs.date_range import DateRange, DateRangeCodec
from excelalchemy.codecs.email import Email, EmailCodec
from excelalchemy.codecs.money import Money, MoneyCodec
from excelalchemy.codecs.multi_checkbox import MultiCheckbox, MultiChoiceCodec
from excelalchemy.codecs.number import Number, NumberCodec
from excelalchemy.codecs.number_range import NumberRange, NumberRangeCodec
from excelalchemy.codecs.organization import (
    MultiOrganization,
    MultiOrganizationCodec,
    SingleOrganization,
    SingleOrganizationCodec,
)
from excelalchemy.codecs.phone_number import PhoneNumber, PhoneNumberCodec
from excelalchemy.codecs.radio import Radio, SingleChoiceCodec
from excelalchemy.codecs.staff import MultiStaff, MultiStaffCodec, SingleStaff, SingleStaffCodec
from excelalchemy.codecs.string import String, StringCodec
from excelalchemy.codecs.tree import (
    MultiTreeNode,
    MultiTreeNodeCodec,
    SingleTreeNode,
    SingleTreeNodeCodec,
)
from excelalchemy.codecs.url import Url, UrlCodec
from excelalchemy.config import ExporterConfig, ImporterConfig, ImportMode
from excelalchemy.core.alchemy import ExcelAlchemy
from excelalchemy.core.storage_protocol import ExcelStorage
from excelalchemy.exceptions import ConfigError, ExcelCellError, ExcelRowError, ProgrammaticError
from excelalchemy.helper.pydantic import extract_pydantic_model
from excelalchemy.metadata import ExcelMeta, FieldMeta, PatchFieldMeta
from excelalchemy.results import ImportResult, ValidateHeaderResult, ValidateResult, ValidateRowResult
from excelalchemy.util.file import flatten

__all__ = [
    'Base64Str',
    'Boolean',
    'BooleanCodec',
    'ColumnIndex',
    'CompositeExcelFieldCodec',
    'ConfigError',
    'DataRangeOption',
    'DataUrlStr',
    'Date',
    'DateCodec',
    'DateFormat',
    'DateRange',
    'DateRangeCodec',
    'Email',
    'EmailCodec',
    'ExcelAlchemy',
    'ExcelAlchemyDeprecationWarning',
    'ExcelArtifact',
    'ExcelCellError',
    'ExcelFieldCodec',
    'ExcelMeta',
    'ExcelRowError',
    'ExcelStorage',
    'ExporterConfig',
    'FieldMeta',
    'ImportMode',
    'ImportResult',
    'ImporterConfig',
    'Key',
    'Label',
    'Money',
    'MoneyCodec',
    'MultiCheckbox',
    'MultiChoiceCodec',
    'MultiOrganization',
    'MultiOrganizationCodec',
    'MultiStaff',
    'MultiStaffCodec',
    'MultiTreeNode',
    'MultiTreeNodeCodec',
    'Number',
    'NumberCodec',
    'NumberRange',
    'NumberRangeCodec',
    'Option',
    'OptionId',
    'PatchFieldMeta',
    'PhoneNumber',
    'PhoneNumberCodec',
    'ProgrammaticError',
    'Radio',
    'RowIndex',
    'SingleChoiceCodec',
    'SingleOrganization',
    'SingleOrganizationCodec',
    'SingleStaff',
    'SingleStaffCodec',
    'SingleTreeNode',
    'SingleTreeNodeCodec',
    'String',
    'StringCodec',
    'UniqueKey',
    'UniqueLabel',
    'Url',
    'UrlCodec',
    'UrlStr',
    'ValidateHeaderResult',
    'ValidateResult',
    'ValidateRowResult',
    'extract_pydantic_model',
    'flatten',
]
