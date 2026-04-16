# FastAPI Reference Project

This directory shows a minimal reference project structure for integrating
ExcelAlchemy into a FastAPI service.

If you want copyable success / failure response shapes that match this
reference project, see
[`docs/api-response-cookbook.md`](../../docs/api-response-cookbook.md).

## Layout

- `models.py`
  Defines workbook schema declarations.
- `schemas.py`
  Defines request schemas, payload models, and success/error response envelopes
  for the HTTP layer.
- `responses.py`
  Builds stable import payloads from ExcelAlchemy result objects.
- `presenters.py`
  Wraps payloads in HTTP-facing success/error envelopes.
- `storage.py`
  Defines a request-scoped in-memory `ExcelStorage` implementation.
- `services.py`
  Holds the import service layer and helper functions.
- `app.py`
  Wires routes to the service layer and exposes a runnable FastAPI app.

## Responsibility Diagram

```text
HTTP request
  -> app.py
     route registration, form parsing, and response_model wiring
  -> schemas.py
     request, payload, and envelope contracts
  -> services.py
     template generation and import workflow orchestration
  -> responses.py
     structured import payload assembly
  -> presenters.py
     HTTP-facing success and error envelopes
  -> storage.py
     upload fixture storage and result workbook upload handling
  -> models.py
     workbook schema declaration
```

This is intentionally small, but it mirrors the shape of a real backend:

- routes stay thin
- workflow logic lives in a service
- storage is injected instead of hard-coded
- schema declarations stay separate from transport concerns

## What It Demonstrates

- route layer and service layer separation
- explicit request, payload, and error-response schemas
- structured API response building with a stable envelope
- injected storage rather than global singleton state
- template download and workbook import endpoints
- a small, copyable structure that can be adapted into a real backend project

## How To Run

Run the demo entry point:

```bash
uv run python -m examples.fastapi_reference.app
```

Or run the app under an ASGI server:

```bash
uv run uvicorn examples.fastapi_reference.app:app --reload
```

## HTTP Endpoints

### `GET /employee-template.xlsx`

Downloads a workbook template generated from the importer schema.

Response:

- `200 OK`
- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition: attachment; filename=employee-template.xlsx`

### `POST /employee-imports`

Accepts an uploaded workbook and runs the import workflow.

Request:

- multipart form-data
- file field name: `file`
- optional form field: `tenant_id`

Example:

```bash
curl -X POST \
  -F "tenant_id=tenant-001" \
  -F "file=@employee-import.xlsx" \
  http://127.0.0.1:8000/employee-imports
```

Example JSON response:

```json
{
  "ok": true,
  "data": {
    "result": {
      "result": "SUCCESS",
      "is_success": true,
      "is_header_invalid": false,
      "is_data_invalid": false,
      "summary": {
        "success_count": 1,
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
      "facets": {
        "field_labels": [],
        "parent_labels": [],
        "unique_labels": [],
        "codes": [],
        "row_numbers_for_humans": []
      },
      "grouped": {
        "messages_by_row": {},
        "messages_by_code": {}
      },
      "summary": {
        "by_row": [],
        "by_code": []
      }
    },
    "remediation": {
      "result": {
        "result": "SUCCESS",
        "is_success": true,
        "is_header_invalid": false,
        "is_data_invalid": false
      },
      "remediation": {
        "needs_remediation": false,
        "affected_row_count": 0,
        "affected_field_count": 0,
        "affected_code_count": 0,
        "header_issue_count": 0,
        "result_workbook_available": true
      },
      "by_field": [],
      "by_code": [],
      "items": []
    },
    "created_rows": 1,
    "uploaded_artifacts": [],
    "request": {
      "tenant_id": "tenant-001"
    }
  }
}
```

If the workbook has validation errors, the same endpoint still returns a
structured result payload. Application code can then read:

- workbook-level result status from `result`
- created row count from `created_rows`
- uploaded result workbook names from `uploaded_artifacts`
- cell-level frontend payloads from `cell_errors`
- row-level frontend payloads from `row_errors`
- compact retry guidance from `remediation`

In the reference app, those values live under `data`, while `ok` tells the
client whether the route returned a success or an API-layer error envelope.

Example validation-error response shape:

```json
{
  "ok": true,
  "data": {
    "result": {
      "result": "DATA_INVALID",
      "is_success": false,
      "is_header_invalid": false,
      "is_data_invalid": true
    },
    "cell_errors": {
      "error_count": 2,
      "items": [
        {
          "code": "valid_email_required",
          "row_number_for_humans": 1,
          "column_number_for_humans": 2,
          "field_label": "Email",
          "display_message": "【Email】Enter a valid email address, such as name@example.com"
        }
      ],
      "facets": {
        "field_labels": ["Email"]
      }
    },
    "row_errors": {
      "error_count": 1,
      "summary": {
        "by_code": [
          {
            "code": "valid_email_required",
            "error_count": 1
          }
        ]
      }
    },
    "remediation": {
      "result": {
        "result": "DATA_INVALID",
        "is_success": false,
        "is_header_invalid": false,
        "is_data_invalid": true
      },
      "remediation": {
        "needs_remediation": true,
        "affected_row_count": 1,
        "affected_field_count": 1,
        "affected_code_count": 1,
        "header_issue_count": 0,
        "result_workbook_available": true,
        "suggested_action": "Correct the invalid rows and re-upload the workbook."
      },
      "by_field": [
        {
          "field_label": "Email",
          "unique_label": "Email",
          "error_count": 1,
          "codes": ["valid_email_required"],
          "suggested_action": "Enter a complete email address and re-upload the workbook.",
          "fix_hint": "Use a format such as name@example.com."
        }
      ]
    }
  }
}
```

The remediation payload is additive:

- `result`, `cell_errors`, and `row_errors` stay available for full inspection
- `remediation` is the smaller retry-oriented view
- `suggested_action` and `fix_hint` are intentionally conservative and may be
  omitted for unknown issue patterns

Example API-layer error response:

```json
{
  "ok": false,
  "error": {
    "code": "file_required",
    "message": "An Excel file is required.",
    "detail": {
      "field": "file"
    }
  }
}
```

In a real project, you would typically extend this response with:

- request-scoped trace metadata
- actor information
- domain-specific identifiers or import job ids
- your own error-code to UI-action mapping

## Suggested Adaptation Path

If you want to copy this into a real service, the next steps are usually:

1. Replace the in-memory `RequestScopedStorage` with your own `ExcelStorage`.
2. Move `EmployeeImporter` into your domain package.
3. Replace the demo `creator` logic with your real service or repository call.
4. Extend the response payload with your own API contract.
5. Add authentication, tenant resolution, and request logging in the route layer.

## Expected Output

The demo entry point prints:

- import result summary
- created row count
- uploaded artifact names
- registered route paths
- response sections
- request tenant and structured summary keys
- remediation summary keys

For a captured output artifact, see:

- [`files/example-outputs/fastapi-reference.txt`](../../files/example-outputs/fastapi-reference.txt)
