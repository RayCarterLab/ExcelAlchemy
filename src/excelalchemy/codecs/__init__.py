"""Public codec helpers and registry helpers."""

from excelalchemy.codecs.base import ExcelCodecConfig, ExcelFieldCodec

EXCEL_CHOICE_CODECS: dict[type[ExcelFieldCodec], type[ExcelFieldCodec]] = {}


def excel_choice_codec(codec: type[ExcelFieldCodec]) -> type[ExcelFieldCodec]:
    EXCEL_CHOICE_CODECS[codec] = codec
    return codec


EXCEL_CHOICE_VALUE_TYPE = EXCEL_CHOICE_CODECS
excel_choice = excel_choice_codec

from excelalchemy.codecs.boolean import BooleanCodec  # noqa: E402
from excelalchemy.codecs.date import DateCodec  # noqa: E402
from excelalchemy.codecs.date_range import DateRangeCodec  # noqa: E402
from excelalchemy.codecs.email import EmailCodec  # noqa: E402
from excelalchemy.codecs.money import MoneyCodec  # noqa: E402
from excelalchemy.codecs.multi_checkbox import MultiChoiceCodec  # noqa: E402
from excelalchemy.codecs.number import NumberCodec  # noqa: E402
from excelalchemy.codecs.number_range import NumberRangeCodec  # noqa: E402
from excelalchemy.codecs.organization import MultiOrganizationCodec, SingleOrganizationCodec  # noqa: E402
from excelalchemy.codecs.phone_number import PhoneNumberCodec  # noqa: E402
from excelalchemy.codecs.radio import SingleChoiceCodec  # noqa: E402
from excelalchemy.codecs.staff import MultiStaffCodec, SingleStaffCodec  # noqa: E402
from excelalchemy.codecs.string import StringCodec  # noqa: E402
from excelalchemy.codecs.tree import MultiTreeNodeCodec, SingleTreeNodeCodec  # noqa: E402
from excelalchemy.codecs.url import UrlCodec  # noqa: E402

__all__ = [
    'EXCEL_CHOICE_CODECS',
    'EXCEL_CHOICE_VALUE_TYPE',
    'BooleanCodec',
    'DateCodec',
    'DateRangeCodec',
    'EmailCodec',
    'ExcelCodecConfig',
    'ExcelFieldCodec',
    'MoneyCodec',
    'MultiChoiceCodec',
    'MultiOrganizationCodec',
    'MultiStaffCodec',
    'MultiTreeNodeCodec',
    'NumberCodec',
    'NumberRangeCodec',
    'PhoneNumberCodec',
    'SingleChoiceCodec',
    'SingleOrganizationCodec',
    'SingleStaffCodec',
    'SingleTreeNodeCodec',
    'StringCodec',
    'UrlCodec',
    'excel_choice',
    'excel_choice_codec',
]
