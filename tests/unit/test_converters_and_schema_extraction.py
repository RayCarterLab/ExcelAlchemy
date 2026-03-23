from unittest import IsolatedAsyncioTestCase

from pydantic import BaseModel

from excelalchemy import ExcelAlchemy, FieldMeta, ImporterConfig, String, extract_pydantic_model
from excelalchemy.util.convertor import export_data_converter, import_data_converter


class TestConvertersAndSchemaExtraction(IsolatedAsyncioTestCase):
    class Importer(BaseModel):
        name: String = FieldMeta(label='名称', order=1)
        address: String | None = FieldMeta(label='地址', order=3)

    def test_download_template_returns_excel_payload(self):
        alchemy = ExcelAlchemy(ImporterConfig(self.Importer))
        template = alchemy.download_template()
        assert template is not None and len(template) > 100

    def test_extract_pydantic_model_returns_field_metadata(self):
        field_metas = extract_pydantic_model(self.Importer)
        self.assertIsNotNone(field_metas)
        assert len(field_metas) == 2
        assert field_metas[0].label == '名称'
        assert field_metas[1].label == '地址'

    @classmethod
    def test_import_data_converter_normalizes_keys_to_snake_case(cls):
        input_data = {'Name': 'name', 'Address': 'address', 'FieldData': {'ID': 'id', 'Name': 'name'}}
        expected = {'name': 'name', 'address': 'address', 'field_data': {'ID': 'id', 'Name': 'name'}}
        assert import_data_converter(input_data) == expected

    @classmethod
    def test_export_data_converter_flattens_field_data_keys(cls):
        input_data = {'name': 'name', 'Age': None, 'address': 'address', 'field_data': {'ID': 'id', 'Name': 'name'}}
        expected = {'address': 'address', 'age': None, 'field_data': {'ID': 'id', 'Name': 'name'}, 'name': 'name'}
        assert export_data_converter(input_data) == expected

    @classmethod
    def test_export_data_converter_preserves_camel_case_when_requested(cls):
        input_data = {'name': 'name', 'address': 'address', 'field_data': {'ID': 'id', 'Name': 'name'}}
        expected = {'address': 'address', 'fieldData.ID': 'id', 'fieldData.Name': 'name', 'name': 'name'}
        assert export_data_converter(input_data, to_camel=True) == expected
