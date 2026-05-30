"""A Python Library for Reading and Writing Excel Files"""

__version__ = '3.0.0a0'
from excelalchemy.adapters.pydantic import extract_pydantic_model
from excelalchemy.artifacts import ExcelArtifact
from excelalchemy.codecs.base import CompositeExcelFieldCodec, ExcelFieldCodec
from excelalchemy.codecs.boolean import BooleanCodec
from excelalchemy.codecs.date import DateCodec
from excelalchemy.codecs.date_range import DateRangeCodec
from excelalchemy.codecs.email import EmailCodec
from excelalchemy.codecs.money import MoneyCodec
from excelalchemy.codecs.multi_checkbox import MultiChoiceCodec
from excelalchemy.codecs.number import NumberCodec
from excelalchemy.codecs.number_range import NumberRangeCodec
from excelalchemy.codecs.organization import (
    MultiOrganizationCodec,
    SingleOrganizationCodec,
)
from excelalchemy.codecs.phone_number import PhoneNumberCodec
from excelalchemy.codecs.radio import SingleChoiceCodec
from excelalchemy.codecs.staff import MultiStaffCodec, SingleStaffCodec
from excelalchemy.codecs.string import StringCodec
from excelalchemy.codecs.tree import (
    MultiTreeNodeCodec,
    SingleTreeNodeCodec,
)
from excelalchemy.codecs.url import UrlCodec
from excelalchemy.columns import ExcelColumn
from excelalchemy.config import ExportConfig, ExporterConfig, ImportConfig, ImporterConfig, ImportMode
from excelalchemy.exceptions import (
    ConfigError,
    ExcelCellError,
    ExcelRowError,
    ProgrammaticError,
    WorksheetNotFoundError,
)
from excelalchemy.primitives.constants import CharacterSet, DataRangeOption, DateFormat, Option
from excelalchemy.primitives.identity import (
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
from excelalchemy.results import (
    CellErrorMap,
    CellIssueRecord,
    CodeIssueSummary,
    FieldIssueSummary,
    ImportPreflightResult,
    ImportPreflightStatus,
    ImportResult,
    RowIssueMap,
    RowIssueRecord,
    RowIssueSummary,
    ValidateHeaderResult,
    ValidateResult,
    ValidateRowResult,
)
from excelalchemy.runtime.facade import ExcelAlchemy
from excelalchemy.storage import ExcelStorage
from excelalchemy.util.file import flatten

__all__ = [
    'BooleanCodec',
    'CellErrorMap',
    'CellIssueRecord',
    'CodeIssueSummary',
    'ColumnIndex',
    'CompositeExcelFieldCodec',
    'ConfigError',
    'DataRangeOption',
    'DataUrlStr',
    'DateCodec',
    'DateFormat',
    'DateRangeCodec',
    'EmailCodec',
    'ExcelAlchemy',
    'ExcelArtifact',
    'ExcelCellError',
    'ExcelColumn',
    'ExcelFieldCodec',
    'ExcelRowError',
    'ExcelStorage',
    'ExportConfig',
    'ExporterConfig',
    'FieldIssueSummary',
    'ImportConfig',
    'ImportMode',
    'ImportPreflightResult',
    'ImportPreflightStatus',
    'ImportResult',
    'ImporterConfig',
    'Key',
    'Label',
    'MoneyCodec',
    'MultiChoiceCodec',
    'MultiOrganizationCodec',
    'MultiStaffCodec',
    'MultiTreeNodeCodec',
    'NumberCodec',
    'NumberRangeCodec',
    'Option',
    'OptionId',
    'PhoneNumberCodec',
    'ProgrammaticError',
    'RowIndex',
    'RowIssueMap',
    'RowIssueRecord',
    'RowIssueSummary',
    'SingleChoiceCodec',
    'SingleOrganizationCodec',
    'SingleStaffCodec',
    'SingleTreeNodeCodec',
    'StringCodec',
    'UniqueKey',
    'UniqueLabel',
    'UrlCodec',
    'UrlStr',
    'ValidateHeaderResult',
    'ValidateResult',
    'ValidateRowResult',
    'WorksheetNotFoundError',
    'extract_pydantic_model',
    'flatten',
]
