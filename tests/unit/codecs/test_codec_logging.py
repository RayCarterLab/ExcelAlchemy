import logging

import pytest
from pydantic import BaseModel

from excelalchemy import Boolean, ExcelAlchemy, FieldMeta, Option, OptionId, Radio
from excelalchemy.codecs.base import CODEC_LOGGER_NAME
from excelalchemy.codecs.multi_checkbox import MultiCheckbox
from excelalchemy.config import ImporterConfig


def _build_field(model: type[BaseModel], field_index: int = 0):
    alchemy = ExcelAlchemy(ImporterConfig(model, locale='en'))
    return alchemy.ordered_field_meta[field_index]


def test_radio_option_resolution_warning_uses_codec_logger(caplog: pytest.LogCaptureFixture) -> None:
    class Importer(BaseModel):
        radio: Radio = FieldMeta(
            label='Status',
            order=1,
            options=[
                Option(id=OptionId(1), name='Open'),
                Option(id=OptionId(2), name='Closed'),
            ],
        )

    field = _build_field(Importer)

    with caplog.at_level(logging.WARNING, logger=CODEC_LOGGER_NAME):
        assert field.value_type.deserialize('3', field) == '3'

    assert caplog.records
    record = caplog.records[-1]
    assert record.name == CODEC_LOGGER_NAME
    assert 'Codec Radio could not resolve a configured option for field "Status"' in record.message
    assert "returning '3' as-is" in record.message


def test_boolean_render_warning_uses_codec_logger(caplog: pytest.LogCaptureFixture) -> None:
    class Importer(BaseModel):
        is_active: Boolean = FieldMeta(label='Is active', order=1)

    field = _build_field(Importer)

    with caplog.at_level(logging.WARNING, logger=CODEC_LOGGER_NAME):
        assert field.value_type.deserialize('maybe', field) == 'maybe'

    assert caplog.records
    record = caplog.records[-1]
    assert record.name == CODEC_LOGGER_NAME
    assert 'Codec Boolean could not format workbook value for field "Is active"' in record.message
    assert "Expected '是' or '否'" in record.message


def test_multi_checkbox_parse_warning_uses_codec_logger(caplog: pytest.LogCaptureFixture) -> None:
    class Importer(BaseModel):
        hobbies: MultiCheckbox = FieldMeta(label='Hobbies', order=1)

    field = _build_field(Importer)

    with caplog.at_level(logging.WARNING, logger=CODEC_LOGGER_NAME):
        assert field.value_type.serialize(123, field) == 123

    assert caplog.records
    record = caplog.records[-1]
    assert record.name == CODEC_LOGGER_NAME
    assert 'Codec MultiCheckbox could not parse workbook input for field "Hobbies"' in record.message
    assert 'Expected a delimited string or a list of selected values' in record.message
