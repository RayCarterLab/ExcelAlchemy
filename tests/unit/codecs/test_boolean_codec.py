from pydantic import BaseModel

from excelalchemy import Boolean, FieldMeta, ValidateResult
from excelalchemy.i18n.messages import use_display_locale
from tests.support import BaseTestCase, FileRegistry


class TestBooleanValueType(BaseTestCase):
    async def test_import_accepts_recognized_boolean_cell_value(self):
        """测试导入时，布尔值正确读取"""

        class Importer(BaseModel):
            is_active: Boolean = FieldMeta(label='是否启用', order=1)

        alchemy = self.build_alchemy(Importer)
        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_BOOLEAN_INPUT, output_excel_name='result.xlsx'
        )
        assert result.result == ValidateResult.SUCCESS, '导入失败'

    async def test_deserialize_maps_supported_boolean_inputs_to_display_values(self):
        class Importer(BaseModel):
            is_active: Boolean = FieldMeta(label='是否启用', order=1)

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        assert field.value_type.deserialize(None, field) == '否'
        assert field.value_type.deserialize(True, field) == '是'
        assert field.value_type.deserialize(False, field) == '否'
        assert field.value_type.deserialize('是', field) == '是'
        assert field.value_type.deserialize('否', field) == '否'
        assert field.value_type.deserialize('任何无法识别的值', field) == '任何无法识别的值'
        assert field.value_type.deserialize('', field) == '否'
        assert field.value_type.deserialize(1, field) == '否'

    async def test_validate_accepts_only_yes_or_no_inputs(self):
        class Importer(BaseModel):
            is_active: Boolean = FieldMeta(label='是否启用', order=1)

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        assert field.value_type.__validate__(True, field)
        assert field.value_type.__validate__(False, field) is False
        assert field.value_type.__validate__('是', field)
        assert field.value_type.__validate__('否', field) is False

        self.assertRaises(ValueError, field.value_type.__validate__, '任何无法识别的值', field)
        self.assertRaises(ValueError, field.value_type.__validate__, '', field)

    async def test_boolean_display_values_follow_english_locale(self):
        class Importer(BaseModel):
            is_active: Boolean = FieldMeta(label='是否启用', order=1)

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        with use_display_locale('en'):
            assert field.value_type.deserialize(None, field) == 'No'
            assert field.value_type.deserialize(True, field) == 'Yes'
            assert field.value_type.deserialize(False, field) == 'No'
            assert field.value_type.deserialize('Yes', field) == 'Yes'
            assert field.value_type.deserialize('No', field) == 'No'
            assert field.value_type.__validate__('Yes', field)
            assert field.value_type.__validate__('No', field) is False
            assert field.value_type.__validate__('是', field)
            assert field.value_type.__validate__('否', field) is False
