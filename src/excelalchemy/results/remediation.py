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


@dataclass(slots=True, frozen=True)
class LocalizedRemediationHint:
    """Remediation hint text with English runtime fallback."""

    en: RemediationHint
    zh_cn: RemediationHint | None = None
    ja: RemediationHint | None = None

    def for_locale(self, locale: str | None) -> RemediationHint:
        match locale:
            case 'zh-CN':
                return self.zh_cn or self.en
            case 'ja':
                return self.ja or self.en
            case _:
                return self.en


def _localized_hint(
    *,
    en: RemediationHint,
    zh_cn: RemediationHint | None = None,
    ja: RemediationHint | None = None,
) -> LocalizedRemediationHint:
    return LocalizedRemediationHint(en=en, zh_cn=zh_cn, ja=ja)


_REMEDIATION_HINTS_BY_MESSAGE_KEY: dict[MessageKey, LocalizedRemediationHint] = {
    MessageKey.VALID_EMAIL_REQUIRED: _localized_hint(
        en=RemediationHint(
            suggested_action='Enter a complete email address and re-upload the workbook.',
            fix_hint='Use a format such as name@example.com.',
        ),
        zh_cn=RemediationHint(
            suggested_action='请输入完整的邮箱地址后重新上传工作簿。',
            fix_hint='使用类似 name@example.com 的格式。',
        ),
        ja=RemediationHint(
            suggested_action='完全なメールアドレスを入力してワークブックを再アップロードしてください。',
            fix_hint='name@example.com のような形式を使用してください。',
        ),
    ),
    MessageKey.INVALID_NUMBER_ENTER_NUMBER: _localized_hint(
        en=RemediationHint(
            suggested_action='Replace the invalid value with a numeric value and re-upload the workbook.',
            fix_hint='Use digits only and avoid free-text values in this cell.',
        ),
        zh_cn=RemediationHint(
            suggested_action='请将无效值替换为数字后重新上传工作簿。',
            fix_hint='此单元格仅填写数字，避免输入自由文本。',
        ),
        ja=RemediationHint(
            suggested_action='無効な値を数値に置き換えてワークブックを再アップロードしてください。',
            fix_hint='このセルには数字のみを入力し、自由記述のテキストは避けてください。',
        ),
    ),
    MessageKey.ENTER_NUMBER: _localized_hint(
        en=RemediationHint(
            suggested_action='Enter a numeric value and re-upload the workbook.',
            fix_hint='Use digits only and avoid leaving the field as free text.',
        ),
        zh_cn=RemediationHint(
            suggested_action='请输入数字后重新上传工作簿。',
            fix_hint='仅填写数字，避免将字段保留为自由文本。',
        ),
        ja=RemediationHint(
            suggested_action='数値を入力してワークブックを再アップロードしてください。',
            fix_hint='数字のみを入力し、自由記述のテキストは避けてください。',
        ),
    ),
    MessageKey.ENTER_NUMBER_EXPECTED_FORMAT: _localized_hint(
        en=RemediationHint(
            suggested_action='Correct the cell value to the expected numeric format and re-upload the workbook.',
            fix_hint='Match the number format shown in the workbook guidance.',
        ),
        zh_cn=RemediationHint(
            suggested_action='请将单元格值修正为要求的数字格式后重新上传工作簿。',
            fix_hint='按照工作簿提示中的数字格式填写。',
        ),
        ja=RemediationHint(
            suggested_action='セルの値を期待される数値形式に修正してワークブックを再アップロードしてください。',
            fix_hint='ワークブックの案内に示された数値形式に合わせてください。',
        ),
    ),
    MessageKey.VALID_URL_REQUIRED: _localized_hint(
        en=RemediationHint(
            suggested_action='Enter a complete URL and re-upload the workbook.',
            fix_hint='Use a format such as https://example.com.',
        ),
        zh_cn=RemediationHint(
            suggested_action='请输入完整的网址后重新上传工作簿。',
            fix_hint='使用类似 https://example.com 的格式。',
        ),
        ja=RemediationHint(
            suggested_action='完全な URL を入力してワークブックを再アップロードしてください。',
            fix_hint='https://example.com のような形式を使用してください。',
        ),
    ),
    MessageKey.VALID_PHONE_NUMBER_REQUIRED: _localized_hint(
        en=RemediationHint(
            suggested_action='Enter a valid phone number and re-upload the workbook.',
            fix_hint='Use the expected phone number format for this field.',
        ),
        zh_cn=RemediationHint(
            suggested_action='请输入有效手机号后重新上传工作簿。',
            fix_hint='按照该字段要求的手机号格式填写。',
        ),
        ja=RemediationHint(
            suggested_action='有効な電話番号を入力してワークブックを再アップロードしてください。',
            fix_hint='この項目で求められる電話番号形式を使用してください。',
        ),
    ),
    MessageKey.THIS_FIELD_IS_REQUIRED: _localized_hint(
        en=RemediationHint(
            suggested_action='Fill in the required field and re-upload the workbook.',
            fix_hint='Required fields cannot be left blank.',
        ),
        zh_cn=RemediationHint(
            suggested_action='请填写必填字段后重新上传工作簿。',
            fix_hint='必填字段不能为空。',
        ),
        ja=RemediationHint(
            suggested_action='必須項目を入力してワークブックを再アップロードしてください。',
            fix_hint='必須項目は空欄にできません。',
        ),
    ),
}

