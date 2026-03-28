from pydantic import BaseModel

from excelalchemy import Date, DateFormat, FieldMeta
from excelalchemy.i18n.messages import (
    DISPLAY_DEFAULT_LOCALE,
    SUPPORTED_DISPLAY_LOCALES,
    SUPPORTED_RUNTIME_LOCALES,
    MessageKey,
    display_message,
    message,
    use_display_locale,
)
from excelalchemy.metadata import extract_declared_field_metadata
from excelalchemy.results import ValidateRowResult


class TestI18nMessages:
    def test_message_formats_templates(self):
        assert message(MessageKey.ENTER_DATE_FORMAT, date_format='yyyy/mm/dd') == 'Enter a date in yyyy/mm/dd format'

    def test_message_falls_back_to_default_locale(self):
        assert (
            message(MessageKey.NO_STORAGE_BACKEND_CONFIGURED, locale='zh-CN')
            == 'No storage backend is configured; pass storage=... or install and configure ExcelAlchemy[minio]'
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
        assert SUPPORTED_DISPLAY_LOCALES == ('zh-CN', 'en')
        assert DISPLAY_DEFAULT_LOCALE == 'zh-CN'

    def test_comment_strings_switch_with_display_locale(self):
        class Importer(BaseModel):
            birth_date: Date = FieldMeta(label='Birth date', order=1, date_format=DateFormat.DAY)

        field = extract_declared_field_metadata(Importer.model_fields['birth_date'])
        field.required = True
        with use_display_locale('en'):
            assert field.comment_required == 'Required: required'
            assert field.comment_date_format == 'Format: date (yyyy/mm/dd)'
