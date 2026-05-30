from typing import Annotated

from pydantic import BaseModel

from excelalchemy import ExcelColumn, ValidateResult
from excelalchemy.messages import use_display_locale
from tests.support import BaseTestCase, FileRegistry


class TestBooleanValueType(BaseTestCase):
    async def test_import_accepts_recognized_boolean_cell_value(self):
        """测试导入时，布尔值正确读取"""

        class Importer(BaseModel):
            is_active: Annotated[bool, ExcelColumn(label='是否启用', order=1)]

        alchemy = self.build_alchemy(Importer)
        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_BOOLEAN_INPUT, output_excel_name='result.xlsx'
        )
        assert result.result == ValidateResult.SUCCESS, '导入失败'

    async def test_deserialize_maps_supported_boolean_inputs_to_display_values(self):
        class Importer(BaseModel):
            is_active: Annotated[bool, ExcelColumn(label='是否启用', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        assert field.excel_codec.format_display_value(None, field) == '否'
        assert field.excel_codec.format_display_value(True, field) == '是'
        assert field.excel_codec.format_display_value(False, field) == '否'
        assert field.excel_codec.format_display_value('是', field) == '是'
        assert field.excel_codec.format_display_value('否', field) == '否'
        assert field.excel_codec.format_display_value('任何无法识别的值', field) == '任何无法识别的值'
        assert field.excel_codec.format_display_value('', field) == '否'
        assert field.excel_codec.format_display_value(1, field) == '否'

    async def test_validate_accepts_only_yes_or_no_inputs(self):
        class Importer(BaseModel):
            is_active: Annotated[bool, ExcelColumn(label='是否启用', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]
        assert field.excel_codec.normalize_import_value(True, field)
        assert field.excel_codec.normalize_import_value(False, field) is False
        assert field.excel_codec.normalize_import_value('是', field)
        assert field.excel_codec.normalize_import_value('否', field) is False

        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, '任何无法识别的值', field)
        self.assertRaises(ValueError, field.excel_codec.normalize_import_value, '', field)

    async def test_boolean_display_values_follow_english_locale(self):
        class Importer(BaseModel):
            is_active: Annotated[bool, ExcelColumn(label='是否启用', order=1)]

        alchemy = self.build_alchemy(Importer)
        field = alchemy.ordered_field_meta[0]

        with use_display_locale('en'):
            assert field.excel_codec.format_display_value(None, field) == 'No'
            assert field.excel_codec.format_display_value(True, field) == 'Yes'
            assert field.excel_codec.format_display_value(False, field) == 'No'
            assert field.excel_codec.format_display_value('Yes', field) == 'Yes'
            assert field.excel_codec.format_display_value('No', field) == 'No'
            assert field.excel_codec.normalize_import_value('Yes', field)
            assert field.excel_codec.normalize_import_value('No', field) is False
            assert field.excel_codec.normalize_import_value('是', field)
            assert field.excel_codec.normalize_import_value('否', field) is False
