# API Response Cookbook

This page shows practical response shapes for exposing ExcelAlchemy through a
backend API.

If you are new to the library, start with
[`docs/getting-started.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/getting-started.md).
If you want the result-object reference first, see
[`docs/result-objects.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/result-objects.md).
If you want a copyable FastAPI-oriented example, see
[`examples/fastapi_reference/README.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/fastapi_reference/README.md).

## Recommended Top-Level Shape

For most backends, a stable import response can look like this:

```python
result = await alchemy.import_data('employees.xlsx', 'employee-import-result.xlsx')

response = {
    'result': result.to_api_payload(),
    'cell_errors': alchemy.cell_error_map.to_api_payload(),
    'row_errors': alchemy.row_error_map.to_api_payload(),
}
```

This shape works well because it separates:

- workbook-level outcome from `result`
- cell-level UI rendering from `cell_errors`
- row-level summaries from `row_errors`

Within each error item:

- use `code` for machine-readable branching
- use `message_key` when you want to map back to a localized message catalog
- use `message` for logs or plain-text APIs
- use `display_message` when you want ready-to-render UI text

## 1. Success Response

Use this when the import completed without header or data failures.

```json
{
  "result": {
    "result": "SUCCESS",
    "is_success": true,
    "is_header_invalid": false,
    "is_data_invalid": false,
    "summary": {
      "success_count": 12,
      "fail_count": 0,
      "result_workbook_url": "memory://employee-import-result.xlsx"
    },
    "header_issues": {
      "is_required_missing": false,
      "missing_required": [],
      "missing_primary": [],
      "unrecognized": [],
      "duplicated": []
    }
  },
  "cell_errors": {
    "error_count": 0,
    "items": [],
    "by_row": {},
    "summary": {
      "by_field": [],
      "by_row": [],
      "by_code": []
    }
  },
  "row_errors": {
    "error_count": 0,
    "items": [],
    "by_row": {},
    "summary": {
      "by_row": [],
      "by_code": []
    }
  }
}
```

Frontend usage:

- show a success toast from `result.result`
- show imported row counts from `result.summary`
- offer the result workbook download when `result.summary.result_workbook_url` is present

## 2. Data-Invalid Response

Use this when the header is valid but one or more rows failed validation.

```json
{
  "result": {
    "result": "DATA_INVALID",
    "is_success": false,
    "is_header_invalid": false,
    "is_data_invalid": true,
    "summary": {
      "success_count": 10,
      "fail_count": 2,
      "result_workbook_url": "memory://employee-import-result.xlsx"
    },
    "header_issues": {
      "is_required_missing": false,
      "missing_required": [],
      "missing_primary": [],
      "unrecognized": [],
      "duplicated": []
    }
  },
  "cell_errors": {
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
        "unique_label": "Email",
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
    }
  },
  "row_errors": {
    "error_count": 1,
    "summary": {
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
    }
  }
}
```

Frontend usage:

- render a failed import banner from `result.is_data_invalid`
- build a row-error table from `row_errors.summary.by_row`
- build field filters or grouped panels from `cell_errors.summary.by_field`
- branch on `code` for field-specific UI affordances

## 3. Header-Invalid Response

Use this when the workbook header row does not match the schema.

```json
{
  "result": {
    "result": "HEADER_INVALID",
    "is_success": false,
    "is_header_invalid": true,
    "is_data_invalid": false,
    "summary": {
      "success_count": 0,
      "fail_count": 0,
      "result_workbook_url": null
    },
    "header_issues": {
      "is_required_missing": true,
      "missing_required": ["Email"],
      "missing_primary": [],
      "unrecognized": ["Nickname"],
      "duplicated": ["Phone"]
    }
  },
  "cell_errors": {
    "error_count": 0,
    "items": [],
    "by_row": {},
    "summary": {
      "by_field": [],
      "by_row": [],
      "by_code": []
    }
  },
  "row_errors": {
    "error_count": 0,
    "items": [],
    "by_row": {},
    "summary": {
      "by_row": [],
      "by_code": []
    }
  }
}
```

Frontend usage:

- show a header-level blocking dialog from `result.is_header_invalid`
- render missing and unrecognized headers directly from `result.header_issues`
- avoid showing row-level validation tables when there are no row errors

## 4. Suggested Backend Helpers

For larger backends, it is useful to wrap the three payload builders:

```python
def build_excel_import_response(alchemy, result):
    return {
        'result': result.to_api_payload(),
        'cell_errors': alchemy.cell_error_map.to_api_payload(),
        'row_errors': alchemy.row_error_map.to_api_payload(),
    }
```

This keeps your route layer thin and your API contract stable.

## 5. Frontend Mapping Ideas

Common patterns:

- use `result.result` for high-level status banners
- use `result.summary.success_count` and `result.summary.fail_count` for summary chips
- use `row_errors.summary.by_row` for row tables
- use `cell_errors.items` for precise cell navigation
- use `cell_errors.summary.by_code` for grouped issue badges
- use `code` when you want machine-readable branching or localization on the frontend
- use `message_key` when you maintain your own message catalog
- use `message` when you want plain text without workbook decoration
- use `display_message` when you want ready-to-render text

## 6. Related Reading

- [`docs/result-objects.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/result-objects.md)
- [`examples/fastapi_reference/README.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/fastapi_reference/README.md)
- [`docs/public-api.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/public-api.md)
