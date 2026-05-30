from __future__ import annotations

import importlib
import importlib.util
from dataclasses import FrozenInstanceError, fields
from typing import Annotated

import pytest
from pydantic import BaseModel, Field
from pydantic_core import PydanticUndefined

from excelalchemy import (
    BooleanCodec,
    DateCodec,
    DateRangeCodec,
    EmailCodec,
    ExcelAlchemy,
    ExcelColumn,
    ImportConfig,
    MultiChoiceCodec,
    NumberCodec,
    NumberRangeCodec,
    SingleChoiceCodec,
    StringCodec,
)
from excelalchemy.adapters.pydantic import extract_pydantic_model, instantiate_pydantic_model
from excelalchemy.codecs import DateCodec as ModuleDateCodec
from excelalchemy.codecs import EmailCodec as ModuleEmailCodec
from excelalchemy.codecs import NumberCodec as ModuleNumberCodec
from excelalchemy.codecs import StringCodec as ModuleStringCodec
from excelalchemy.columns import ExcelColumn as ModuleExcelColumn
from excelalchemy.columns import ExcelColumnSpec
from excelalchemy.config import ExporterConfig, ImporterConfig
from excelalchemy.config import ImportConfig as ModuleImportConfig
from excelalchemy.metadata import extract_declared_field_metadata
from excelalchemy.primitives.constants import DEFAULT_FIELD_META_ORDER, CharacterSet, DateFormat, Option
from excelalchemy.primitives.identity import OptionId
from excelalchemy.runtime.facade import ExcelAlchemy as RuntimeExcelAlchemy


class V3AnnotatedImportModel(BaseModel):
    name: Annotated[str, ExcelColumn(label='Name', required=True, order=1)]
    joined_at: Annotated[int | None, ExcelColumn(label='Joined At', codec=DateCodec.day(), order=2)]
    salary: Annotated[
        float | None,
        Field(ge=0),
        ExcelColumn(label='Salary', codec=NumberCodec(fraction_digits=2), order=3),
    ]
    email: Annotated[str | None, ExcelColumn(label='Email', codec=EmailCodec(), order=4)]


def test_v3_public_root_exports_target_entry_points() -> None:
    assert ExcelAlchemy.__name__ == 'ExcelAlchemy'
    assert ExcelColumn is ModuleExcelColumn
    assert DateCodec is ModuleDateCodec
    assert NumberCodec is ModuleNumberCodec
    assert StringCodec is ModuleStringCodec
    assert EmailCodec is ModuleEmailCodec
    assert ImportConfig is ModuleImportConfig
    assert ExcelAlchemy is RuntimeExcelAlchemy
    assert callable(ImportConfig)


def test_v3_target_public_modules_are_importable() -> None:
    for module_name in (
        'excelalchemy',
        'excelalchemy.config',
        'excelalchemy.columns',
        'excelalchemy.codecs',
        'excelalchemy.storage',
        'excelalchemy.results',
        'excelalchemy.errors',
    ):
        assert importlib.import_module(module_name).__name__ == module_name


def test_v3_config_removes_legacy_storage_fields() -> None:
    removed_fields = {'minio', 'bucket_name', 'url_expires'}

    assert removed_fields.isdisjoint({field.name for field in fields(ImporterConfig)})
    assert removed_fields.isdisjoint({field.name for field in fields(ExporterConfig)})


def test_v3_concrete_responsibility_modules_are_importable() -> None:
    for module_name in (
        'excelalchemy.adapters',
        'excelalchemy.adapters.pydantic',
        'excelalchemy.schema',
        'excelalchemy.schema.layout',
        'excelalchemy.workbook',
        'excelalchemy.workbook.headers',
        'excelalchemy.workbook.table',
        'excelalchemy.runtime',
        'excelalchemy.runtime.facade',
        'excelalchemy.runtime.import_session',
        'excelalchemy.rendering',
        'excelalchemy.rendering.renderer',
        'excelalchemy.messages',
        'excelalchemy.diagnostics',
    ):
        assert importlib.import_module(module_name).__name__ == module_name


def test_excelcolumn_annotated_declaration_keeps_python_type_visible() -> None:
    name_field = V3AnnotatedImportModel.model_fields['name']
    joined_at_field = V3AnnotatedImportModel.model_fields['joined_at']
    salary_field = V3AnnotatedImportModel.model_fields['salary']
    email_field = V3AnnotatedImportModel.model_fields['email']

    name_column = extract_declared_field_metadata(name_field)
    joined_at_column = extract_declared_field_metadata(joined_at_field)
    salary_column = extract_declared_field_metadata(salary_field)
    email_column = extract_declared_field_metadata(email_field)

    assert name_field.annotation is str
    assert joined_at_field.annotation == int | None
    assert salary_field.annotation == float | None
    assert name_field.default is PydanticUndefined
    assert name_column.label == 'Name'
    assert name_column.required is True
    assert name_column.order == 1
    assert joined_at_column.label == 'Joined At'
    assert joined_at_column.date_format is DateFormat.DAY
    assert joined_at_column.excel_codec.__name__ == 'Date'
    assert salary_column.label == 'Salary'
    assert salary_column.excel_codec.__name__ == 'Number'
    assert salary_column.fraction_digits == 2
    assert salary_column.importer_ge == 0
    assert email_column.label == 'Email'
    assert email_column.excel_codec.__name__ == 'Email'


