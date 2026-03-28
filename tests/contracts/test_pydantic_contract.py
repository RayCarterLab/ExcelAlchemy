from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

from excelalchemy import (
    DateFormat,
    DateRange,
    Email,
    ExcelCellError,
    ExcelFieldCodec,
    ExcelMeta,
    ExcelRowError,
    FieldMeta,
    Label,
)
from excelalchemy.helper.pydantic import extract_pydantic_model, instantiate_pydantic_model
from excelalchemy.metadata import FieldMetaInfo, extract_declared_field_metadata


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

    def test_instantiate_pydantic_model_applies_field_constraints_and_field_validators(self):
        class FieldValidatedModel(BaseModel):
            name: Email = FieldMeta(label='邮箱', order=1, min_length=20)

            @field_validator('name')
            @classmethod
            def must_use_company_domain(cls, value: str) -> str:
                if not value.endswith('@example.com'):
                    raise ValueError('must use the company domain')
                return value

        too_short = instantiate_pydantic_model({'name': 'a@b.co'}, FieldValidatedModel)
        wrong_domain = instantiate_pydantic_model({'name': 'long-enough-address@openai.com'}, FieldValidatedModel)

        assert isinstance(too_short, list)
        assert too_short == [
            ExcelCellError(label=Label('邮箱'), message='Value should have at least 20 items after validation, not 6')
        ]

        assert isinstance(wrong_domain, list)
        assert wrong_domain == [ExcelCellError(label=Label('邮箱'), message='Value error, must use the company domain')]

    def test_instantiate_pydantic_model_maps_model_validators_to_row_errors(self):
        class ModelValidatedContract(BaseModel):
            email: Email = FieldMeta(label='邮箱', order=1)
            stay_range: DateRange = FieldMeta(label='停留时间', order=2, date_format=DateFormat.DAY)

            @model_validator(mode='after')
            def reject_combination(self):
                raise ValueError('combination invalid')

        result = instantiate_pydantic_model(
            {
                'email': 'noreply@example.com',
                'stay_range': DateRange.model_validate({'start': '2024-01-01', 'end': '2024-01-02'}),
            },
            ModelValidatedContract,
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ExcelRowError)
        assert str(result[0]) == 'Value error, combination invalid'

    def test_custom_excel_field_codec_can_define_new_style_extension_surface(self):
        class UppercaseTextCodec(str, ExcelFieldCodec):
            @classmethod
            def build_comment(cls, field_meta: FieldMetaInfo) -> str:
                return f'Normalize {field_meta.label} to uppercase'

            @classmethod
            def parse_input(cls, value: object, field_meta: FieldMetaInfo) -> str:
                return str(value).strip()

            @classmethod
            def format_display_value(cls, value: object, field_meta: FieldMetaInfo) -> str:
                return '' if value is None else str(value)

            @classmethod
            def normalize_import_value(cls, value: object, field_meta: FieldMetaInfo) -> str:
                return str(value).upper()

        class CodecContractModel(BaseModel):
            name: UppercaseTextCodec = FieldMeta(label='名称', order=1)

        metas = extract_pydantic_model(CodecContractModel)
        result = instantiate_pydantic_model({'name': 'alice'}, CodecContractModel)

        assert metas[0].excel_codec is UppercaseTextCodec
        assert metas[0].value_type is UppercaseTextCodec
        assert isinstance(result, CodecContractModel)
        assert result.name == 'ALICE'

    def test_annotated_excel_meta_supports_explicit_pydantic_v2_style_declarations(self):
        class AnnotatedContractModel(BaseModel):
            email: Annotated[Email, Field(min_length=20), ExcelMeta(label='邮箱', order=1)]
            stay_range: Annotated[
                DateRange,
                ExcelMeta(label='停留时间', order=2, date_format=DateFormat.DAY),
            ]

        raw_field_info = AnnotatedContractModel.model_fields['email']
        declared_metadata = extract_declared_field_metadata(raw_field_info)
        metas = extract_pydantic_model(AnnotatedContractModel)
        result = instantiate_pydantic_model(
            {
                'email': 'a@b.co',
                'stay_range': {'start': '2024-01-01', 'end': '2024-01-02'},
            },
            AnnotatedContractModel,
        )

        assert declared_metadata.label == Label('邮箱')
        assert declared_metadata.importer_min_length == 20
        assert [meta.unique_label for meta in metas] == ['邮箱', '停留时间·开始日期', '停留时间·结束日期']
        assert isinstance(result, list)
        assert result == [
            ExcelCellError(label=Label('邮箱'), message='Value should have at least 20 items after validation, not 6')
        ]
