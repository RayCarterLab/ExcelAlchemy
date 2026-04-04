# FastAPI Reference Project

This directory shows a minimal reference project structure for integrating
ExcelAlchemy into a FastAPI service.

## Layout

- `models.py`
  Defines workbook schema declarations.
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
     route registration and request parsing
  -> services.py
     template generation and import workflow orchestration
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

Example:

```bash
curl -X POST \
  -F "file=@employee-import.xlsx" \
  http://127.0.0.1:8000/employee-imports
```

Example JSON response:

```json
{
  "result": {
    "result": "SUCCESS",
    "download_url": "memory://employee-import-result.xlsx",
    "success_count": 1,
    "fail_count": 0
  },
  "created_rows": 1,
  "uploaded_artifacts": ["employee-import-result.xlsx"]
}
```

If the workbook has validation errors, the same endpoint still returns a
structured result payload. Application code can then read:

- workbook-level result status from `result`
- created row count from `created_rows`
- uploaded result workbook names from `uploaded_artifacts`

In a real project, you would typically extend this response with:

- `cell_error_map.to_api_payload()`
- `row_error_map.to_api_payload()`
- request-scoped trace or tenant metadata

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

For a captured output artifact, see:

- [`files/example-outputs/fastapi-reference.txt`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/files/example-outputs/fastapi-reference.txt)
