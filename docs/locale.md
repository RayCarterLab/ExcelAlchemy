# Locale Policy

## Scope

ExcelAlchemy currently distinguishes between two kinds of language output:

- runtime messages, intended for Python developers and integrators
- workbook display text, intended for spreadsheet users

These two layers do not currently share the same locale policy.

## Runtime Message Policy

- Supported runtime locale set: `('en',)`
- Default runtime locale: `en`
- Stability policy: runtime exceptions are intentionally standardized in English for the 2.x line

This means error messages raised in Python code are expected to stay English unless the
project explicitly announces broader runtime i18n support in a future release.

## Workbook Display Locale Policy

- Supported workbook display locales: `('zh-CN', 'en')`
- Default workbook display locale: `zh-CN`
- Stability policy: the default workbook locale is considered stable for the 2.x line

Workbook display locale affects user-facing spreadsheet text such as:

- import instructions in the first row
- header comments
- result and reason column labels
- row validation status text
- composite child labels such as start/end date and min/max value
- workbook-facing boolean values such as `Yes/No` or `是/否`

## Fallback Rules

- Runtime messages fall back to the runtime default locale: `en`
- Workbook display messages fall back to the workbook display default locale: `zh-CN`

If you pass an unsupported locale today, ExcelAlchemy will continue working and fall back
to the default locale for that message layer.

## Recommended Usage

Use `locale='zh-CN'` when the workbook is meant for Chinese-speaking spreadsheet users.

Use `locale='en'` when the workbook is meant for English-speaking spreadsheet users.

Examples:

```python
from excelalchemy import ExcelAlchemy, ImporterConfig

alchemy_zh = ExcelAlchemy(ImporterConfig(ImporterModel, creator=create_func, locale='zh-CN'))
alchemy_en = ExcelAlchemy(ImporterConfig(ImporterModel, creator=create_func, locale='en'))
```

## Compatibility Notes

- Constants in `excelalchemy.const` such as `HEADER_HINT`, `RESULT_COLUMN_LABEL`, and `REASON_COLUMN_LABEL`
  remain available as compatibility helpers and represent the stable `zh-CN` defaults.
- Locale-aware behavior should be driven through `ImporterConfig(..., locale=...)` and
  `ExporterConfig(..., locale=...)`, not by reading those constants directly.

## Future Direction

The i18n roadmap remains intentionally incremental:

1. keep runtime messages consistently English
2. keep workbook display locale explicit and stable
3. add new workbook locales additively
4. only expand runtime locale support when there is a clear maintenance plan
