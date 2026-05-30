import logging
from typing import Annotated

import pytest
from pydantic import BaseModel

from excelalchemy import (
    ExcelAlchemy,
    ExcelColumn,
    MultiChoiceCodec,
    Option,
    OptionId,
    SingleChoiceCodec,
)
from excelalchemy.codecs.field_codec import CODEC_LOGGER_NAME
from excelalchemy.config import ImporterConfig


def _build_field(model: type[BaseModel], field_index: int = 0):
    alchemy = ExcelAlchemy(ImporterConfig(model, locale='en'))
    return alchemy.ordered_field_meta[field_index]


def test_radio_option_resolution_warning_uses_codec_logger(caplog: pytest.LogCaptureFixture) -> None:
    class Importer(BaseModel):
        radio: Annotated[
            str,
            ExcelColumn(
                codec=SingleChoiceCodec(),
                label='Status',
                order=1,
                options=[
                    Option(id=OptionId(1), name='Open'),
                    Option(id=OptionId(2), name='Closed'),
                ],
            ),
        ]

    field = _build_field(Importer)

    with caplog.at_level(logging.WARNING, logger=CODEC_LOGGER_NAME):
        assert field.excel_codec.format_display_value('3', field) == '3'

    assert caplog.records
    record = caplog.records[-1]
    assert record.name == CODEC_LOGGER_NAME
    assert 'Codec SingleChoiceFieldCodec could not resolve a configured option for field "Status"' in record.message
    assert "returning '3' as-is" in record.message


def test_boolean_render_warning_uses_codec_logger(caplog: pytest.LogCaptureFixture) -> None:
    class Importer(BaseModel):
        is_active: Annotated[bool, ExcelColumn(label='Is active', order=1)]

    field = _build_field(Importer)

    with caplog.at_level(logging.WARNING, logger=CODEC_LOGGER_NAME):
        assert field.excel_codec.format_display_value('maybe', field) == 'maybe'

    assert caplog.records
    record = caplog.records[-1]
    assert record.name == CODEC_LOGGER_NAME
    assert 'Codec BooleanFieldCodec could not format workbook value for field "Is active"' in record.message
    assert "Expected '是' or '否'" in record.message


def test_multi_checkbox_parse_warning_uses_codec_logger(caplog: pytest.LogCaptureFixture) -> None:
    class Importer(BaseModel):
        hobbies: Annotated[list[str], ExcelColumn(codec=MultiChoiceCodec(), label='Hobbies', order=1)]

    field = _build_field(Importer)

    with caplog.at_level(logging.WARNING, logger=CODEC_LOGGER_NAME):
        assert field.excel_codec.parse_input(123, field) == 123

    assert caplog.records
    record = caplog.records[-1]
    assert record.name == CODEC_LOGGER_NAME
    assert 'Codec MultiChoiceFieldCodec could not parse workbook input for field "Hobbies"' in record.message
    assert 'Expected a delimited string or a list of selected values' in record.message
