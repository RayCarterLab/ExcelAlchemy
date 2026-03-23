import datetime
import random
from typing import Any, cast

from minio import Minio
from pydantic import BaseModel

from excelalchemy import (
    Boolean,
    ConfigError,
    Date,
    DateFormat,
    DateRange,
    Email,
    ExcelAlchemy,
    ExcelCellError,
    ExporterConfig,
    FieldMeta,
    ImporterConfig,
    ImportMode,
    Label,
    Money,
    MultiCheckbox,
    MultiOrganization,
    MultiStaff,
    MultiTreeNode,
    Number,
    NumberRange,
    Option,
    OptionId,
    PhoneNumber,
    ProgrammaticError,
    Radio,
    SingleOrganization,
    SingleStaff,
    SingleTreeNode,
    String,
    Url,
    ValidateResult,
)
from tests.support import BaseTestCase, FileRegistry


class TestExcelAlchemyIntegrationWorkflows(BaseTestCase):
    class NoMergeHeaderImporter(BaseModel):
        age: Number = FieldMeta(label='年龄', order=1)
        name: String = FieldMeta(label='姓名', order=2)
        address: String | None = FieldMeta(label='地址', order=4)
        is_active: Boolean = FieldMeta(label='是否启用', order=5)
        birth_date: Date = FieldMeta(label='出生日期', order=6, date_format=DateFormat.YEAR)
        email: Email = FieldMeta(label='邮箱', order=7)
        price: Money = FieldMeta(label='价格', order=8)
        web: Url = FieldMeta(label='网址', order=9)
        hobby: MultiCheckbox = FieldMeta(
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
        )
        company: MultiOrganization = FieldMeta(
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
        )
        manager: MultiStaff = FieldMeta(
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
        )
        department: MultiTreeNode = FieldMeta(
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
        )
        team: SingleTreeNode = FieldMeta(
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
        )
        phone: PhoneNumber = FieldMeta(label='电话', order=15)
        radio: Radio = FieldMeta(
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
        )
        boss: SingleOrganization = FieldMeta(
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
        )
        leader: SingleStaff = FieldMeta(
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
        )

    class MergeHeaderImporter(NoMergeHeaderImporter):
        max_stay_date: DateRange = FieldMeta(label='最大停留日期', order=19, date_format=DateFormat.YEAR)
        salary: NumberRange = FieldMeta(label='工资', order=20)

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
        config = ImporterConfig(self.NoMergeHeaderImporter, creator=self.creator, minio=cast(Minio, self.minio))
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
            minio=cast(Minio, self.minio),
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
                minio=cast(Minio, self.minio),
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
        config = ImporterConfig(self.NoMergeHeaderImporter, creator=self.creator, minio=cast(Minio, self.minio))
        alchemy = ExcelAlchemy(config)
        template = alchemy.download_template()
        assert template is not None

        result = await alchemy.import_data(
            input_excel_name=FileRegistry.TEST_SIMPLE_IMPORT_WITH_ERROR,
            output_excel_name='result.xlsx',
        )
        assert result is not None
        assert result.result == ValidateResult.DATA_INVALID

        assert alchemy.cell_errors == {
            0: {
                6: [ExcelCellError(label=Label('出生日期'), message='请输入格式为yyyy的日期')],
                7: [ExcelCellError(label=Label('邮箱'), message='请输入正确的邮箱')],
                18: [ExcelCellError(label=Label('网址'), message='请输入正确的网址')],
                9: [ExcelCellError(label=Label('爱好'), message='选项不存在，请参照表头的注释填写')],
                10: [ExcelCellError(label=Label('公司'), message='选项不存在，请参照表头的注释填写')],
                11: [ExcelCellError(label=Label('经理'), message='选项不存在，请参照表头的注释填写')],
                12: [ExcelCellError(label=Label('部门'), message='选项不存在，请参照表头的注释填写')],
                17: [ExcelCellError(label=Label('团队'), message='选项不存在，请参照字段注释填写')],
                13: [ExcelCellError(label=Label('电话'), message='请输入正确的手机号')],
                14: [ExcelCellError(label=Label('单选'), message='选项不存在，请参照字段注释填写')],
                15: [ExcelCellError(label=Label('老板'), message='选项不存在，请参照字段注释填写')],
                16: [ExcelCellError(label=Label('领导'), message='选项不存在，请参照字段注释填写')],
            }
        }

    async def test_export_returns_simple_header_dataframe_for_flat_model(self):
        config = ExporterConfig(self.NoMergeHeaderImporter, minio=cast(Minio, self.minio))
        alchemy = ExcelAlchemy(config)
        data = [
            {
                'age': 18,
                'name': '张三',
                'address': '北京市朝阳区',
                'is_active': True,
                'birth_date': datetime.datetime.now(datetime.UTC),
                'email': 'norepy@icloud.com',
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
            max_stay_date: DateRange = FieldMeta(label='最大停留日期', order=7, date_format=DateFormat.YEAR)
            salary: NumberRange = FieldMeta(label='工资', order=14)

        config = ExporterConfig(DuplicateOrderImporter, minio=cast(Minio, self.minio))
        self.assertRaises(ConfigError, ExcelAlchemy, config)

    async def test_export_detects_merged_header_layout_for_composite_fields(self):
        config = ExporterConfig(self.MergeHeaderImporter, minio=cast(Minio, self.minio))
        alchemy = ExcelAlchemy(config)
        data = [
            {
                'age': 18,
                'name': '张三',
                'address': '北京市朝阳区',
                'is_active': True,
                'birth_date': datetime.datetime.now(datetime.UTC),
                'email': 'norepy@icloud.com',
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

        df, has_merged_header = alchemy._gen_export_df(data)
        assert has_merged_header is True

    async def test_import_returns_success_for_merged_header_workbook(self):
        config = ImporterConfig(self.MergeHeaderImporter, creator=self.creator, minio=cast(Minio, self.minio))
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

        config = ImporterConfig(EmptyCModel, creator=self.creator, minio=cast(Minio, self.minio))
        with self.assertRaises(ConfigError) as cm:
            ExcelAlchemy(config)

        self.assertEqual(str(cm.exception), '没有从模型 EmptyCModel 中提取到字段元数据，请检查模型是否定义了字段')

    async def test_non_fieldmeta_definition_raises_programmatic_error(self):
        class EmptyFieldMetaModel(BaseModel):
            name: str

        config = ImporterConfig(EmptyFieldMetaModel, creator=self.creator, minio=cast(Minio, self.minio))
        with self.assertRaises(ProgrammaticError) as cm:
            ExcelAlchemy(config)
        self.assertEqual(str(cm.exception), '字段定义必须是 FieldMeta 的实例')

    async def test_passing_non_config_object_raises_config_error(self):
        class NotImporterConfigModel(BaseModel):
            name: str = FieldMeta(label='姓名')

        with self.assertRaises(ConfigError) as cm:
            ExcelAlchemy(NotImporterConfigModel)

        self.assertEqual(str(cm.exception), '导出模式的配置类必须是 ExporterConfig')

    async def test_download_template_in_export_mode_raises_config_error(self):
        config = ExporterConfig(self.MergeHeaderImporter, minio=cast(Minio, self.minio))
        alchemy = ExcelAlchemy(config)

        with self.assertRaises(ConfigError) as cm:
            alchemy.download_template()

        self.assertEqual(str(cm.exception), '只支持导入模式调用此方法')
