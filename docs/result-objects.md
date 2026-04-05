# Result Objects and API Integration

This page explains how to read import results from ExcelAlchemy and how to turn
them into backend or frontend-friendly responses.

If you are new to the library, start with
[`docs/getting-started.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/getting-started.md).
If you want the stable public API boundaries, see
[`docs/public-api.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/public-api.md).
If you want copyable success / failure / header-invalid response shapes, see
[`docs/api-response-cookbook.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/api-response-cookbook.md).

## Core Result Objects

The most important public result objects are:

- `ImportResult`
- `CellErrorMap`
- `RowIssueMap`

You can import them from:

```python
from excelalchemy import ImportResult
from excelalchemy.results import CellErrorMap, RowIssueMap
```

## Error Payload Layers

ExcelAlchemy keeps machine-readable metadata separate from ready-to-render
messages.

- `code`
  Stable machine-readable identifier for frontend branching, filters, and
  summary aggregation.
- `message_key`
  Optional i18n-oriented identifier when the error originated from a known
  `MessageKey`.
- `message`
  Human-readable base message without workbook-coordinate decoration.
- `display_message`
  Human-readable message ready for UI rendering. For cell-level errors, this may
  include the workbook field prefix such as `【Email】...`.

Recommended usage:

- use `code` for branching and grouping
- use `message_key` for i18n-aware clients when present
- use `message` for logs, plain APIs, or analytics
- use `display_message` for UI lists, toasts, and workbook-adjacent feedback

Developer diagnostics are a separate layer. Warning and info logs are emitted
through named loggers such as `excelalchemy.codecs`, `excelalchemy.runtime`, and
`excelalchemy.metadata`, and should not be treated as API payload text.

## `ImportResult`

`ImportResult` is the high-level summary of one import run.

Useful fields include:

- `result`
  Overall status such as `SUCCESS`, `DATA_INVALID`, or `HEADER_INVALID`.
- `success_count`
  Number of successfully imported rows.
- `fail_count`
  Number of failed rows.
- `url`
  Result workbook download URL when one is produced.
- `missing_required`
- `missing_primary`
- `unrecognized`
- `duplicated`

Typical usage:

```python
result = await alchemy.import_data('employees.xlsx', 'employee-import-result.xlsx')

if result.result == 'SUCCESS':
    ...
```

Useful helpers:

- `is_success`
- `is_header_invalid`
- `is_data_invalid`
- `to_api_payload()`

Example payload:

```json
{
  "result": "DATA_INVALID",
  "is_success": false,
  "is_header_invalid": false,
  "is_data_invalid": true,
  "summary": {
    "success_count": 3,
    "fail_count": 1,
    "result_workbook_url": "memory://employee-import-result.xlsx"
  },
  "header_issues": {
    "is_required_missing": false,
    "missing_required": [],
    "missing_primary": [],
    "unrecognized": [],
    "duplicated": []
  }
}
```

## `CellErrorMap`

`cell_error_map` stores workbook-coordinate cell-level failures.

Recommended facade access:

```python
cell_error_map = alchemy.cell_error_map
```

Useful helpers:

- `at(row_index, column_index)`
- `messages_at(row_index, column_index)`
- `field_labels()`
- `codes()`
- `row_numbers_for_humans()`
- `flatten()`
- `records()`
- `summary_by_field()`
- `summary_by_row()`
- `summary_by_code()`
- `to_dict()`
- `to_api_payload()`

Example:

```python
payload = alchemy.cell_error_map.to_api_payload()
field_labels = alchemy.cell_error_map.field_labels()
codes = alchemy.cell_error_map.codes()
```

Shape:

```json
{
  "error_count": 2,
  "items": [
    {
      "code": "valid_email_required",
      "message_key": "valid_email_required",
      "row_index": 0,
      "row_number_for_humans": 1,
      "column_index": 1,
      "column_number_for_humans": 2,
      "field_label": "Email",
      "parent_label": null,
      "message": "Enter a valid email address, such as name@example.com",
      "display_message": "【Email】Enter a valid email address, such as name@example.com"
    }
  ],
  "summary": {
    "by_field": [
      {
        "field_label": "Email",
        "parent_label": null,
        "unique_label": "Email",
        "error_count": 1,
        "row_indices": [0],
        "row_numbers_for_humans": [1],
        "codes": ["valid_email_required"]
      }
    ],
    "by_row": [
      {
        "row_index": 0,
        "row_number_for_humans": 1,
        "error_count": 1,
        "codes": ["valid_email_required"],
        "field_labels": ["Email"],
        "unique_labels": ["Email"]
      }
    ],
    "by_code": [
      {
        "code": "valid_email_required",
        "error_count": 1,
        "row_indices": [0],
        "row_numbers_for_humans": [1],
        "unique_labels": ["Email"]
      }
    ]
  },
  "facets": {
    "field_labels": ["Email"],
    "parent_labels": [],
    "unique_labels": ["Email"],
    "codes": ["valid_email_required"],
    "row_numbers_for_humans": [1],
    "column_numbers_for_humans": [2]
  },
  "grouped": {
    "messages_by_field": {
      "Email": [
        "【Email】Enter a valid email address, such as name@example.com"
      ]
    },
    "messages_by_row": {
      "0": [
        "【Email】Enter a valid email address, such as name@example.com"
      ]
    },
    "messages_by_code": {
      "valid_email_required": [
        "【Email】Enter a valid email address, such as name@example.com"
      ]
    }
  },
  "by_row": {
    "0": {
      "1": [
        {
          "code": "valid_email_required",
          "message": "Enter a valid email address, such as name@example.com"
        }
      ]
    }
  }
}
```

Use this when you need:

- frontend field-level highlighting
- API responses that point back to workbook coordinates
- UI summaries that keep workbook and JSON feedback aligned
- aggregated views by field, row, or machine-readable code
- direct field/code/row facets without doing a second client-side pass

## `RowIssueMap`

`row_error_map` stores row-level failures, including row errors and
cell-originated row summaries.

Recommended facade access:

```python
row_error_map = alchemy.row_error_map
```

Useful helpers:

- `at(row_index)`
- `messages_for_row(row_index)`
- `numbered_messages_for_row(row_index)`
- `field_labels()`
- `codes()`
- `row_numbers_for_humans()`
- `flatten()`
- `records()`
- `summary_by_row()`
- `summary_by_code()`
- `to_dict()`
- `to_api_payload()`

Example:

```python
payload = alchemy.row_error_map.to_api_payload()
```

Use this when you need:

- one-line row summaries in an admin UI
- numbered failure lists for APIs
- a simpler summary than cell coordinates alone
- direct grouped row/code message collections for a frontend table or sidebar

## Recommended API Response Pattern

For a backend endpoint, a practical response shape is:

```python
result = await alchemy.import_data('employees.xlsx', 'employee-import-result.xlsx')

response = {
    'result': result.to_api_payload(),
    'cell_errors': alchemy.cell_error_map.to_api_payload(),
    'row_errors': alchemy.row_error_map.to_api_payload(),
}
```

This gives you:

- a stable top-level import summary
- row-level summaries for tables or toast messages
- cell-level coordinates for fine-grained UI rendering
- machine-readable `code` fields for frontend branching
- optional `message_key` fields for i18n-aware clients
- human-friendly row numbers through `row_number_for_humans`

For concrete success, data-invalid, and header-invalid API response examples,
see
[`docs/api-response-cookbook.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/api-response-cookbook.md).

## Workbook Feedback vs API Feedback

ExcelAlchemy is designed so the workbook result and the API response can tell
the same story.

- workbook feedback is written back into the result workbook
- API feedback can be built from `ImportResult`, `CellErrorMap`, and
  `RowIssueMap`

This is especially useful when:

- an admin user downloads the result workbook
- a frontend wants to preview failures before download
- a backend needs to log structured import failures

## Recommended Reading

- [`docs/getting-started.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/getting-started.md)
- [`docs/public-api.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/public-api.md)
- [`docs/api-response-cookbook.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/api-response-cookbook.md)
- [`examples/employee_import_workflow.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/employee_import_workflow.py)
- [`examples/fastapi_reference/README.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/fastapi_reference/README.md)
