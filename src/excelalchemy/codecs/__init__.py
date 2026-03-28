"""Registry helpers for choice-oriented Excel field codecs."""

from excelalchemy.codecs.base import ExcelFieldCodec

EXCEL_CHOICE_CODECS: dict[type[ExcelFieldCodec], type[ExcelFieldCodec]] = {}


def excel_choice_codec(codec: type[ExcelFieldCodec]) -> type[ExcelFieldCodec]:
    EXCEL_CHOICE_CODECS[codec] = codec
    return codec


EXCEL_CHOICE_VALUE_TYPE = EXCEL_CHOICE_CODECS
excel_choice = excel_choice_codec
