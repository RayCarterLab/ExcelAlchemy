from contextlib import contextmanager
from contextvars import ContextVar
from enum import StrEnum
from typing import Final


class MessageKey(StrEnum):
    EXCEL_IMPORT_ERROR = 'excel_import_error'
    EXCEL_ROW_IMPORT_ERROR = 'excel_row_import_error'
    LABEL_CANNOT_BE_EMPTY = 'label_cannot_be_empty'
    MODEL_CANNOT_BE_NONE = 'model_cannot_be_none'
    UNSUPPORTED_FIELD_TYPE_DECLARATION = 'unsupported_field_type_declaration'
    THIS_FIELD_IS_REQUIRED = 'this_field_is_required'
    VALUE_TYPE_DECLARATION_UNSUPPORTED = 'value_type_declaration_unsupported'
    INVALID_INPUT = 'invalid_input'
    INVALID_IMPORT_MODE = 'invalid_import_mode'
    CREATE_IMPORTER_MODEL_REQUIRED_CREATE = 'create_importer_model_required_create'
    UPDATE_IMPORTER_MODEL_REQUIRED_UPDATE = 'update_importer_model_required_update'
    CREATE_IMPORTER_MODEL_REQUIRED_CREATE_OR_UPDATE = 'create_importer_model_required_create_or_update'
    UPDATE_IMPORTER_MODEL_REQUIRED_CREATE_OR_UPDATE = 'update_importer_model_required_create_or_update'
    IS_DATA_EXIST_REQUIRED_CREATE_OR_UPDATE = 'is_data_exist_required_create_or_update'
    IMPORTER_MODELS_FIELD_NAMES_MUST_MATCH = 'importer_models_field_names_must_match'
    EXPORTER_MODEL_CANNOT_BE_EMPTY = 'exporter_model_cannot_be_empty'
    IMPORT_MODE_CONFIG_REQUIRED = 'import_mode_config_required'
    EXPORT_MODE_CONFIG_REQUIRED = 'export_mode_config_required'
    NO_IMPORTER_OR_EXPORTER_MODEL_CONFIGURED = 'no_importer_or_exporter_model_configured'
    IMPORT_MODE_ONLY_METHOD = 'import_mode_only_method'
    IMPORT_MODE_ONLY_PROPERTY = 'import_mode_only_property'
    WORKSHEET_TABLE_NOT_LOADED = 'worksheet_table_not_loaded'
    EXPORTER_MODEL_INFERENCE_CONFLICT = 'exporter_model_inference_conflict'
    EXPORTER_MODEL_CANNOT_BE_INFERRED = 'exporter_model_cannot_be_inferred'
    CONFIG_ALREADY_INITIALIZED = 'config_already_initialized'
    UNSUPPORTED_IMPORT_MODE = 'unsupported_import_mode'
    CREATOR_NOT_CONFIGURED = 'creator_not_configured'
    CREATE_IMPORTER_MODEL_NOT_CONFIGURED = 'create_importer_model_not_configured'
    UPDATER_NOT_CONFIGURED = 'updater_not_configured'
    UPDATE_IMPORTER_MODEL_NOT_CONFIGURED = 'update_importer_model_not_configured'
    IS_DATA_EXIST_NOT_CONFIGURED = 'is_data_exist_not_configured'
    INVALID_MERGED_HEADER_CHILD_EMPTY = 'invalid_merged_header_child_empty'
    UNSUPPORTED_COLUMN_NAME = 'unsupported_column_name'
    FIELD_META_RUNTIME_KEY_MISSING = 'field_meta_runtime_key_missing'
    FIELD_NOT_FOUND = 'field_not_found'
    COLUMN_NOT_FOUND = 'column_not_found'
    NO_FIELD_METADATA_EXTRACTED = 'no_field_metadata_extracted'
    NO_FIELD_METADATA_EXTRACTED_FROM_MODEL = 'no_field_metadata_extracted_from_model'
    PARENT_LABEL_EMPTY_RUNTIME = 'parent_label_empty_runtime'
    PARENT_KEY_EMPTY_RUNTIME = 'parent_key_empty_runtime'
    KEY_EMPTY_RUNTIME = 'key_empty_runtime'
    DUPLICATE_FIELD_ORDER_DEFINITIONS = 'duplicate_field_order_definitions'
    INVALID_KEY = 'invalid_key'
    NO_STORAGE_BACKEND_CONFIGURED = 'no_storage_backend_configured'
    MINIO_CLIENT_NOT_CONFIGURED = 'minio_client_not_configured'
    WORKSHEET_NOT_FOUND = 'worksheet_not_found'
    PRIMARY_KEY_MUST_BE_UNIQUE = 'primary_key_must_be_unique'
    PRIMARY_KEY_AND_UNIQUE_MUST_BE_REQUIRED = 'primary_key_and_unique_must_be_required'
    OPTION_NOT_FOUND_HEADER_COMMENT = 'option_not_found_header_comment'
    OPTION_NOT_FOUND_FIELD_COMMENT = 'option_not_found_field_comment'
    DATE_FORMAT_EMPTY_RUNTIME = 'date_format_empty_runtime'
    FIELD_DEFINITIONS_MUST_USE_FIELDMETA = 'field_definitions_must_use_fieldmeta'
    FRACTION_DIGITS_MUST_BE_INTEGER = 'fraction_digits_must_be_integer'
    DATE_FORMAT_NOT_CONFIGURED = 'date_format_not_configured'
    ENTER_DATE_FORMAT = 'enter_date_format'
    DATE_MUST_BE_EARLIER_THAN_NOW = 'date_must_be_earlier_than_now'
    DATE_MUST_BE_LATER_THAN_NOW = 'date_must_be_later_than_now'
    DATE_RANGE_START_AFTER_END = 'date_range_start_after_end'
    VALID_EMAIL_REQUIRED = 'valid_email_required'
    INVALID_NUMBER_ENTER_NUMBER = 'invalid_number_enter_number'
    NUMBER_BETWEEN_MIN_AND_MAX = 'number_between_min_and_max'
    NUMBER_BETWEEN_NEG_INF_AND_MAX = 'number_between_neg_inf_and_max'
    NUMBER_BETWEEN_MIN_AND_POS_INF = 'number_between_min_and_pos_inf'
    NUMBER_RANGE_MIN_GREATER_THAN_MAX = 'number_range_min_greater_than_max'
    ENTER_NUMBER = 'enter_number'
    ENTER_NUMBER_EXPECTED_FORMAT = 'enter_number_expected_format'
    VALID_URL_REQUIRED = 'valid_url_required'
    VALID_PHONE_NUMBER_REQUIRED = 'valid_phone_number_required'
    MULTIPLE_SELECTIONS_NOT_SUPPORTED = 'multiple_selections_not_supported'
    OPTIONS_CANNOT_BE_NONE_FOR_SELECTION_FIELDS = 'options_cannot_be_none_for_selection_fields'
    OPTIONS_CANNOT_BE_NONE_FOR_VALUE_TYPE = 'options_cannot_be_none_for_value_type'
    OPTIONS_CONTAIN_DUPLICATES = 'options_contain_duplicates'
    CHARACTER_SET_NOT_CONFIGURED = 'character_set_not_configured'
    MAX_LENGTH_CHARACTERS = 'max_length_characters'
    ONLY_CHARACTER_SET_ALLOWED = 'only_character_set_allowed'
    IMPORT_RESULT_ONLY_FOR_INVALID_HEADER_VALIDATION = 'import_result_only_for_invalid_header_validation'
    BOOLEAN_ENTER_YES_OR_NO = 'boolean_enter_yes_or_no'
    BOOLEAN_TRUE_DISPLAY = 'boolean_true_display'
    BOOLEAN_FALSE_DISPLAY = 'boolean_false_display'
    CHARACTER_SET_NAME_CHINESE = 'character_set_name_chinese'
    CHARACTER_SET_NAME_NUMBER = 'character_set_name_number'
    CHARACTER_SET_NAME_LOWERCASE = 'character_set_name_lowercase'
    CHARACTER_SET_NAME_UPPERCASE = 'character_set_name_uppercase'
    CHARACTER_SET_NAME_SPECIAL = 'character_set_name_special'
    HEADER_HINT = 'header_hint'
    RESULT_COLUMN_LABEL = 'result_column_label'
    REASON_COLUMN_LABEL = 'reason_column_label'
    VALIDATE_ROW_SUCCESS = 'validate_row_success'
    VALIDATE_ROW_FAIL = 'validate_row_fail'
    COMMENT_REQUIRED = 'comment_required'
    COMMENT_DATE_FORMAT = 'comment_date_format'
    COMMENT_DATE_RANGE_OPTION = 'comment_date_range_option'
    COMMENT_HINT = 'comment_hint'
    COMMENT_OPTIONS = 'comment_options'
    COMMENT_FRACTION_DIGITS = 'comment_fraction_digits'
    COMMENT_UNIT = 'comment_unit'
    COMMENT_UNIQUE = 'comment_unique'
    COMMENT_MAX_LENGTH = 'comment_max_length'
    COMMENT_NUMBER_FORMAT = 'comment_number_format'
    COMMENT_NUMBER_INPUT_RANGE = 'comment_number_input_range'
    COMMENT_STRING_ALLOWED_CONTENT = 'comment_string_allowed_content'
    COMMENT_SELECTION_MODE = 'comment_selection_mode'
    COMMENT_REQUIRED_VALUE_REQUIRED = 'comment_required_value_required'
    COMMENT_REQUIRED_VALUE_OPTIONAL = 'comment_required_value_optional'
    COMMENT_UNIQUE_VALUE_UNIQUE = 'comment_unique_value_unique'
    COMMENT_UNIQUE_VALUE_NON_UNIQUE = 'comment_unique_value_non_unique'
    COMMENT_SELECTION_VALUE_SINGLE = 'comment_selection_value_single'
    COMMENT_SELECTION_VALUE_MULTI = 'comment_selection_value_multi'
    COMMENT_UNIT_VALUE_NONE = 'comment_unit_value_none'
    COMMENT_MAX_LENGTH_VALUE_UNLIMITED = 'comment_max_length_value_unlimited'
    COMMENT_DATE_RANGE_START_NOT_AFTER_END = 'comment_date_range_start_not_after_end'
    DATE_RANGE_OPTION_PRE_DISPLAY = 'date_range_option_pre_display'
    DATE_RANGE_OPTION_NEXT_DISPLAY = 'date_range_option_next_display'
    DATE_RANGE_OPTION_NONE_DISPLAY = 'date_range_option_none_display'
    SINGLE_ORGANIZATION_HINT = 'single_organization_hint'
    MULTI_ORGANIZATION_HINT = 'multi_organization_hint'
    SINGLE_STAFF_HINT = 'single_staff_hint'
    MULTI_STAFF_HINT = 'multi_staff_hint'
    SINGLE_TREE_HINT = 'single_tree_hint'
    MULTI_TREE_HINT = 'multi_tree_hint'
    LABEL_START_DATE = 'label_start_date'
    LABEL_END_DATE = 'label_end_date'
    LABEL_MINIMUM_VALUE = 'label_minimum_value'
    LABEL_MAXIMUM_VALUE = 'label_maximum_value'