def test_excelcolumn_returns_immutable_column_spec() -> None:
    column = ExcelColumn(
        label='Name',
        character_set={CharacterSet.NUMBER},
        options=[Option(id=OptionId('1'), name='One')],
    )

    assert isinstance(column, ExcelColumnSpec)
    assert column.character_set == frozenset({CharacterSet.NUMBER})
    assert column.options == (Option(id=OptionId('1'), name='One'),)
    with pytest.raises(FrozenInstanceError):
        column.label = 'Other'


def test_codec_helpers_return_immutable_runtime_configuration() -> None:
    number_codec = NumberCodec(fraction_digits=2)
    date_codec = DateCodec.day()
    string_codec = StringCodec()
    email_codec = EmailCodec()
    boolean_codec = BooleanCodec()
    date_range_codec = DateRangeCodec.day()
    number_range_codec = NumberRangeCodec(fraction_digits=2)
    single_choice_codec = SingleChoiceCodec()
    multi_choice_codec = MultiChoiceCodec()

    assert not isinstance(number_codec, type)
    assert not isinstance(date_codec, type)
    assert not isinstance(string_codec, type)
    assert not isinstance(email_codec, type)
    assert not isinstance(boolean_codec, type)
    assert not isinstance(date_range_codec, type)
    assert not isinstance(number_range_codec, type)
    assert not isinstance(single_choice_codec, type)
    assert not isinstance(multi_choice_codec, type)
    assert number_codec.codec_type.__name__ == 'Number'
    assert number_codec.as_column_options() == {'fraction_digits': 2}
    assert date_codec.codec_type.__name__ == 'Date'
    assert date_codec.as_column_options() == {'date_format': DateFormat.DAY}
    assert string_codec.codec_type.__name__ == 'String'
    assert string_codec.as_column_options() == {}
    assert email_codec.codec_type.__name__ == 'Email'
    assert boolean_codec.codec_type.__name__ == 'Boolean'
    assert date_range_codec.codec_type.__name__ == 'DateRange'
    assert date_range_codec.as_column_options() == {'date_format': DateFormat.DAY}
    assert number_range_codec.codec_type.__name__ == 'NumberRange'
    assert number_range_codec.as_column_options() == {'fraction_digits': 2}
    assert single_choice_codec.codec_type.__name__ == 'Radio'
    assert multi_choice_codec.codec_type.__name__ == 'MultiCheckbox'
    with pytest.raises(FrozenInstanceError):
        number_codec.codec_type = object


def test_excelcolumn_defaults_to_no_ordering_or_requiredness_override() -> None:
    class DefaultColumnModel(BaseModel):
        name: Annotated[str, ExcelColumn(label='Name')]

    column = extract_declared_field_metadata(DefaultColumnModel.model_fields['name'])

    assert column.order == DEFAULT_FIELD_META_ORDER
    assert column.required is None


def test_excelcolumn_drives_schema_extraction_with_plain_python_types() -> None:
    metas = extract_pydantic_model(V3AnnotatedImportModel)
    result = instantiate_pydantic_model(
        {'name': 'Alice', 'joined_at': None, 'salary': '42.5', 'email': 'alice@example.com'},
        V3AnnotatedImportModel,
    )

    assert [meta.label for meta in metas] == ['Name', 'Joined At', 'Salary', 'Email']
    assert [meta.key for meta in metas] == ['name', 'joined_at', 'salary', 'email']
    assert metas[0].excel_codec.__name__ == 'String'
    assert metas[1].excel_codec.__name__ == 'Date'
    assert metas[2].excel_codec.__name__ == 'Number'
    assert metas[3].excel_codec.__name__ == 'Email'
    assert isinstance(result, V3AnnotatedImportModel)
    assert result.name == 'Alice'
    assert result.joined_at is None
    assert result.salary == 42.5
    assert result.email == 'alice@example.com'


def test_v3_removes_2x_compatibility_imports() -> None:
    removed_modules = (
        'excelalchemy.const',
        'excelalchemy.exc',
        'excelalchemy.identity',
        'excelalchemy.header_models',
        'excelalchemy.types',
        'excelalchemy.util.convertor',
        'excelalchemy.core',
        'excelalchemy.helper',
        'excelalchemy.i18n',
        'excelalchemy._primitives',
    )

    for module_name in removed_modules:
        assert importlib.util.find_spec(module_name) is None
