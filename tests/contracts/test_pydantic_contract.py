from typing import Annotated

import pytest
from pydantic import BaseModel, Field, field_validator, model_validator

from excelalchemy import (
    DateFormat,
    DateRangeCodec,
    EmailCodec,
    ExcelCellError,
    ExcelColumn,
    ExcelFieldCodec,
    ExcelRowError,
    Label,
    MultiChoiceCodec,
    Option,
    OptionId,
    ProgrammaticError,
)
from excelalchemy.adapters.pydantic import extract_pydantic_model, instantiate_pydantic_model
from excelalchemy.adapters.pydantic_fields import extract_declared_field_metadata
from excelalchemy.codecs.date_range import DateRangeValue
from excelalchemy.field_metadata import FieldMetaInfo


class ContractPydanticModel(BaseModel):
    email: Annotated[str, ExcelColumn(codec=EmailCodec(), label='邮箱', order=1)]
    stay_range: Annotated[
        dict[str, object],
        ExcelColumn(codec=DateRangeCodec.day(), label='停留时间', order=2, date_format=DateFormat.DAY),
    ]


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

    def test_requiredness_follows_pydantic_v2_nullable_field_semantics(self):
        class NullableRequiredModel(BaseModel):
            email: Annotated[str | None, ExcelColumn(label='邮箱', order=1)]

        field = NullableRequiredModel.model_fields['email']
        metas = extract_pydantic_model(NullableRequiredModel)

        assert field.is_required() is True
        assert metas[0].required is True

    def test_default_none_makes_nullable_field_optional(self):
        class NullableDefaultModel(BaseModel):
            email: Annotated[str | None, ExcelColumn(label='邮箱', order=1)] = None

        field = NullableDefaultModel.model_fields['email']
        metas = extract_pydantic_model(NullableDefaultModel)

        assert field.is_required() is False
        assert metas[0].required is False

    def test_excelcolumn_required_override_controls_workbook_requiredness(self):
        class WorkbookOptionalModel(BaseModel):
            email: Annotated[str, ExcelColumn(label='邮箱', order=1, required=False)]

        field = WorkbookOptionalModel.model_fields['email']
        metas = extract_pydantic_model(WorkbookOptionalModel)

        assert field.is_required() is True
        assert metas[0].required is False

    def test_unique_field_cannot_be_declared_workbook_optional(self):
        class UniqueOptionalModel(BaseModel):
            email: Annotated[str, ExcelColumn(label='邮箱', order=1, unique=True, required=False)]

        with pytest.raises(ProgrammaticError) as context:
            extract_pydantic_model(UniqueOptionalModel)

        assert str(context.value) == 'Primary key and unique fields must be required'

    def test_instantiate_pydantic_model_maps_validation_errors_to_excel_cell_errors(self):
        result = instantiate_pydantic_model({'email': 'not-an-email'}, ContractPydanticModel)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].label == Label('邮箱')
        assert result[1].label == Label('停留时间')

    def test_instantiate_pydantic_model_normalizes_missing_field_messages(self):
        result = instantiate_pydantic_model({'email': 'noreply@example.com'}, ContractPydanticModel)

        assert isinstance(result, list)
        assert result == [ExcelCellError(label=Label('停留时间'), message='This field is required')]

    def test_instantiate_pydantic_model_uses_field_specific_expected_format_for_composite_codecs(self):
        result = instantiate_pydantic_model(
            {'email': 'noreply@example.com', 'stay_range': 'not-a-range'}, ContractPydanticModel
        )

        assert isinstance(result, list)
        assert result == [
            ExcelCellError(
                label=Label('停留时间'),
                message='Enter both a start date and an end date in the format shown in the header comment',
            )
        ]

    def test_instantiate_pydantic_model_applies_field_constraints_and_field_validators(self):
        class FieldValidatedModel(BaseModel):
            name: Annotated[str, Field(min_length=20), ExcelColumn(codec=EmailCodec(), label='邮箱', order=1)]

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
            ExcelCellError(label=Label('邮箱'), message='The minimum length is 20 characters', min_length=20)
        ]

        assert isinstance(wrong_domain, list)
        assert wrong_domain == [ExcelCellError(label=Label('邮箱'), message='Must use the company domain')]

    def test_instantiate_pydantic_model_validates_by_model_field_name_when_field_has_alias(self):
        class AliasedModel(BaseModel):
            full_name: Annotated[str, Field(alias='fullName'), ExcelColumn(label='姓名', order=1)]

        result = instantiate_pydantic_model({'full_name': 'Alice'}, AliasedModel)

        assert isinstance(result, AliasedModel)
        assert result.full_name == 'Alice'

    def test_instantiate_pydantic_model_maps_aliased_field_errors_to_excel_labels(self):
        class AliasedModel(BaseModel):
            full_name: Annotated[str, Field(alias='fullName', min_length=5), ExcelColumn(label='姓名', order=1)]

        result = instantiate_pydantic_model({'full_name': 'Al'}, AliasedModel)

        assert isinstance(result, list)
        assert result == [
            ExcelCellError(label=Label('姓名'), message='The minimum length is 5 characters', min_length=5)
        ]

    def test_instantiate_pydantic_model_normalizes_list_constraint_errors_from_pydantic_context(self):
        options = [
            Option(id=OptionId('a'), name='A'),
            Option(id=OptionId('b'), name='B'),
            Option(id=OptionId('c'), name='C'),
        ]

        class MultiChoiceModel(BaseModel):
            choices: Annotated[
                list[str],
                Field(min_length=2, max_length=2),
                ExcelColumn(codec=MultiChoiceCodec(), label='选项', order=1, options=options),
            ]

        too_short = instantiate_pydantic_model({'choices': ['A']}, MultiChoiceModel)
        too_long = instantiate_pydantic_model({'choices': ['A', 'B', 'C']}, MultiChoiceModel)

        assert isinstance(too_short, list)
        assert too_short == [ExcelCellError(label=Label('选项'), message='Select at least 2 items', min_items=2)]

        assert isinstance(too_long, list)
        assert too_long == [ExcelCellError(label=Label('选项'), message='Select no more than 2 items', max_items=2)]

    def test_instantiate_pydantic_model_maps_model_validators_to_row_errors(self):
        class ModelValidatedContract(BaseModel):
            email: Annotated[str, ExcelColumn(codec=EmailCodec(), label='邮箱', order=1)]
            stay_range: Annotated[
                dict[str, object],
                ExcelColumn(codec=DateRangeCodec.day(), label='停留时间', order=2, date_format=DateFormat.DAY),
            ]

            @model_validator(mode='after')
            def reject_combination(self):
                raise ValueError('combination invalid')

        result = instantiate_pydantic_model(
            {
                'email': 'noreply@example.com',
                'stay_range': DateRangeValue.model_validate({'start': '2024-01-01', 'end': '2024-01-02'}),
            },
            ModelValidatedContract,
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ExcelRowError)
        assert str(result[0]) == 'Combination invalid'

    def test_custom_excel_field_codec_can_define_new_style_extension_surface(self):
        class UppercaseTextCodec(ExcelFieldCodec):
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
            name: Annotated[str, ExcelColumn(codec=UppercaseTextCodec, label='名称', order=1)]

        metas = extract_pydantic_model(CodecContractModel)
        result = instantiate_pydantic_model({'name': 'alice'}, CodecContractModel)

        assert metas[0].excel_codec is UppercaseTextCodec
        assert metas[0].excel_codec is UppercaseTextCodec
        assert isinstance(result, CodecContractModel)
        assert result.name == 'ALICE'

    def test_annotated_excel_meta_supports_explicit_pydantic_v2_style_declarations(self):
        class AnnotatedContractModel(BaseModel):
            email: Annotated[str, Field(min_length=20), ExcelColumn(codec=EmailCodec(), label='邮箱', order=1)]
            stay_range: Annotated[
                dict[str, object],
                ExcelColumn(codec=DateRangeCodec.day(), label='停留时间', order=2, date_format=DateFormat.DAY),
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
            ExcelCellError(label=Label('邮箱'), message='The minimum length is 20 characters', min_length=20)
        ]

    def test_extract_pydantic_model_requires_a_model(self):
        with pytest.raises(ProgrammaticError) as context:
            extract_pydantic_model(None)

        assert str(context.value) == 'model cannot be None'
