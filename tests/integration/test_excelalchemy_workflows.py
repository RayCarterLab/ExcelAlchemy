import datetime
import random
from typing import Annotated, Any, cast

from pydantic import BaseModel, Field

from excelalchemy import (
    ConfigError,
    DateCodec,
    DateFormat,
    DateRangeCodec,
    EmailCodec,
    ExcelAlchemy,
    ExcelCellError,
    ExcelColumn,
    ExporterConfig,
    ImportConfig,
    ImporterConfig,
    ImportMode,
    Label,
    MultiChoiceCodec,
    NumberCodec,
    NumberRangeCodec,
    Option,
    OptionId,
    PhoneNumberCodec,
    ProgrammaticError,
    SingleChoiceCodec,
    UrlCodec,
    ValidateResult,
)
from excelalchemy.messages import MessageKey
from excelalchemy.messages import display_message as dmsg
from tests.support import BaseTestCase, FileRegistry

MULTI_ORGANIZATION_CODEC = MultiChoiceCodec(
    entity_name_plural='organizations',
    hint=dmsg(MessageKey.MULTI_ORGANIZATION_HINT),
    include_options_in_comment=False,
    include_mode_in_comment=False,
    separator='、',
)
MULTI_STAFF_CODEC = MultiChoiceCodec(
    entity_name_plural='staff members',
    hint=dmsg(MessageKey.MULTI_STAFF_HINT),
    include_options_in_comment=False,
    include_mode_in_comment=False,
    separator='、',
)
MULTI_TREE_NODE_CODEC = MultiChoiceCodec(
    entity_name_plural='tree nodes',
    hint=dmsg(MessageKey.MULTI_TREE_HINT),
    include_options_in_comment=False,
    include_mode_in_comment=False,
)
SINGLE_TREE_NODE_CODEC = SingleChoiceCodec(
    entity_name='tree node',
    hint=dmsg(MessageKey.SINGLE_TREE_HINT),
    include_options_in_comment=False,
    include_mode_in_comment=False,
)
SINGLE_ORGANIZATION_CODEC = SingleChoiceCodec(
    entity_name='organization',
    hint=dmsg(MessageKey.SINGLE_ORGANIZATION_HINT),
    include_options_in_comment=False,
    include_mode_in_comment=False,
)
SINGLE_STAFF_CODEC = SingleChoiceCodec(
    entity_name='staff member',
    hint=dmsg(MessageKey.SINGLE_STAFF_HINT),
    include_options_in_comment=False,
    include_mode_in_comment=False,
)