DEFAULT_LOCALE: Final[str] = 'en'
DISPLAY_DEFAULT_LOCALE: Final[str] = 'zh-CN'
SUPPORTED_RUNTIME_LOCALES: Final[tuple[str, ...]] = (DEFAULT_LOCALE,)
SUPPORTED_DISPLAY_LOCALES: Final[tuple[str, ...]] = (DISPLAY_DEFAULT_LOCALE, 'en')
_current_display_locale: ContextVar[str] = ContextVar('excelalchemy_display_locale', default=DISPLAY_DEFAULT_LOCALE)

MESSAGES: Final[dict[str, dict[MessageKey, str]]] = {
    'en': {
        MessageKey.EXCEL_IMPORT_ERROR: 'Excel import error',
        MessageKey.EXCEL_ROW_IMPORT_ERROR: 'Excel row import error',
        MessageKey.LABEL_CANNOT_BE_EMPTY: 'label cannot be empty',
        MessageKey.MODEL_CANNOT_BE_NONE: 'model cannot be None',
        MessageKey.UNSUPPORTED_FIELD_TYPE_DECLARATION: 'Unsupported field type declaration: {annotation}',
        MessageKey.THIS_FIELD_IS_REQUIRED: 'This field is required',
        MessageKey.VALUE_TYPE_DECLARATION_UNSUPPORTED: (
            'Field definitions must use an ExcelFieldCodec or CompositeExcelFieldCodec subclass; {value_type} is not supported'
        ),
        MessageKey.INVALID_INPUT: 'Invalid input',
        MessageKey.INVALID_IMPORT_MODE: 'Invalid import mode: {import_mode}',
        MessageKey.CREATE_IMPORTER_MODEL_REQUIRED_CREATE: 'create_importer_model is required in CREATE mode',
        MessageKey.UPDATE_IMPORTER_MODEL_REQUIRED_UPDATE: 'update_importer_model is required in UPDATE mode',
        MessageKey.CREATE_IMPORTER_MODEL_REQUIRED_CREATE_OR_UPDATE: (
            'create_importer_model is required in CREATE_OR_UPDATE mode'
        ),
        MessageKey.UPDATE_IMPORTER_MODEL_REQUIRED_CREATE_OR_UPDATE: (
            'update_importer_model is required in CREATE_OR_UPDATE mode'
        ),
        MessageKey.IS_DATA_EXIST_REQUIRED_CREATE_OR_UPDATE: 'is_data_exist is required in CREATE_OR_UPDATE mode',
        MessageKey.IMPORTER_MODELS_FIELD_NAMES_MUST_MATCH: (
            'create and update importer models must define the same field names'
        ),
        MessageKey.EXPORTER_MODEL_CANNOT_BE_EMPTY: 'exporter_model cannot be empty',
        MessageKey.IMPORT_MODE_CONFIG_REQUIRED: 'Import mode requires an {config_name} instance',
        MessageKey.EXPORT_MODE_CONFIG_REQUIRED: 'Export mode requires an {config_name} instance',
        MessageKey.NO_IMPORTER_OR_EXPORTER_MODEL_CONFIGURED: 'No importer or exporter model is configured',
        MessageKey.IMPORT_MODE_ONLY_METHOD: 'This method is only available in import mode',
        MessageKey.IMPORT_MODE_ONLY_PROPERTY: 'This property is only available in import mode',
        MessageKey.WORKSHEET_TABLE_NOT_LOADED: 'The worksheet table must be loaded before accessing this property',
        MessageKey.EXPORTER_MODEL_INFERENCE_CONFLICT: (
            'Cannot infer exporter_model when both importer models are configured'
        ),
        MessageKey.EXPORTER_MODEL_CANNOT_BE_INFERRED: (
            'Could not infer exporter_model; please configure it explicitly'
        ),
        MessageKey.CONFIG_ALREADY_INITIALIZED: (
            '{class_name} has already been initialized; config cannot be reassigned'
        ),
        MessageKey.UNSUPPORTED_IMPORT_MODE: 'Unsupported import mode: {import_mode}',
        MessageKey.CREATOR_NOT_CONFIGURED: 'creator is not configured',
        MessageKey.CREATE_IMPORTER_MODEL_NOT_CONFIGURED: 'create_importer_model is not configured',
        MessageKey.UPDATER_NOT_CONFIGURED: 'updater is not configured',
        MessageKey.UPDATE_IMPORTER_MODEL_NOT_CONFIGURED: 'update_importer_model is not configured',
        MessageKey.IS_DATA_EXIST_NOT_CONFIGURED: 'is_data_exist is not configured',
        MessageKey.INVALID_MERGED_HEADER_CHILD_EMPTY: 'Invalid merged header: child header cannot be empty',
        MessageKey.UNSUPPORTED_COLUMN_NAME: 'Unsupported column name: {unique_label}',
        MessageKey.FIELD_META_RUNTIME_KEY_MISSING: '{field_meta_type} is missing runtime key/parent_key',
        MessageKey.FIELD_NOT_FOUND: 'Could not find a field for {unique_label}',
        MessageKey.COLUMN_NOT_FOUND: (
            'Could not find a column for {unique_label}; the codec definition may be invalid'
        ),
        MessageKey.NO_FIELD_METADATA_EXTRACTED: (
            'No field metadata was extracted; check whether the model defines any fields'
        ),
        MessageKey.NO_FIELD_METADATA_EXTRACTED_FROM_MODEL: (
            'No field metadata was extracted from model {model_name}; check its field definitions'
        ),
        MessageKey.PARENT_LABEL_EMPTY_RUNTIME: 'parent_label cannot be empty at runtime',
        MessageKey.PARENT_KEY_EMPTY_RUNTIME: 'parent_key cannot be empty at runtime',
        MessageKey.KEY_EMPTY_RUNTIME: 'key cannot be empty at runtime',
        MessageKey.DUPLICATE_FIELD_ORDER_DEFINITIONS: (
            'Duplicate field order definitions found: {duplicate_order}'
        ),
        MessageKey.INVALID_KEY: 'Invalid key: {key}',
        MessageKey.NO_STORAGE_BACKEND_CONFIGURED: (
            'No storage backend is configured; pass storage=... or install and configure ExcelAlchemy[minio]'
        ),
        MessageKey.MINIO_CLIENT_NOT_CONFIGURED: 'minio client is not configured',
        MessageKey.WORKSHEET_NOT_FOUND: 'Worksheet named {sheet_name!r} not found',
        MessageKey.PRIMARY_KEY_MUST_BE_UNIQUE: 'Primary key fields must be unique',
        MessageKey.PRIMARY_KEY_AND_UNIQUE_MUST_BE_REQUIRED: (
            'Primary key and unique fields must be required'
        ),
        MessageKey.OPTION_NOT_FOUND_HEADER_COMMENT: (
            'Option not found; check the header comment for valid values'
        ),
        MessageKey.OPTION_NOT_FOUND_FIELD_COMMENT: (
            'Option not found; check the field comment for valid values'
        ),
        MessageKey.DATE_FORMAT_EMPTY_RUNTIME: 'date_format cannot be empty at runtime',
        MessageKey.FIELD_DEFINITIONS_MUST_USE_FIELDMETA: (
            'Field definitions must be created with FieldMeta or Annotated[..., ExcelMeta(...)]'
        ),
        MessageKey.FRACTION_DIGITS_MUST_BE_INTEGER: 'fraction_digits must be an integer',
        MessageKey.DATE_FORMAT_NOT_CONFIGURED: 'date_format is not configured',
        MessageKey.ENTER_DATE_FORMAT: 'Enter a date in {date_format} format',
        MessageKey.DATE_MUST_BE_EARLIER_THAN_NOW: 'The value must be earlier than or equal to the current time',
        MessageKey.DATE_MUST_BE_LATER_THAN_NOW: 'The value must be later than or equal to the current time',
        MessageKey.DATE_RANGE_START_AFTER_END: 'The start date cannot be later than the end date',
        MessageKey.VALID_EMAIL_REQUIRED: 'Enter a valid email address',
        MessageKey.INVALID_NUMBER_ENTER_NUMBER: 'Invalid input; enter a number.',
        MessageKey.NUMBER_BETWEEN_MIN_AND_MAX: 'Enter a number between {minimum} and {maximum}.',
        MessageKey.NUMBER_BETWEEN_NEG_INF_AND_MAX: 'Enter a number between -∞ and {maximum}.',
        MessageKey.NUMBER_BETWEEN_MIN_AND_POS_INF: 'Enter a number between {minimum} and +∞.',
        MessageKey.NUMBER_RANGE_MIN_GREATER_THAN_MAX: 'The minimum value cannot be greater than the maximum value',
        MessageKey.ENTER_NUMBER: 'Enter a number',
        MessageKey.ENTER_NUMBER_EXPECTED_FORMAT: 'Enter a number in the expected format',
        MessageKey.VALID_URL_REQUIRED: 'Enter a valid URL',
        MessageKey.VALID_PHONE_NUMBER_REQUIRED: 'Enter a valid phone number',
        MessageKey.MULTIPLE_SELECTIONS_NOT_SUPPORTED: 'Multiple selections are not supported',
        MessageKey.OPTIONS_CANNOT_BE_NONE_FOR_SELECTION_FIELDS: (
            'options cannot be None when validating RADIO / MULTI_CHECKBOX / SELECT fields'
        ),
        MessageKey.OPTIONS_CANNOT_BE_NONE_FOR_VALUE_TYPE: 'options cannot be None when validating codec {value_type}',
        MessageKey.OPTIONS_CONTAIN_DUPLICATES: 'Options contain duplicates',
        MessageKey.CHARACTER_SET_NOT_CONFIGURED: 'character_set is not configured',
        MessageKey.MAX_LENGTH_CHARACTERS: 'The maximum length is {max_length} characters',
        MessageKey.ONLY_CHARACTER_SET_ALLOWED: 'Only {character_set_names} are allowed',
        MessageKey.IMPORT_RESULT_ONLY_FOR_INVALID_HEADER_VALIDATION: (
            'ImportResult can only be built from an invalid header validation result'
        ),
        MessageKey.BOOLEAN_ENTER_YES_OR_NO: 'Enter "{true_value}" or "{false_value}"',
        MessageKey.BOOLEAN_TRUE_DISPLAY: 'Yes',
        MessageKey.BOOLEAN_FALSE_DISPLAY: 'No',
        MessageKey.CHARACTER_SET_NAME_CHINESE: 'Chinese characters',
        MessageKey.CHARACTER_SET_NAME_NUMBER: 'numbers',
        MessageKey.CHARACTER_SET_NAME_LOWERCASE: 'lowercase letters',
        MessageKey.CHARACTER_SET_NAME_UPPERCASE: 'uppercase letters',
        MessageKey.CHARACTER_SET_NAME_SPECIAL: 'symbols',
        MessageKey.HEADER_HINT: (
            'Import instructions:\n'
            '1. Review the header comments before filling in data to avoid import failures.\n'
            '2. Some columns may be read-only and generated by system rules; they are shown for export only and ignored on import.\n'
            '3. Columns with a red background are required and must be filled according to the header comment.\n'
            '4. Do not change the cell format of any column to avoid validation failures.\n'
            '5. Remove the sample rows before importing.'
        ),
        MessageKey.RESULT_COLUMN_LABEL: 'Validation result\nDelete this column before re-uploading',
        MessageKey.REASON_COLUMN_LABEL: 'Failure reason\nDelete this column before re-uploading',
        MessageKey.VALIDATE_ROW_SUCCESS: 'Validation passed',
        MessageKey.VALIDATE_ROW_FAIL: 'Validation failed',
        MessageKey.COMMENT_REQUIRED: 'Required: {value}',
        MessageKey.COMMENT_DATE_FORMAT: 'Format: date ({value})',
        MessageKey.COMMENT_DATE_RANGE_OPTION: 'Range: {value}',
        MessageKey.COMMENT_HINT: 'Hint: {value}',
        MessageKey.COMMENT_OPTIONS: 'Options: {value}',
        MessageKey.COMMENT_FRACTION_DIGITS: 'Fraction digits: {value}',
        MessageKey.COMMENT_UNIT: 'Unit: {value}',
        MessageKey.COMMENT_UNIQUE: 'Uniqueness: {value}',
        MessageKey.COMMENT_MAX_LENGTH: 'Max length: {value}',
        MessageKey.COMMENT_NUMBER_FORMAT: 'Format: number',
        MessageKey.COMMENT_NUMBER_INPUT_RANGE: 'Allowed range: {value}',
        MessageKey.COMMENT_STRING_ALLOWED_CONTENT: 'Allowed content: Chinese characters, numbers, uppercase letters, lowercase letters, symbols',
        MessageKey.COMMENT_SELECTION_MODE: 'Selection mode: {value}',
        MessageKey.COMMENT_REQUIRED_VALUE_REQUIRED: 'required',
        MessageKey.COMMENT_REQUIRED_VALUE_OPTIONAL: 'optional',
        MessageKey.COMMENT_UNIQUE_VALUE_UNIQUE: 'unique',
        MessageKey.COMMENT_UNIQUE_VALUE_NON_UNIQUE: 'not unique',
        MessageKey.COMMENT_SELECTION_VALUE_SINGLE: 'single',
        MessageKey.COMMENT_SELECTION_VALUE_MULTI: 'multiple',
        MessageKey.COMMENT_UNIT_VALUE_NONE: 'none',
        MessageKey.COMMENT_MAX_LENGTH_VALUE_UNLIMITED: 'unlimited',
        MessageKey.COMMENT_DATE_RANGE_START_NOT_AFTER_END: 'Hint: the start date cannot be later than the end date{extra_hint}',
        MessageKey.DATE_RANGE_OPTION_PRE_DISPLAY: 'earlier than the current time',
        MessageKey.DATE_RANGE_OPTION_NEXT_DISPLAY: 'later than the current time',
        MessageKey.DATE_RANGE_OPTION_NONE_DISPLAY: 'unlimited',
        MessageKey.SINGLE_ORGANIZATION_HINT: "Enter the full organization path, for example 'Company/Department/Sub-department'.",
        MessageKey.MULTI_ORGANIZATION_HINT: (
            "Enter the full organization path, for example 'Company/Department/Sub-department'. "
            'Use "、" to separate multiple selections.'
        ),
        MessageKey.SINGLE_STAFF_HINT: 'Enter the staff name and employee ID, for example "Zhang San/001".',
        MessageKey.MULTI_STAFF_HINT: (
            'Enter the staff name and employee ID, for example "Zhang San/001". '
            'Use "、" to separate multiple selections.'
        ),
        MessageKey.SINGLE_TREE_HINT: (
            'Enter the full tree path, for example "Company/Department/Sub-department".'
        ),
        MessageKey.MULTI_TREE_HINT: (
            'Enter the full path including the root node. Use "/" between levels, for example '
            '"Level 1/Level 2/Option 1". Use "，" to separate multiple selections.'
        ),
        MessageKey.LABEL_START_DATE: 'Start date',
        MessageKey.LABEL_END_DATE: 'End date',
        MessageKey.LABEL_MINIMUM_VALUE: 'Minimum value',
        MessageKey.LABEL_MAXIMUM_VALUE: 'Maximum value',
    },
    'zh-CN': {
        MessageKey.HEADER_HINT: (
            '\n导入填写须知：\n'
            '1、填写数据时，请注意查看字段名称上的注释，避免导入失败。\n'
            '2、表格中可能包含部分只读字段，可能是根据系统规则自动生成或是在编辑时禁止被修改，仅用于导出时查看，导入时不生效。\n'
            '3、字段名称背景是红色的为必填字段，导入时必须根据注释的提示填写好内容。\n'
            '4、请不要随意修改列的单元格格式，避免模板校验不通过。\n'
            '5、导入前请删除示例数据。\n'
        ),
        MessageKey.RESULT_COLUMN_LABEL: '校验结果\n重新上传前请删除此列',
        MessageKey.REASON_COLUMN_LABEL: '失败原因\n重新上传前请删除此列',
        MessageKey.VALIDATE_ROW_SUCCESS: '校验通过',
        MessageKey.VALIDATE_ROW_FAIL: '校验不通过',
        MessageKey.COMMENT_REQUIRED: '必填性：{value}',
        MessageKey.COMMENT_DATE_FORMAT: '格式：日期（{value}）',
        MessageKey.COMMENT_DATE_RANGE_OPTION: '范围：{value}',
        MessageKey.COMMENT_HINT: '提示：{value}',
        MessageKey.COMMENT_OPTIONS: '选项：{value}',
        MessageKey.COMMENT_FRACTION_DIGITS: '小数位数：{value}',
        MessageKey.COMMENT_UNIT: '单位：{value}',
        MessageKey.COMMENT_UNIQUE: '唯一性：{value}',
        MessageKey.COMMENT_MAX_LENGTH: '最大长度：{value}',
        MessageKey.COMMENT_NUMBER_FORMAT: '格式：数值',
        MessageKey.COMMENT_NUMBER_INPUT_RANGE: '可输入范围：{value}',
        MessageKey.COMMENT_STRING_ALLOWED_CONTENT: '可输入内容:中文、数字、大写字母、小写字母、符号',
        MessageKey.COMMENT_SELECTION_MODE: '单/多选：{value}',
        MessageKey.COMMENT_REQUIRED_VALUE_REQUIRED: '必填',
        MessageKey.COMMENT_REQUIRED_VALUE_OPTIONAL: '选填',
        MessageKey.COMMENT_UNIQUE_VALUE_UNIQUE: '唯一',
        MessageKey.COMMENT_UNIQUE_VALUE_NON_UNIQUE: '非唯一',
        MessageKey.COMMENT_SELECTION_VALUE_SINGLE: '单选',
        MessageKey.COMMENT_SELECTION_VALUE_MULTI: '多选',
        MessageKey.COMMENT_UNIT_VALUE_NONE: '无',
        MessageKey.COMMENT_MAX_LENGTH_VALUE_UNLIMITED: '无限制',
        MessageKey.COMMENT_DATE_RANGE_START_NOT_AFTER_END: '提示：开始日期不得晚于结束日期{extra_hint}',
        MessageKey.DATE_RANGE_OPTION_PRE_DISPLAY: '早于当前时间',
        MessageKey.DATE_RANGE_OPTION_NEXT_DISPLAY: '晚于当前时间',
        MessageKey.DATE_RANGE_OPTION_NONE_DISPLAY: '无限制',
        MessageKey.BOOLEAN_TRUE_DISPLAY: '是',
        MessageKey.BOOLEAN_FALSE_DISPLAY: '否',
        MessageKey.SINGLE_ORGANIZATION_HINT: "需按照组织架构树填写组织完整路径，例如 'XX公司/一级部门/二级部门'.",
        MessageKey.MULTI_ORGANIZATION_HINT: '需按照组织架构树填写组织完整路径，如“XX公司/一级部门/二级部门”，多选时，选项之间用“、”连接',
        MessageKey.SINGLE_STAFF_HINT: '请输入人员姓名和工号，如“张三/001”',
        MessageKey.MULTI_STAFF_HINT: '请输入人员姓名和工号，如“张三/001”，多选时，选项之间用“、”连接',
        MessageKey.SINGLE_TREE_HINT: '需按照组织架构树填写组织完整路径，如“XX公司/一级部门/二级部门”，多选时，选项之间用“、”连接',
        MessageKey.MULTI_TREE_HINT: '请输入完整路径（包含根节点），层级之间用“/”连接，如“一级/二级/选项1”；多选时，选项之间用“，”连接',
        MessageKey.LABEL_START_DATE: '开始日期',
        MessageKey.LABEL_END_DATE: '结束日期',
        MessageKey.LABEL_MINIMUM_VALUE: '最小值',
        MessageKey.LABEL_MAXIMUM_VALUE: '最大值',
    }
}


def message(key: MessageKey, locale: str = DEFAULT_LOCALE, **kwargs: object) -> str:
    locale_messages = MESSAGES.get(locale, MESSAGES[DEFAULT_LOCALE])
    template = locale_messages.get(key) or MESSAGES[DEFAULT_LOCALE][key]
    return template.format(**kwargs)


def get_display_locale() -> str:
    return _current_display_locale.get()


@contextmanager
def use_display_locale(locale: str):
    token = _current_display_locale.set(locale)
    try:
        yield
    finally:
        _current_display_locale.reset(token)


def display_message(key: MessageKey, locale: str | None = None, **kwargs: object) -> str:
    effective_locale = locale or get_display_locale()
    locale_messages = MESSAGES.get(effective_locale, MESSAGES[DISPLAY_DEFAULT_LOCALE])
    template = locale_messages.get(key) or MESSAGES[DISPLAY_DEFAULT_LOCALE][key]
    return template.format(**kwargs)