_REMEDIATION_HINTS_BY_CODE: dict[str, LocalizedRemediationHint] = {
    'ExcelCellError': _localized_hint(
        en=RemediationHint(
            suggested_action='Review the highlighted cells, correct the invalid values, and re-upload the workbook.'
        ),
        zh_cn=RemediationHint(suggested_action='请查看高亮单元格，修正无效值后重新上传工作簿。'),
        ja=RemediationHint(
            suggested_action='強調表示されたセルを確認し、無効な値を修正してワークブックを再アップロードしてください。'
        ),
    ),
    'ExcelRowError': _localized_hint(
        en=RemediationHint(
            suggested_action='Review the row-level validation message, correct the row, and re-upload the workbook.'
        ),
        zh_cn=RemediationHint(suggested_action='请查看行级校验信息，修正该行后重新上传工作簿。'),
        ja=RemediationHint(
            suggested_action='行レベルの検証メッセージを確認し、行を修正してワークブックを再アップロードしてください。'
        ),
    ),
}


def _merge_remediation_hints(*hints: RemediationHint) -> RemediationHint:
    for hint in hints:
        if hint.suggested_action is not None or hint.fix_hint is not None:
            return hint
    return RemediationHint()


def _hint_for_issue(error: RowIssue, *, locale: str | None) -> RemediationHint:
    message_hint_catalog = (
        _REMEDIATION_HINTS_BY_MESSAGE_KEY.get(error.message_key) if error.message_key is not None else None
    )
    message_hint = message_hint_catalog.for_locale(locale) if message_hint_catalog is not None else None
    code_hint = (
        _REMEDIATION_HINTS_BY_CODE[error.code].for_locale(locale) if error.code in _REMEDIATION_HINTS_BY_CODE else None
    )
    return _merge_remediation_hints(message_hint or RemediationHint(), code_hint or RemediationHint())


def _hint_for_issues(errors: Iterable[RowIssue], *, locale: str | None) -> RemediationHint:
    for error in errors:
        hint = _hint_for_issue(error, locale=locale)
        if hint.suggested_action is not None or hint.fix_hint is not None:
            return hint
    return RemediationHint()


def _top_level_remediation_hint(result: 'ImportResult', *, locale: str | None) -> RemediationHint:
    if result.is_success:
        return RemediationHint()
    if result.is_header_invalid:
        return _localized_hint(
            en=RemediationHint(
                suggested_action='Correct the workbook headers to match the template and retry the import.',
                fix_hint='Use a fresh template or align missing, duplicated, and unrecognized headers before retrying.',
            ),
            zh_cn=RemediationHint(
                suggested_action='请修正工作簿表头，使其与模板一致后重新导入。',
                fix_hint='使用新的模板，或在重试前修正缺失、重复和无法识别的表头。',
            ),
            ja=RemediationHint(
                suggested_action='ワークブックのヘッダーをテンプレートに合わせて修正し、インポートを再試行してください。',
                fix_hint='新しいテンプレートを使用するか、再試行前に不足、重複、未認識のヘッダーを修正してください。',
            ),
        ).for_locale(locale)
    if result.is_data_invalid:
        if result.url is not None:
            return _localized_hint(
                en=RemediationHint(
                    suggested_action='Correct the invalid rows and re-upload the workbook.',
                    fix_hint='Download the result workbook and review the highlighted rows before re-uploading.',
                ),
                zh_cn=RemediationHint(
                    suggested_action='请修正无效行后重新上传工作簿。',
                    fix_hint='下载结果工作簿，并在重新上传前查看高亮行。',
                ),
                ja=RemediationHint(
                    suggested_action='無効な行を修正してワークブックを再アップロードしてください。',
                    fix_hint='結果ワークブックをダウンロードし、再アップロード前に強調表示された行を確認してください。',
                ),
            ).for_locale(locale)
        return _localized_hint(
            en=RemediationHint(
                suggested_action='Correct the invalid rows and re-upload the workbook.',
                fix_hint='Review the invalid rows and field messages before re-uploading.',
            ),
            zh_cn=RemediationHint(
                suggested_action='请修正无效行后重新上传工作簿。',
                fix_hint='重新上传前请查看无效行和字段错误信息。',
            ),
            ja=RemediationHint(
                suggested_action='無効な行を修正してワークブックを再アップロードしてください。',
                fix_hint='再アップロード前に無効な行と項目メッセージを確認してください。',
            ),
        ).for_locale(locale)
    return RemediationHint()


def _with_remediation_fields(payload: dict[str, object], hint: RemediationHint) -> dict[str, object]:
    payload.update(hint.to_dict())
    return payload


def build_frontend_remediation_payload(
    *,
    result: ImportResult,
    cell_error_map: CellErrorMap,
    row_error_map: RowIssueMap,
    locale: str | None = None,
) -> dict[str, object]:
    """Build a compact, remediation-oriented payload for frontend workflows."""

    effective_locale = locale or 'en'
    row_records = row_error_map.records()
    cell_records = cell_error_map.records()
    top_level_hint = _top_level_remediation_hint(result, locale=effective_locale)

    by_field: list[dict[str, object]] = []
    for summary in cell_error_map.summary_by_field():
        summary_payload = summary.to_dict()
        matching_errors = tuple(
            record.error for record in cell_records if str(record.error.unique_label) == summary.unique_label
        )
        by_field.append(
            _with_remediation_fields(summary_payload, _hint_for_issues(matching_errors, locale=effective_locale))
        )

    by_code: list[dict[str, object]] = []
    for summary in row_error_map.summary_by_code():
        summary_payload = summary.to_dict()
        matching_errors = tuple(record.error for record in row_records if record.error.code == summary.code)
        by_code.append(
            _with_remediation_fields(summary_payload, _hint_for_issues(matching_errors, locale=effective_locale))
        )

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
        items.append(_with_remediation_fields(item_payload, _hint_for_issue(record.error, locale=effective_locale)))

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
        items.append(_with_remediation_fields(item_payload, _hint_for_issue(record.error, locale=effective_locale)))

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
