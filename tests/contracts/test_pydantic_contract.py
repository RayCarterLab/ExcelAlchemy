from pydantic import BaseModel

from excelalchemy import DateFormat, DateRange, Email, FieldMeta, Label
from excelalchemy.helper.pydantic import extract_pydantic_model, instantiate_pydantic_model
from excelalchemy.types.field import FieldMetaInfo, extract_declared_field_metadata


class ContractPydanticModel(BaseModel):
    email: Email = FieldMeta(label='邮箱', order=1)
    stay_range: DateRange = FieldMeta(label='停留时间', order=2, date_format=DateFormat.DAY)


class TestPydanticContracts:
    def test_fieldmeta_keeps_excel_metadata_outside_pydantic_fieldinfo_subclass(self):
        raw_field_info = ContractPydanticModel.model_fields['email']

        assert not isinstance(raw_field_info, FieldMetaInfo)
        assert extract_declared_field_metadata(raw_field_info).label == Label('邮箱')

    def test_extract_pydantic_model_preserves_excel_metadata_shape(self):
        metas = extract_pydantic_model(ContractPydanticModel)

        assert [meta.unique_label for meta in metas] == ['邮箱', '停留时间·开始日期', '停留时间·结束日期']
        assert [meta.parent_key for meta in metas] == ['email', 'stay_range', 'stay_range']
        assert [meta.key for meta in metas] == ['email', 'start', 'end']
        assert [meta.offset for meta in metas] == [0, 0, 1]
        assert metas[0].required is True

    def test_instantiate_pydantic_model_maps_validation_errors_to_excel_cell_errors(self):
        result = instantiate_pydantic_model({'email': 'not-an-email'}, ContractPydanticModel)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].label == Label('邮箱')
        assert result[1].label == Label('停留时间')
