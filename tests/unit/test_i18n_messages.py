from typing import Annotated

from pydantic import BaseModel

from excelalchemy import (
    DateCodec,
    DateFormat,
    EmailCodec,
    ExcelColumn,
)
from excelalchemy.adapters.pydantic import instantiate_pydantic_model
from excelalchemy.adapters.pydantic_fields import extract_declared_field_metadata
from excelalchemy.messages import (
    DISPLAY_DEFAULT_LOCALE,
    MESSAGES,
    SUPPORTED_DISPLAY_LOCALES,
    SUPPORTED_RUNTIME_LOCALES,
    MessageKey,
    display_message,
    message,
    use_display_locale,
)
from excelalchemy.results import ValidateRowResult


class TestI18nMessages:
    def test_message_formats_templates(self):
        assert message(MessageKey.ENTER_DATE_FORMAT, date_format='yyyy/mm/dd') == 'Enter a date in yyyy/mm/dd format'

    def test_message_falls_back_to_default_locale(self):
        assert (
            message(MessageKey.NO_STORAGE_BACKEND_CONFIGURED, locale='zh-CN')
            == 'No storage backend is configured; pass storage=... or install and configure ExcelAlchemy[minio]'
        )
        assert message(MessageKey.VALID_EMAIL_REQUIRED, locale='ja') == (
            'Enter a valid email address, such as name@example.com'
        )

    def test_display_message_uses_context_locale(self):
        with use_display_locale('en'):
            assert (
                display_message(MessageKey.RESULT_COLUMN_LABEL)
                == 'Validation result\nDelete this column before re-uploading'
            )
            assert str(ValidateRowResult.FAIL) == 'Validation failed'

    def test_public_locale_policy_constants_are_stable(self):
        assert SUPPORTED_RUNTIME_LOCALES == ('en',)
        assert SUPPORTED_DISPLAY_LOCALES == ('zh-CN', 'en', 'ja')
        assert DISPLAY_DEFAULT_LOCALE == 'zh-CN'

    def test_japanese_display_messages_are_supported(self):
        with use_display_locale('ja'):
            assert (
                display_message(MessageKey.RESULT_COLUMN_LABEL)
                == '検証結果\n再アップロード前にこの列を削除してください'
            )
            assert str(ValidateRowResult.FAIL) == '検証に失敗しました'
            assert display_message(MessageKey.THIS_FIELD_IS_REQUIRED) == 'この項目は必須です'

    def test_japanese_display_catalog_matches_chinese_display_coverage(self):
        assert set(MESSAGES['ja']) == set(MESSAGES['zh-CN'])

    def test_user_validation_messages_keep_english_message_and_localized_display_message(self):
        class Importer(BaseModel):
            email: Annotated[str, ExcelColumn(codec=EmailCodec(), label='Email', order=1)]

        with use_display_locale('ja'):
            result = instantiate_pydantic_model({'email': 'not-an-email'}, Importer)

        assert isinstance(result, list)
        assert result[0].message == 'Enter a valid email address, such as name@example.com'
        assert result[0].display_message == '【Email】有効なメールアドレスを入力してください。例: name@example.com'
        assert result[0].code == 'valid_email_required'

    def test_comment_strings_switch_with_display_locale(self):
        class Importer(BaseModel):
            birth_date: Annotated[
                int, ExcelColumn(codec=DateCodec.day(), label='Birth date', order=1, date_format=DateFormat.DAY)
            ]

        field = extract_declared_field_metadata(Importer.model_fields['birth_date'])
        field.required = True
        with use_display_locale('en'):
            assert field.comment_required == 'Required: required'
            assert field.comment_date_format == 'Format: date (yyyy/mm/dd)'
