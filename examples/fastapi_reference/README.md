# FastAPI Reference Project

This directory shows a minimal reference project structure for integrating
ExcelAlchemy into a FastAPI service.

If you want copyable success / failure response shapes that match this
reference project, see
[`docs/api-response-cookbook.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/api-response-cookbook.md).

## Layout

- `models.py`
  Defines workbook schema declarations.
- `schemas.py`
  Defines request and response schemas for the HTTP layer.
- `responses.py`
  Builds stable structured API payloads from ExcelAlchemy result objects.
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
     request and response contracts
  -> services.py
     template generation and import workflow orchestration
  -> responses.py
     structured payload assembly for API consumers
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
- explicit request and response schemas
- structured API response building
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
    "summary": {
      "by_row": [],
      "by_code": []
    }
  },
  "created_rows": 1,
  "uploaded_artifacts": ["employee-import-result.xlsx"],
  "request": {
    "tenant_id": "tenant-001"
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

Example validation-error response shape:

```json
{
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
    ]
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

For a captured output artifact, see:

- [`files/example-outputs/fastapi-reference.txt`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/files/example-outputs/fastapi-reference.txt)
