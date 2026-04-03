from dataclasses import FrozenInstanceError
from typing import Annotated

from pydantic import BaseModel, Field

from excelalchemy import (
    ConfigError,
    DataRangeOption,
    Date,
    DateFormat,
    Email,
    EmailCodec,
    ExcelMeta,
    FieldMeta,
    Number,
    Option,
    OptionId,
    Radio,
)
from tests.support import BaseTestCase


class TestFieldMetadata(BaseTestCase):
    async def test_set_is_primary_key_marks_field_as_required_and_unique(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(
                label='邮箱',
                is_primary_key=True,
                order=1,
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].is_primary_key

        class Importer(BaseModel):
            email: Email = FieldMeta(
                label='邮箱',
                is_primary_key=False,
                order=1,
            )

        alchemy = self.build_alchemy(Importer)
        assert not alchemy.ordered_field_meta[0].is_primary_key
        alchemy.ordered_field_meta[0].set_is_primary_key(True)

        assert alchemy.ordered_field_meta[0].is_primary_key
        assert alchemy.ordered_field_meta[0].required and alchemy.ordered_field_meta[0].unique

    async def test_set_unique_marks_field_as_required(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(
                label='邮箱',
                unique=True,
                order=1,
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].unique

        class Importer(BaseModel):
            email: Email = FieldMeta(
                label='邮箱',
                unique=False,
                order=1,
            )

        alchemy = self.build_alchemy(Importer)
        assert not alchemy.ordered_field_meta[0].unique
        alchemy.ordered_field_meta[0].set_unique(True)

        assert alchemy.ordered_field_meta[0].unique
        assert alchemy.ordered_field_meta[0].required

    async def test_validate_state_accepts_consistent_field_configuration(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(
                label='邮箱',
                order=1,
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].validate_state() is None

    async def test_exchange_option_ids_to_names(self):
        class Importer(BaseModel):
            sex: Radio = FieldMeta(
                label='邮箱',
                order=1,
                options=[Option(id=OptionId('male'), name='男'), Option(id=OptionId('female'), name='女')],
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].exchange_option_ids_to_names([OptionId('male')]) == ['男']
        assert alchemy.ordered_field_meta[0].exchange_option_ids_to_names([OptionId('not found')]) == ['not found']

    async def test_exchange_names_to_option_ids_with_errors(self):
        class Importer(BaseModel):
            sex: Radio = FieldMeta(
                label='邮箱',
                order=1,
                options=[Option(id=OptionId('male'), name='男'), Option(id=OptionId('female'), name='女')],
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].exchange_names_to_option_ids_with_errors(
            [OptionId('男'), OptionId('不存在')]
        ) == (['male'], ['Option not found; check the header comment for valid values'])

    async def test_unique_label_uses_parent_label_for_nested_fields(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(
                label='邮箱',
                order=1,
            )
            email2: Email = FieldMeta(
                label='邮箱2',
                order=2,
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].unique_label == '邮箱'

        # this is a trick, in user's code, they should not do this
        alchemy.ordered_field_meta[1].parent_label = '父'
        assert alchemy.ordered_field_meta[1].unique_label == '父·邮箱2'

    async def test_unique_key_uses_parent_key_for_nested_fields(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(
                label='邮箱',
                order=1,
            )
            email2: Email = FieldMeta(
                label='邮箱',
                order=2,
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].unique_key == 'email'

        # this is a trick, in user's code, they should not do this
        alchemy.ordered_field_meta[1].parent_key = 'parent'
        assert alchemy.ordered_field_meta[1].unique_key == 'parent·email2'

    async def test_options_id_map_indexes_options_by_id(self):
        class Importer(BaseModel):
            sex: Radio = FieldMeta(
                label='邮箱',
                order=1,
                options=[Option(id=OptionId('male'), name='男'), Option(id=OptionId('female'), name='女')],
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].options_id_map == {
            'male': Option(id=OptionId('male'), name='男'),
            'female': Option(id=OptionId('female'), name='女'),
        }

    async def test_options_name_map_indexes_options_by_name(self):
        class Importer(BaseModel):
            sex: Radio = FieldMeta(
                label='邮箱',
                order=1,
                options=[Option(id=OptionId('male'), name='男'), Option(id=OptionId('female'), name='女')],
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].options_name_map == {
            '男': Option(id=OptionId('male'), name='男'),
            '女': Option(id=OptionId('female'), name='女'),
        }

    async def test_comment_required_reflects_required_flag(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(
                label='邮箱',
                order=1,
            )
            email2: Email | None = FieldMeta(
                label='邮箱',
                order=2,
                required=False,
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].comment_required == '必填性：必填'
        assert alchemy.ordered_field_meta[1].comment_required == '必填性：选填'

    async def test_comment_date_format_uses_configured_date_pattern(self):
        class Importer(BaseModel):
            date: Date = FieldMeta(label='日期', order=1, date_format=DateFormat.DAY)
            date2: Date = FieldMeta(label='日期', order=2, date_format=DateFormat.MONTH)

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].comment_date_format == '格式：日期（yyyy/mm/dd）'
        assert alchemy.ordered_field_meta[1].comment_date_format == '格式：日期（yyyy/mm）'

    async def test_comment_date_range_option_reflects_range_constraint(self):
        class Importer(BaseModel):
            ne: Date = FieldMeta(
                label='日期',
                order=1,
                date_range_option=DataRangeOption.NEXT,
            )
            no: Date = FieldMeta(
                label='日期',
                order=2,
                date_range_option=DataRangeOption.NONE,
            )
            pre: Date = FieldMeta(
                label='日期',
                order=3,
                date_range_option=DataRangeOption.PRE,
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].comment_date_range_option == '范围：晚于当前时间'
        assert alchemy.ordered_field_meta[1].comment_date_range_option == '范围：无限制'
        assert alchemy.ordered_field_meta[2].comment_date_range_option == '范围：早于当前时间'

    async def test_comment_hint_returns_configured_hint(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(
                label='邮箱',
                order=1,
                hint='请输入邮箱',
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].comment_hint == '提示：请输入邮箱'

    async def test_comment_options_lists_available_option_names(self):
        class Importer(BaseModel):
            sex: Radio = FieldMeta(
                label='邮箱',
                order=1,
                options=[Option(id=OptionId('male'), name='男'), Option(id=OptionId('female'), name='女')],
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].comment_options == '选项：男，女'

    async def test_comment_fraction_digits_reflects_numeric_precision(self):
        class Importer(BaseModel):
            decimal: Number = FieldMeta(
                label='邮箱',
                order=1,
                fraction_digits=2,
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].comment_fraction_digits == '小数位数：2'

    async def test_comment_unit_reflects_configured_unit(self):
        class Importer(BaseModel):
            decimal: Number = FieldMeta(
                label='邮箱',
                order=1,
                unit='元',
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].comment_unit == '单位：元'

    async def test_comment_unique_reflects_unique_constraint(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(
                label='邮箱',
                order=1,
                unique=True,
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].comment_unique == '唯一性：唯一'

    async def test_comment_max_length_reflects_string_length_limit(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(
                label='邮箱',
                order=1,
                max_length=10,
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].comment_max_length == '最大长度：10'

    async def test_must_date_format_returns_configured_format_or_raises(self):
        class Importer(BaseModel):
            date: Date = FieldMeta(label='日期', order=1, date_format=DateFormat.DAY)
            date2: Date = FieldMeta(
                label='日期',
                order=2,
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].must_date_format == DateFormat.DAY

        with self.assertRaises(ConfigError):
            alchemy.ordered_field_meta[1].must_date_format  # noqa

    async def test_python_date_format_maps_enum_to_strftime_pattern(self):
        class Importer(BaseModel):
            date: Date = FieldMeta(label='日期', order=1, date_format=DateFormat.DAY)
            date2: Date = FieldMeta(
                label='日期',
                order=2,
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].python_date_format == '%Y-%m-%d'

        with self.assertRaises(ConfigError):
            alchemy.ordered_field_meta[1].python_date_format  # noqa

    async def test_repr_summarizes_field_metadata_state(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(
                label='邮箱',
                order=1,
                unique=True,
            )

        alchemy = self.build_alchemy(Importer)
        assert alchemy.ordered_field_meta[0].excel_codec is Email
        assert alchemy.ordered_field_meta[0].value_type is EmailCodec
        assert repr(alchemy.ordered_field_meta[0]) == (
            "FieldMeta(label='邮箱', order=1, excel_codec='Email', required=True, "
            "unique=True, comment_required='必填性：必填', comment_unique='唯一性：唯一')"
        )

    async def test_excelmeta_supports_annotated_field_declarations(self):
        class Importer(BaseModel):
            email: Annotated[Email, Field(max_length=10), ExcelMeta(label='邮箱', order=1)]

        alchemy = self.build_alchemy(Importer)
        field_meta = alchemy.ordered_field_meta[0]

        assert field_meta.label == '邮箱'
        assert field_meta.excel_codec is Email
        assert field_meta.comment_max_length == '最大长度：10'

    async def test_field_metadata_exposes_split_internal_layers(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(
                label='邮箱',
                order=1,
                unique=True,
                hint='请输入邮箱',
                max_length=10,
            )

        alchemy = self.build_alchemy(Importer)
        field_meta = alchemy.ordered_field_meta[0]

        assert field_meta.declared_meta.label == '邮箱'
        assert field_meta.declared_meta.unique
        assert field_meta.runtime_binding.parent_label == '邮箱'
        assert field_meta.runtime_binding.parent_key == 'email'
        assert field_meta.presentation_meta.hint == '请输入邮箱'
        assert field_meta.import_constraints.max_length == 10
        assert field_meta.declared is field_meta.declared_meta
        assert field_meta.runtime is field_meta.runtime_binding
        assert field_meta.presentation is field_meta.presentation_meta
        assert field_meta.constraints is field_meta.import_constraints

    async def test_split_layers_own_comment_and_option_mapping_logic(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(
                label='邮箱',
                order=1,
                unique=True,
                hint='请输入邮箱',
                max_length=10,
                options=[Option(id=OptionId('work'), name='工作邮箱')],
            )

        alchemy = self.build_alchemy(Importer)
        field_meta = alchemy.ordered_field_meta[0]

        assert field_meta.declared.comment_required == '必填性：必填'
        assert field_meta.declared.comment_unique == '唯一性：唯一'
        assert field_meta.presentation.comment_hint == '提示：请输入邮箱'
        assert field_meta.presentation.options_name_map(field_label=field_meta.label) == {
            '工作邮箱': Option(id=OptionId('work'), name='工作邮箱')
        }
        assert field_meta.constraints.comment_max_length == '最大长度：10'

    async def test_clone_keeps_split_internal_layers_independent(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(label='邮箱', order=1, hint='原始提示')

        alchemy = self.build_alchemy(Importer)
        original = alchemy.ordered_field_meta[0]
        cloned = original.clone()
        cloned.hint = '新提示'
        cloned.parent_label = '父'

        assert original.hint == '原始提示'
        assert original.parent_label == '邮箱'
        assert cloned.hint == '新提示'
        assert cloned.parent_label == '父'

    async def test_split_internal_layers_are_immutable_value_objects(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(label='邮箱', order=1, hint='原始提示')

        alchemy = self.build_alchemy(Importer)
        field_meta = alchemy.ordered_field_meta[0]

        with self.assertRaises(FrozenInstanceError):
            field_meta.declared_meta.label = '新标签'  # type: ignore[misc]

        with self.assertRaises(FrozenInstanceError):
            field_meta.runtime_binding.parent_label = '父'  # type: ignore[misc]

        with self.assertRaises(FrozenInstanceError):
            field_meta.presentation_meta.hint = '新提示'  # type: ignore[misc]

        with self.assertRaises(FrozenInstanceError):
            field_meta.import_constraints.max_length = 20  # type: ignore[misc]

    async def test_mutating_facade_replaces_internal_layers_instead_of_mutating_in_place(self):
        class Importer(BaseModel):
            email: Email = FieldMeta(
                label='邮箱',
                order=1,
                hint='原始提示',
                options=[Option(id=OptionId('work'), name='工作邮箱')],
            )

        alchemy = self.build_alchemy(Importer)
        field_meta = alchemy.ordered_field_meta[0]

        original_declared_meta = field_meta.declared_meta
        original_presentation_meta = field_meta.presentation_meta

        field_meta.label = '新邮箱'
        field_meta.hint = '新的提示'
        field_meta.options = [Option(id=OptionId('personal'), name='个人邮箱')]

        assert field_meta.declared_meta is not original_declared_meta
        assert field_meta.presentation_meta is not original_presentation_meta
        assert field_meta.label == '新邮箱'
        assert field_meta.hint == '新的提示'
        assert field_meta.options == [Option(id=OptionId('personal'), name='个人邮箱')]
