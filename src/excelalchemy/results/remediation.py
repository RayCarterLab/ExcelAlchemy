"""Frontend-oriented import remediation payload helpers."""

from collections.abc import Iterable
from dataclasses import dataclass

from excelalchemy.errors import ExcelCellError
from excelalchemy.messages import MessageKey
from excelalchemy.results.import_result import ImportResult
from excelalchemy.results.issue_maps import (
    CellErrorMap,
    RowIssue,
    RowIssueMap,
    column_number_for_humans,
    row_number_for_humans,
)


@dataclass(slots=True, frozen=True)
class RemediationHint:
    """Optional remediation hint data for frontend-oriented payloads."""

    suggested_action: str | None = None
    fix_hint: str | None = None

    def to_dict(self) -> dict[str, str]:
        payload: dict[str, str] = {}
        if self.suggested_action is not None:
            payload['suggested_action'] = self.suggested_action
        if self.fix_hint is not None:
            payload['fix_hint'] = self.fix_hint
        return payload


_REMEDIATION_HINTS_BY_MESSAGE_KEY: dict[MessageKey, RemediationHint] = {
    MessageKey.VALID_EMAIL_REQUIRED: RemediationHint(
        suggested_action='Enter a complete email address and re-upload the workbook.',
        fix_hint='Use a format such as name@example.com.',
    ),
    MessageKey.INVALID_NUMBER_ENTER_NUMBER: RemediationHint(
        suggested_action='Replace the invalid value with a numeric value and re-upload the workbook.',
        fix_hint='Use digits only and avoid free-text values in this cell.',
    ),
    MessageKey.ENTER_NUMBER: RemediationHint(
        suggested_action='Enter a numeric value and re-upload the workbook.',
        fix_hint='Use digits only and avoid leaving the field as free text.',
    ),
    MessageKey.ENTER_NUMBER_EXPECTED_FORMAT: RemediationHint(
        suggested_action='Correct the cell value to the expected numeric format and re-upload the workbook.',
        fix_hint='Match the number format shown in the workbook guidance.',
    ),
    MessageKey.VALID_URL_REQUIRED: RemediationHint(
        suggested_action='Enter a complete URL and re-upload the workbook.',
        fix_hint='Use a format such as https://example.com.',
    ),
    MessageKey.VALID_PHONE_NUMBER_REQUIRED: RemediationHint(
        suggested_action='Enter a valid phone number and re-upload the workbook.',
        fix_hint='Use the expected phone number format for this field.',
    ),
    MessageKey.THIS_FIELD_IS_REQUIRED: RemediationHint(
        suggested_action='Fill in the required field and re-upload the workbook.',
        fix_hint='Required fields cannot be left blank.',
    ),
}

_REMEDIATION_HINTS_BY_CODE: dict[str, RemediationHint] = {
    'ExcelCellError': RemediationHint(
        suggested_action='Review the highlighted cells, correct the invalid values, and re-upload the workbook.'
    ),
    'ExcelRowError': RemediationHint(
        suggested_action='Review the row-level validation message, correct the row, and re-upload the workbook.'
    ),
}


def _merge_remediation_hints(*hints: RemediationHint) -> RemediationHint:
    for hint in hints:
        if hint.suggested_action is not None or hint.fix_hint is not None:
            return hint
    return RemediationHint()


def _hint_for_issue(error: RowIssue) -> RemediationHint:
    message_hint = _REMEDIATION_HINTS_BY_MESSAGE_KEY.get(error.message_key) if error.message_key is not None else None
    code_hint = _REMEDIATION_HINTS_BY_CODE.get(error.code)
    return _merge_remediation_hints(message_hint or RemediationHint(), code_hint or RemediationHint())


def _hint_for_issues(errors: Iterable[RowIssue]) -> RemediationHint:
    for error in errors:
        hint = _hint_for_issue(error)
        if hint.suggested_action is not None or hint.fix_hint is not None:
            return hint
    return RemediationHint()


