# Examples

These examples are organized as a recommended learning path rather than a flat list.

## Recommended Reading Order

1. `annotated_schema.py`
   - Start here if you want to learn the declaration style first.
   - Shows the modern `Annotated[..., Field(...), ExcelMeta(...)]` pattern.
2. `employee_import_workflow.py`
   - Read this next if you want to understand the core import story.
   - Shows template generation, workbook upload, import execution, and result reporting.
3. `create_or_update_import.py`
   - Read this after the basic import flow.
   - Shows `ImporterConfig.for_create_or_update(...)` with `is_data_exist`, `creator`, and `updater`.
4. `export_workflow.py`
   - Read this once the import flow is clear.
   - Shows artifact generation, export uploads, and a custom storage-backed export task.
5. `custom_storage.py`
   - Read this when you want to implement your own `ExcelStorage`.
   - Keeps the example minimal and focused on the protocol boundary.
6. `date_and_range_fields.py`
   - Read this if you want to understand workbook-friendly date, date range, number range, and money fields.
7. `selection_fields.py`
   - Read this if your domain uses approval forms, assignments, ownership trees, or selection-heavy templates.
8. `minio_storage.py`
   - Read this if you need the built-in Minio path in the current 2.x line.
   - This reflects the current 2.x compatibility-based Minio path rather than a future 3.x-only storage story.
9. `fastapi_upload.py`
   - Read this last as an integration sketch.
   - It is useful once the import and storage examples already make sense.

## By Goal

- Learn the declaration style:
  - `annotated_schema.py`
- Learn the core import flow:
  - `employee_import_workflow.py`
  - `create_or_update_import.py`
- Learn export and storage integration:
  - `export_workflow.py`
  - `custom_storage.py`
  - `minio_storage.py`
- Learn field families:
  - `date_and_range_fields.py`
  - `selection_fields.py`
- Learn web integration:
  - `fastapi_upload.py`

## Storage and Backend Integration

- `custom_storage.py`
  - Shows a minimal custom `ExcelStorage` implementation for export uploads.
- `export_workflow.py`
  - Shows a realistic export flow with artifact generation and upload.
- `minio_storage.py`
  - Shows the built-in Minio-backed storage path currently available in the 2.x line.
- `fastapi_upload.py`
  - Shows a FastAPI integration sketch for template download and workbook import.

## How To Run

Run examples from the repository root:

```bash
uv run python examples/annotated_schema.py
uv run python examples/employee_import_workflow.py
uv run python examples/create_or_update_import.py
uv run python examples/date_and_range_fields.py
uv run python examples/selection_fields.py
uv run python examples/custom_storage.py
uv run python examples/export_workflow.py
uv run python examples/minio_storage.py
```

If you want to try the FastAPI sketch, install FastAPI first and then run your
preferred ASGI server against `examples.fastapi_upload:app`.

## Notes

- The examples intentionally use in-memory storage so they stay self-contained.
- They are meant to show the recommended public API shape for the stable 2.x
  line.
- If you want a production backend, prefer `storage=...` with
  `MinioStorageGateway` or your own `ExcelStorage` implementation.
- The built-in `minio_storage.py` example reflects the current 2.x Minio path,
  which still uses the compatibility configuration fields under the hood.
- The smoke tests in `tests/integration/test_examples_smoke.py` cover the main
  example entry points directly.