class TestExcelAlchemyIntegrationWorkflows(BaseTestCase):
    class NoMergeHeaderImporter(BaseModel):
        age: Annotated[float, ExcelColumn(label='年龄', order=1)]
        name: Annotated[str, ExcelColumn(label='姓名', order=2)]
        address: Annotated[str | None, ExcelColumn(label='地址', order=4)]
        is_active: Annotated[bool, ExcelColumn(label='是否启用', order=5)]
        birth_date: Annotated[
            int, ExcelColumn(codec=DateCodec.year(), label='出生日期', order=6, date_format=DateFormat.YEAR)
        ]
        email: Annotated[str, ExcelColumn(codec=EmailCodec(), label='邮箱', order=7)]
        price: Annotated[float, ExcelColumn(codec=NumberCodec(fraction_digits=2), label='价格', order=8)]
        web: Annotated[str, ExcelColumn(codec=UrlCodec(), label='网址', order=9)]
        hobby: Annotated[
            list[str],
            ExcelColumn(
                codec=MultiChoiceCodec(),
                label='爱好',
                order=10,
                options=[
                    Option(
                        id=OptionId('1'),
                        name='篮球',
                    ),
                    Option(
                        id=OptionId('2'),
                        name='足球',
                    ),
                    Option(
                        id=OptionId('3'),
                        name='乒乓球',
                    ),
                ],
            ),
        ]
        company: Annotated[
            list[str],
            ExcelColumn(
                codec=MULTI_ORGANIZATION_CODEC,
                label='公司',
                order=11,
                options=[
                    Option(
                        id=OptionId('1'),
                        name='腾讯',
                    ),
                    Option(
                        id=OptionId('2'),
                        name='阿里巴巴',
                    ),
                    Option(
                        id=OptionId('3'),
                        name='百度',
                    ),
                ],
            ),
        ]
        manager: Annotated[
            list[str],
            ExcelColumn(
                codec=MULTI_STAFF_CODEC,
                label='经理',
                order=12,
                options=[
                    Option(
                        id=OptionId('1'),
                        name='张三',
                    ),
                    Option(
                        id=OptionId('2'),
                        name='李四',
                    ),
                    Option(
                        id=OptionId('3'),
                        name='王五',
                    ),
                ],
            ),
        ]
        department: Annotated[
            list[str],
            ExcelColumn(
                codec=MULTI_TREE_NODE_CODEC,
                label='部门',
                order=13,
                options=[
                    Option(
                        id=OptionId('1'),
                        name='研发部',
                    ),
                    Option(
                        id=OptionId('2'),
                        name='市场部',
                    ),
                    Option(
                        id=OptionId('3'),
                        name='销售部',
                    ),
                ],
            ),
        ]
        team: Annotated[
            str,
            ExcelColumn(
                codec=SINGLE_TREE_NODE_CODEC,
                label='团队',
                order=14,
                options=[
                    Option(
                        id=OptionId('1'),
                        name='研发部',
                    ),
                    Option(
                        id=OptionId('2'),
                        name='市场部',
                    ),
                    Option(
                        id=OptionId('3'),
                        name='销售部',
                    ),
                ],
            ),
        ]
        phone: Annotated[str, ExcelColumn(codec=PhoneNumberCodec(), label='电话', order=15)]
        radio: Annotated[
            str,
            ExcelColumn(
                codec=SingleChoiceCodec(),
                label='单选',
                order=16,
                options=[
                    Option(
                        id=OptionId('1'),
                        name='选项1',
                    ),
                    Option(
                        id=OptionId('2'),
                        name='选项2',
                    ),
                    Option(
                        id=OptionId('3'),
                        name='选项3',
                    ),
                ],
            ),
        ]
        boss: Annotated[
            str,
            ExcelColumn(
                codec=SINGLE_ORGANIZATION_CODEC,
                label='老板',
                order=17,
                options=[
                    Option(
                        id=OptionId('1'),
                        name='马云',
                    ),
                    Option(
                        id=OptionId('2'),
                        name='马化腾',
                    ),
                    Option(
                        id=OptionId('3'),
                        name='李彦宏',
                    ),
                ],
            ),
        ]
        leader: Annotated[
            str,
            ExcelColumn(
                codec=SINGLE_STAFF_CODEC,
                label='领导',
                order=18,
                options=[
                    Option(
                        id=OptionId('1'),
                        name='张三',
                    ),
                    Option(
                        id=OptionId('2'),
                        name='李四',
                    ),
                    Option(
                        id=OptionId('3'),
                        name='王五',
                    ),
                ],
            ),
        ]

    class MergeHeaderImporter(NoMergeHeaderImporter):
        max_stay_date: Annotated[
            dict[str, object],
            ExcelColumn(codec=DateRangeCodec.year(), label='最大停留日期', order=19, date_format=DateFormat.YEAR),
        ]
        salary: Annotated[dict[str, object], ExcelColumn(codec=NumberRangeCodec(), label='工资', order=20)]

    @staticmethod
    async def creator(data: dict[str, Any], context: dict[str, Any] | None) -> dict[str, Any]:
        if context is None:
            context = {}
        company_id = context.get('company_id')
        data['company_id'] = company_id
        return data

    @staticmethod
    async def updater(data: dict[str, Any], context: dict[str, Any] | None) -> dict[str, Any]:
        if context is None:
            context = {}
        company_id = context.get('company_id')
        data['company_id'] = company_id
        return data

    @staticmethod
    async def is_data_exist(data: dict[str, Any], context: dict[str, Any] | None) -> bool:
        if context is None:
            context = {}
        return random.choices([True, False], weights=[0.5, 0.5])[0]

    async def test_import_create_mode_returns_success_for_valid_simple_workbook(self):
        """Test import excel with no merged header"""
        config = ImporterConfig(self.NoMergeHeaderImporter, creator=self.creator, storage=self.storage_gateway)
        alchemy = ExcelAlchemy(config)
        template = alchemy.download_template()
        assert template is not None

        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_SIMPLE_IMPORT,
            output_excel_name='result.xlsx',
        )
        assert result is not None
        assert result.result == ValidateResult.SUCCESS
        assert result.success_count == 1
        assert result.url is None

    async def test_import_update_mode_returns_success_for_valid_simple_workbook(self):
        """Test import excel with no merged header"""
        self.assertRaises(ConfigError, ImporterConfig, self.NoMergeHeaderImporter, import_mode=ImportMode.UPDATE)
        config = ImporterConfig(
            update_importer_model=self.NoMergeHeaderImporter,
            updater=self.updater,
            storage=self.storage_gateway,
            import_mode=ImportMode.UPDATE,
        )
        alchemy = ExcelAlchemy(config)

        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_SIMPLE_IMPORT,
            output_excel_name='result.xlsx',
        )
        assert result is not None
        assert result.result == ValidateResult.SUCCESS
        assert result.success_count == 1
        assert result.url is None

    async def test_import_create_or_update_mode_returns_success_for_valid_simple_workbook(self):
        """Test import excel with no merged header"""
        self.assertRaises(
            ConfigError,
            ImporterConfig,
            self.NoMergeHeaderImporter,
            creator=self.creator,
            import_mode=ImportMode.CREATE_OR_UPDATE,
        )

        alchemy = ExcelAlchemy(
            ImporterConfig(
                create_importer_model=self.NoMergeHeaderImporter,
                update_importer_model=self.NoMergeHeaderImporter,
                is_data_exist=self.is_data_exist,
                creator=self.creator,
                updater=self.updater,
                storage=self.storage_gateway,
                import_mode=ImportMode.CREATE_OR_UPDATE,
            )
        )

        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_SIMPLE_IMPORT,
            output_excel_name='result.xlsx',
        )
        assert result is not None
        assert result.result == ValidateResult.SUCCESS
        assert result.success_count == 1
        assert result.url is None

    async def test_import_records_cell_errors_for_invalid_simple_workbook(self):
        """Test import excel with no merged header"""
        config = ImporterConfig(self.NoMergeHeaderImporter, creator=self.creator, storage=self.storage_gateway)
        alchemy = ExcelAlchemy(config)
        template = alchemy.download_template()
        assert template is not None

        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_SIMPLE_IMPORT_WITH_ERROR,
            output_excel_name='result.xlsx',
        )
        assert result is not None
        assert result.result == ValidateResult.DATA_INVALID

        assert alchemy.worksheet_table is not None
        assert alchemy.header_table is not None
        assert alchemy.cell_error_map == {
            0: {
                6: [ExcelCellError(label=Label('出生日期'), message='Enter a date in yyyy format')],
                7: [
                    ExcelCellError(label=Label('邮箱'), message='Enter a valid email address, such as name@example.com')
                ],
                18: [ExcelCellError(label=Label('网址'), message='Enter a valid URL, such as https://example.com')],
                9: [
                    ExcelCellError(
                        label=Label('爱好'),
                        message='Select only configured options. Valid values include: 篮球，足球，乒乓球',
                    )
                ],
                10: [
                    ExcelCellError(
                        label=Label('公司'),
                        message='Select organizations from the configured options. Valid values include: 腾讯、阿里巴巴、百度',
                    )
                ],
                11: [
                    ExcelCellError(
                        label=Label('经理'),
                        message='Select staff members from the configured options. Valid values include: 张三、李四、王五',
                    )
                ],
                12: [
                    ExcelCellError(
                        label=Label('部门'),
                        message='Select tree nodes from the configured options. Valid values include: 研发部，市场部，销售部',
                    )
                ],
                17: [
                    ExcelCellError(
                        label=Label('团队'),
                        message='Select one tree node from the configured options. Valid values include: 研发部，市场部，销售部',
                    )
                ],
                13: [ExcelCellError(label=Label('电话'), message='Enter a valid phone number, such as 13800138000')],
                14: [
                    ExcelCellError(
                        label=Label('单选'),
                        message='Select one of the configured options. Valid values include: 选项1，选项2，选项3',
                    )
                ],
                15: [
                    ExcelCellError(
                        label=Label('老板'),
                        message='Select one organization from the configured options. Valid values include: 马云，马化腾，李彦宏',
                    )
                ],
                16: [
                    ExcelCellError(
                        label=Label('领导'),
                        message='Select one staff member from the configured options. Valid values include: 张三，李四，王五',
                    )
                ],
            }
        }

    async def test_export_returns_simple_header_dataframe_for_flat_model(self):
        config = ExporterConfig(self.NoMergeHeaderImporter, storage=self.storage_gateway)
        alchemy = ExcelAlchemy(config)
        data = [
            {
                'age': 18,
                'name': '张三',
                'address': '北京市朝阳区',
                'is_active': True,
                'birth_date': datetime.datetime.now(datetime.UTC),
                'email': 'noreply@example.com',
                'price': 100.0,
                'web': 'https://www.baidu.com',
                'hobby': '篮球',
                'company': '腾讯',
                'manager': '马化腾',
                'department': '技术部',
                'team': '技术团队',
                'phone': '13800138000',
                'radio': '选项1',
                'boss': '张三',
                'leader': '李四',
            }
        ]
        result = alchemy.export(data)

        assert result is not None

        df, has_merged_header = alchemy._gen_export_df(data)
        assert has_merged_header is False
        assert df is not None
        assert df.shape == (1, 17)
        assert df.iloc[0, 0] == '18'

    async def test_duplicate_field_order_raises_config_error(self):
        class DuplicateOrderImporter(self.NoMergeHeaderImporter):
            max_stay_date: Annotated[
                dict[str, object],
                ExcelColumn(codec=DateRangeCodec.year(), label='最大停留日期', order=7, date_format=DateFormat.YEAR),
            ]
            salary: Annotated[dict[str, object], ExcelColumn(codec=NumberRangeCodec(), label='工资', order=14)]

        config = ExporterConfig(DuplicateOrderImporter, storage=self.storage_gateway)
        self.assertRaises(ConfigError, ExcelAlchemy, config)

    async def test_export_detects_merged_header_layout_for_composite_fields(self):
        config = ExporterConfig(self.MergeHeaderImporter, storage=self.storage_gateway)
        alchemy = ExcelAlchemy(config)
        data = [
            {
                'age': 18,
                'name': '张三',
                'address': '北京市朝阳区',
                'is_active': True,
                'birth_date': datetime.datetime.now(datetime.UTC),
                'email': 'noreply@example.com',
                'price': 100.0,
                'web': 'https://www.baidu.com',
                'hobby': '篮球',
                'company': '腾讯',
                'manager': '马化腾',
                'department': '技术部',
                'team': '技术团队',
                'phone': '13800138000',
                'radio': '选项1',
                'boss': '张三',
                'leader': '李四',
                'max_stay_date': {'start': '2020-01-01', 'end': '2021-01-02'},
                'salary': {'start': 1000, 'end': 2000},
            }
        ]
        result = alchemy.export(data)
        assert result is not None

        _, has_merged_header = alchemy._gen_export_df(data)
        assert has_merged_header is True

    async def test_import_returns_success_for_merged_header_workbook(self):
        config = ImporterConfig(self.MergeHeaderImporter, creator=self.creator, storage=self.storage_gateway)
        alchemy = ExcelAlchemy(config)

        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_IMPORT_WITH_MERGE_HEADER,
            output_excel_name='result.xlsx',
        )
        assert result is not None
        assert result.result == ValidateResult.SUCCESS
        assert result.success_count == 1
        assert result.url is None

    async def test_empty_importer_model_raises_config_error(self):
        class EmptyCModel(BaseModel): ...

        config = ImporterConfig(EmptyCModel, creator=self.creator, storage=self.storage_gateway)
        with self.assertRaises(ConfigError) as cm:
            ExcelAlchemy(config)

        self.assertEqual(
            str(cm.exception),
            'No field metadata was extracted from model EmptyCModel; check its field definitions',
        )

    async def test_non_fieldmeta_definition_raises_programmatic_error(self):
        class EmptyExcelColumnModel(BaseModel):
            name: str

        config = ImporterConfig(EmptyExcelColumnModel, creator=self.creator, storage=self.storage_gateway)
        with self.assertRaises(ProgrammaticError) as cm:
            ExcelAlchemy(config)
        self.assertEqual(
            str(cm.exception),
            'Field definitions must be created with ExcelColumn or Annotated[..., ExcelColumn(...)]',
        )

    async def test_misplaced_excelmeta_default_raises_helpful_programmatic_error(self):
        class MisplacedAnnotatedExcelColumnModel(BaseModel):
            name: Annotated[str, Field(min_length=3)] = cast(str, ExcelColumn(label='Name', order=1))

        config = ImporterConfig(MisplacedAnnotatedExcelColumnModel, creator=self.creator, storage=self.storage_gateway)

        with self.assertRaises(ProgrammaticError) as cm:
            ExcelAlchemy(config)

        self.assertEqual(
            str(cm.exception),
            'Annotated fields must place ExcelColumn(...) inside Annotated metadata; '
            'use `field: Annotated[T, Field(...), ExcelColumn(...)]`',
        )

    async def test_annotated_excel_meta_definition_can_build_template(self):
        class AnnotatedImporter(BaseModel):
            email: Annotated[str, Field(min_length=10), ExcelColumn(codec=EmailCodec(), label='邮箱', order=1)]

        config = ImporterConfig(AnnotatedImporter, creator=self.creator, storage=self.storage_gateway)
        alchemy = ExcelAlchemy(config)

        template = alchemy.download_template()

        self.assertTrue(
            template.startswith('data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,')
        )

    async def test_annotated_native_python_type_with_excelcolumn_can_build_template(self):
        class NativeAnnotatedImporter(BaseModel):
            name: Annotated[str, Field(min_length=3), ExcelColumn(label='Name', order=1)]

        config = ImportConfig(
            NativeAnnotatedImporter,
            creator=self.creator,
        )
        alchemy = ExcelAlchemy(config)

        template = alchemy.download_template()

        self.assertTrue(
            template.startswith('data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,')
        )

    async def test_passing_non_config_object_raises_config_error(self):
        class NotImporterConfigModel(BaseModel):
            name: Annotated[str, ExcelColumn(label='姓名')]

        with self.assertRaises(ConfigError) as cm:
            ExcelAlchemy(cast(Any, NotImporterConfigModel))

        self.assertEqual(str(cm.exception), 'Export mode requires an ExporterConfig instance')

    async def test_download_template_in_export_mode_raises_config_error(self):
        config = ExporterConfig(self.MergeHeaderImporter, storage=self.storage_gateway)
        alchemy = ExcelAlchemy(config)

        with self.assertRaises(ConfigError) as cm:
            alchemy.download_template()

        self.assertEqual(str(cm.exception), 'This method is only available in import mode')