def _top_level_remediation_hint(result: 'ImportResult') -> RemediationHint:
    if result.is_success:
        return RemediationHint()
    if result.is_header_invalid:
        return RemediationHint(
            suggested_action='Correct the workbook headers to match the template and retry the import.',
            fix_hint='Use a fresh template or align missing, duplicated, and unrecognized headers before retrying.',
        )
    if result.is_data_invalid:
        fix_hint = (
            'Download the result workbook and review the highlighted rows before re-uploading.'
            if result.url is not None
            else 'Review the invalid rows and field messages before re-uploading.'
        )
        return RemediationHint(
            suggested_action='Correct the invalid rows and re-upload the workbook.',
            fix_hint=fix_hint,
        )
    return RemediationHint()


def _with_remediation_fields(payload: dict[str, object], hint: RemediationHint) -> dict[str, object]:
    payload.update(hint.to_dict())
    return payload


def build_frontend_remediation_payload(
    *,
    result: ImportResult,
    cell_error_map: CellErrorMap,
    row_error_map: RowIssueMap,
) -> dict[str, object]:
    """Build a compact, remediation-oriented payload for frontend workflows."""

    row_records = row_error_map.records()
    cell_records = cell_error_map.records()
    top_level_hint = _top_level_remediation_hint(result)

    by_field: list[dict[str, object]] = []
    for summary in cell_error_map.summary_by_field():
        summary_payload = summary.to_dict()
        matching_errors = tuple(
            record.error for record in cell_records if str(record.error.unique_label) == summary.unique_label
        )
        by_field.append(_with_remediation_fields(summary_payload, _hint_for_issues(matching_errors)))

    by_code: list[dict[str, object]] = []
    for summary in row_error_map.summary_by_code():
        summary_payload = summary.to_dict()
        matching_errors = tuple(record.error for record in row_records if record.error.code == summary.code)
        by_code.append(_with_remediation_fields(summary_payload, _hint_for_issues(matching_errors)))

    items: list[dict[str, object]] = []
    for record in cell_records:
        item_payload: dict[str, object] = {
            'scope': 'cell',
            'code': record.error.code,
            'message': record.error.message,
            'display_message': record.error.display_message,
            'row_index': int(record.row_index),
            'row_number_for_humans': row_number_for_humans(record.row_index),
            'column_index': int(record.column_index),
            'column_number_for_humans': column_number_for_humans(record.column_index),
            'field_label': str(record.error.label),
            'parent_label': None if record.error.parent_label is None else str(record.error.parent_label),
            'unique_label': str(record.error.unique_label),
        }
        if record.error.message_key is not None:
            item_payload['message_key'] = record.error.message_key.value
        items.append(_with_remediation_fields(item_payload, _hint_for_issue(record.error)))

    for record in row_records:
        if isinstance(record.error, ExcelCellError):
            continue
        item_payload: dict[str, object] = {
            'scope': 'row',
            'code': record.error.code,
            'message': record.error.message,
            'display_message': record.error.display_message,
            'row_index': int(record.row_index),
            'row_number_for_humans': row_number_for_humans(record.row_index),
        }
        if record.error.message_key is not None:
            item_payload['message_key'] = record.error.message_key.value
        items.append(_with_remediation_fields(item_payload, _hint_for_issue(record.error)))

    remediation_summary: dict[str, object] = {
        'needs_remediation': not result.is_success,
        'affected_row_count': len(row_error_map.summary_by_row()),
        'affected_field_count': len(cell_error_map.summary_by_field()),
        'affected_code_count': len(row_error_map.summary_by_code()),
        'header_issue_count': (
            len(result.missing_required)
            + len(result.missing_primary)
            + len(result.unrecognized)
            + len(result.duplicated)
        ),
        'result_workbook_available': result.url is not None,
    }
    _with_remediation_fields(remediation_summary, top_level_hint)

    return {
        'result': result.to_api_payload(),
        'remediation': remediation_summary,
        'by_field': by_field,
        'by_code': by_code,
        'items': items,
    }
