from __future__ import annotations

from excelalchemy.adapters.pydantic import VALIDATION_MESSAGE_NORMALIZATION_POLICY
from excelalchemy.config import ImportMode
from excelalchemy.messages import (
    DISPLAY_LOCALE_POLICY,
    RUNTIME_LOCALE_POLICY,
    MessageKey,
    display_message,
    message,
)
from excelalchemy.policies import (
    EVENT_CALLBACK_FAILURE_POLICY,
    HEADER_HINT_LINE_COUNT,
    MERGED_HEADER_ROW_COUNT,
    MISSING_VALUE_IMPORT_POLICY,
    PAYLOAD_PATH_SEPARATOR,
    RESULT_WORKBOOK_POLICY,
    SIMPLE_HEADER_ROW_COUNT,
    WORKBOOK_UNIQUE_KEY_SEPARATOR,
    WORKBOOK_UNIQUE_LABEL_SEPARATOR,
    EventCallbackFailurePolicy,
    MissingValueImportAction,
)
from excelalchemy.primitives.constants import REASON_COLUMN_KEY, RESULT_COLUMN_KEY
from excelalchemy.primitives.identity import Label, UniqueLabel
from excelalchemy.results import (
    ImportCompletedEvent,
    ImportFailedEvent,
    ImportHeaderValidatedEvent,
    ImportLifecycleEvent,
    ImportLifecycleEventName,
    ImportRowProcessedEvent,
    ImportStartedEvent,
    ValidateResult,
)
from excelalchemy.util.file import flatten
from excelalchemy.worksheet.header import ExcelHeader


def test_v3_workbook_layout_policies_make_header_row_counts_explicit() -> None:
    assert HEADER_HINT_LINE_COUNT == 1
    assert SIMPLE_HEADER_ROW_COUNT == 1
    assert MERGED_HEADER_ROW_COUNT == 2


def test_v3_identity_and_payload_path_policies_make_separators_explicit() -> None:
    assert WORKBOOK_UNIQUE_LABEL_SEPARATOR == '·'
    assert WORKBOOK_UNIQUE_KEY_SEPARATOR == '·'
    assert PAYLOAD_PATH_SEPARATOR == '·'
    assert ExcelHeader(label=Label('Child'), parent_label=Label('Parent')).unique_label == UniqueLabel('Parent·Child')
    assert flatten({'employee': {'address': {'city': 'Shanghai'}}}) == {'employee·address·city': 'Shanghai'}


def test_v3_missing_value_import_policy_is_named_by_import_mode() -> None:
    assert MISSING_VALUE_IMPORT_POLICY.action_for_import_mode(ImportMode.CREATE) is MissingValueImportAction.OMIT_FIELD
    assert MISSING_VALUE_IMPORT_POLICY.action_for_import_mode(ImportMode.UPDATE) is MissingValueImportAction.USE_NONE
    assert (
        MISSING_VALUE_IMPORT_POLICY.action_for_import_mode(ImportMode.CREATE_OR_UPDATE)
        is MissingValueImportAction.USE_NONE
    )


def test_v3_result_workbook_policy_makes_column_identity_and_outcomes_explicit() -> None:
    assert [column.key for column in RESULT_WORKBOOK_POLICY.column_order] == [
        RESULT_COLUMN_KEY,
        REASON_COLUMN_KEY,
    ]
    assert [column.label_message_key for column in RESULT_WORKBOOK_POLICY.column_order] == [
        MessageKey.RESULT_COLUMN_LABEL,
        MessageKey.REASON_COLUMN_LABEL,
    ]
    assert RESULT_WORKBOOK_POLICY.header_invalid_uploads_result_workbook is False
    assert RESULT_WORKBOOK_POLICY.data_invalid_uploads_result_workbook is True


def test_v3_event_callback_failure_policy_is_named() -> None:
    assert EVENT_CALLBACK_FAILURE_POLICY is EventCallbackFailurePolicy.LOG_AND_CONTINUE


def test_v3_locale_fallback_policies_are_named() -> None:
    assert RUNTIME_LOCALE_POLICY.default_locale == 'en'
    assert RUNTIME_LOCALE_POLICY.missing_key_fallback_locale == 'en'
    assert DISPLAY_LOCALE_POLICY.default_locale == 'zh-CN'
    assert DISPLAY_LOCALE_POLICY.missing_key_fallback_locale == 'zh-CN'
    assert message(MessageKey.NO_STORAGE_BACKEND_CONFIGURED, locale='zh-CN').startswith('No storage backend')
    assert display_message(MessageKey.RESULT_COLUMN_LABEL, locale='unknown') == '校验结果\n重新上传前请删除此列'


def test_v3_validation_message_normalization_policy_is_named() -> None:
    assert VALIDATION_MESSAGE_NORMALIZATION_POLICY.required_message == 'Field required'
    assert 'Value error, ' in VALIDATION_MESSAGE_NORMALIZATION_POLICY.stripped_prefixes
    assert VALIDATION_MESSAGE_NORMALIZATION_POLICY.valid_dictionary_message == 'Input should be a valid dictionary'
    assert VALIDATION_MESSAGE_NORMALIZATION_POLICY.capitalize_unmapped_lowercase is True


def test_v3_import_lifecycle_events_are_typed_models() -> None:
    events: list[ImportLifecycleEvent] = [
        ImportStartedEvent(),
        ImportHeaderValidatedEvent(is_valid=True),
        ImportRowProcessedEvent(processed_row_count=1, total_row_count=1, success_count=1, fail_count=0),
        ImportCompletedEvent(result=ValidateResult.SUCCESS, success_count=1, fail_count=0),
        ImportFailedEvent(error_type='RuntimeError', error_message='boom'),
    ]

    assert [event.event for event in events] == [
        ImportLifecycleEventName.STARTED,
        ImportLifecycleEventName.HEADER_VALIDATED,
        ImportLifecycleEventName.ROW_PROCESSED,
        ImportLifecycleEventName.COMPLETED,
        ImportLifecycleEventName.FAILED,
    ]
    assert events[3].model_dump(mode='json', exclude_none=True) == {
        'event': 'completed',
        'result': 'SUCCESS',
        'success_count': 1,
        'fail_count': 0,
    }
