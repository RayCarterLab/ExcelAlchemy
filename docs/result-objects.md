# Result Objects and API Integration

This page explains how to read import results from ExcelAlchemy and how to turn
them into backend or frontend-friendly responses.

If you are new to the library, start with
[`docs/getting-started.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/getting-started.md).
If you want the stable public API boundaries, see
[`docs/public-api.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/public-api.md).

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

## `CellErrorMap`

`cell_error_map` stores workbook-coordinate cell-level failures.

Recommended facade access:

```python
cell_error_map = alchemy.cell_error_map
```

Useful helpers:

- `at(row_index, column_index)`
- `messages_at(row_index, column_index)`
- `flatten()`
- `records()`
- `to_dict()`
- `to_api_payload()`

Example:

```python
payload = alchemy.cell_error_map.to_api_payload()
```

Shape:

```json
{
  "error_count": 2,
  "items": [
    {
      "row_index": 0,
      "column_index": 1,
      "message": "Enter a valid email address, such as name@example.com",
      "display_message": "Enter a valid email address, such as name@example.com"
    }
  ],
  "by_row": {
    "0": {
      "1": [
        {
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
- `flatten()`
- `records()`
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

## Recommended API Response Pattern

For a backend endpoint, a practical response shape is:

```python
result = await alchemy.import_data('employees.xlsx', 'employee-import-result.xlsx')

response = {
    'result': result.model_dump(),
    'cell_errors': alchemy.cell_error_map.to_api_payload(),
    'row_errors': alchemy.row_error_map.to_api_payload(),
}
```

This gives you:

- a stable top-level import summary
- row-level summaries for tables or toast messages
- cell-level coordinates for fine-grained UI rendering

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
- [`examples/employee_import_workflow.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/employee_import_workflow.py)
- [`examples/fastapi_reference/README.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/fastapi_reference/README.md)
