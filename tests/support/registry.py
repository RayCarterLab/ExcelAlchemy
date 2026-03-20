from enum import Enum


class FileRegistry(str, Enum):
    TEST_HEADER_INVALID_INPUT = 'test_header_invalid_input'
    TEST_BOOLEAN_INPUT = 'test_boolean_input'

    TEST_DATE_INPUT = 'test_date_input'
    TEST_DATE_INPUT_WRONG_RANGE = 'test_date_input_wrong_range'
    TEST_DATE_INPUT_WRONG_FORMAT = 'test_date_input_wrong_format'

    TEST_DATE_RANGE_INPUT = 'test_date_range_input'
    TEST_DATE_RANGE_MISSING_INPUT_BEFORE = 'test_date_range_missing_input_before'
    TEST_DATE_RANGE_MISSING_INPUT_AFTER = 'test_date_range_missing_input_after'

    TEST_EMAIL_WRONG_FORMAT = 'test_email_wrong_format'
    TEST_EMAIL_CORRECT_FORMAT = 'test_email_correct_format'

    TEST_SIMPLE_IMPORT = 'test_simple_import'
    TEST_SIMPLE_IMPORT_WITH_ERROR = 'test_simple_import_with_error'

    TEST_IMPORT_WITH_MERGE_HEADER = 'test_import_with_merge_header'
