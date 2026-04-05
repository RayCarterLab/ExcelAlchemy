import logging

import pytest
from pydantic import BaseModel

from excelalchemy import ExcelAlchemy, ExporterConfig, FieldMeta, Option, OptionId, String
from excelalchemy._primitives.diagnostics import METADATA_LOGGER_NAME, RUNTIME_LOGGER_NAME
from excelalchemy.config import ImporterConfig


def _build_field(model: type[BaseModel], field_index: int = 0):
    alchemy = ExcelAlchemy(ImporterConfig(model, locale='en'))
    return alchemy.ordered_field_meta[field_index]


def test_metadata_option_warning_uses_named_logger(caplog: pytest.LogCaptureFixture) -> None:
    class Importer(BaseModel):
        status: String = FieldMeta(
            label='Status',
            order=1,
            options=[Option(id=OptionId(index), name=f'Option {index}') for index in range(1, 102)],
        )

    field = _build_field(Importer)

    with caplog.at_level(logging.WARNING, logger=METADATA_LOGGER_NAME):
        field.presentation.options_name_map(field_label=field.declared.label)

    assert caplog.records
    record = caplog.records[-1]
    assert record.name == METADATA_LOGGER_NAME
    assert 'Field "Status" defines 101 options.' in record.message
    assert 'bounded vocabularies' in record.message


def test_runtime_context_warning_uses_named_logger(caplog: pytest.LogCaptureFixture) -> None:
    class Importer(BaseModel):
        name: String = FieldMeta(label='Name', order=1)

    alchemy = ExcelAlchemy(ImporterConfig(Importer, locale='en'))

    with caplog.at_level(logging.WARNING, logger=RUNTIME_LOGGER_NAME):
        alchemy.add_context({'tenant': 'a'})
        alchemy.add_context({'tenant': 'b'})

    assert caplog.records
    record = caplog.records[-1]
    assert record.name == RUNTIME_LOGGER_NAME
    assert 'Replacing an existing conversion context' in record.message


def test_runtime_exporter_inference_logs_use_named_logger(caplog: pytest.LogCaptureFixture) -> None:
    class Importer(BaseModel):
        name: String = FieldMeta(label='Name', order=1)

    async def _creator(data: dict[str, object], context: object | None) -> dict[str, object]:
        return data

    alchemy = ExcelAlchemy(ImporterConfig.for_create(Importer, creator=_creator, locale='en'))

    with caplog.at_level(logging.INFO, logger=RUNTIME_LOGGER_NAME):
        _ = alchemy.exporter_model

    assert caplog.records
    record = caplog.records[-1]
    assert record.name == RUNTIME_LOGGER_NAME
    assert 'Inferring exporter_model from create_importer_model.' in record.message


def test_runtime_unrecognized_export_keys_warning_uses_named_logger(caplog: pytest.LogCaptureFixture) -> None:
    class Exporter(BaseModel):
        name: String = FieldMeta(label='Name', order=1)

    alchemy = ExcelAlchemy(ExporterConfig.for_model(Exporter, locale='en'))

    with caplog.at_level(logging.WARNING, logger=RUNTIME_LOGGER_NAME):
        alchemy.export([], keys=['name', 'missing'])

    assert caplog.records
    record = caplog.records[-1]
    assert record.name == RUNTIME_LOGGER_NAME
    assert 'Ignoring export keys that are not present in the exporter model.' in record.message
    assert 'missing' in record.message
