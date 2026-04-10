# Examples

These examples are organized as a recommended learning path rather than a flat list.

If you want a single public-facing page that combines screenshots,
representative workflows, and captured outputs, see
[`docs/examples-showcase.md`](../docs/examples-showcase.md).

If you want a copyable reference layout rather than a single script, see
[`examples/fastapi_reference/`](fastapi_reference/README.md).

## Recommended Reading Order

1. `annotated_schema.py`
   - Start here if you want to learn the declaration style first.
   - Shows the modern `Annotated[..., Field(...), ExcelMeta(...)]` pattern.
   - Best for: first-time readers who want to understand the schema declaration style.
   - Output: prints the generated template filename and the declared field labels.
   - Captured output: [`files/example-outputs/annotated-schema.txt`](../files/example-outputs/annotated-schema.txt)
2. `employee_import_workflow.py`
   - Read this next if you want to understand the core import story.
   - Shows template generation, workbook upload, import execution, and result reporting.
   - Best for: backend developers implementing the basic import path.
   - Output: prints success and failure counts, created row count, and uploaded result artifacts.
   - Captured output: [`files/example-outputs/employee-import-workflow.txt`](../files/example-outputs/employee-import-workflow.txt)
3. `create_or_update_import.py`
   - Read this after the basic import flow.
   - Shows `ImporterConfig.for_create_or_update(...)` with `is_data_exist`, `creator`, and `updater`.
   - Best for: admin tools and synchronization flows that mix creates and updates.
   - Output: prints created row count, updated row count, and the final import result.
   - Captured output: [`files/example-outputs/create-or-update-import.txt`](../files/example-outputs/create-or-update-import.txt)
4. `export_workflow.py`
   - Read this once the import flow is clear.
   - Shows artifact generation, export uploads, and a custom storage-backed export task.
   - Best for: download centers and reporting tasks that need workbook artifacts and upload URLs.
   - Output: prints artifact filename, byte size, upload URL, and uploaded object names.
   - Captured output: [`files/example-outputs/export-workflow.txt`](../files/example-outputs/export-workflow.txt)
5. `custom_storage.py`
   - Read this when you want to implement your own `ExcelStorage`.
   - Keeps the example minimal and focused on the protocol boundary.
   - Best for: teams wiring ExcelAlchemy into their own object storage layer.
   - Output: prints the in-memory upload URL and uploaded byte count.
   - Captured output: [`files/example-outputs/custom-storage.txt`](../files/example-outputs/custom-storage.txt)
6. `date_and_range_fields.py`
   - Read this if you want to understand workbook-friendly date, date range, number range, and money fields.
   - Best for: data-entry templates with compensation, effective dates, or range fields.
   - Output: prints the generated template filename and the exported field labels.
   - Captured output: [`files/example-outputs/date-and-range-fields.txt`](../files/example-outputs/date-and-range-fields.txt)
7. `selection_fields.py`
   - Read this if your domain uses approval forms, assignments, ownership trees, or selection-heavy templates.
   - Best for: approval forms, personnel assignment forms, and selection-heavy business templates.
   - Output: prints the generated template filename and the declared selection field labels.
   - Captured output: [`files/example-outputs/selection-fields.txt`](../files/example-outputs/selection-fields.txt)
8. `minio_storage.py`
   - Read this if you need the built-in Minio path in the current 2.x line.
   - This reflects the current 2.x compatibility-based Minio path rather than a future 3.x-only storage story.
   - Best for: teams already using the built-in Minio compatibility path in 2.x.
   - Output: prints the gateway type and confirms the built-in Minio path.
9. `fastapi_upload.py`
   - Read this last as a web integration example.
   - It is useful once the import and storage examples already make sense.
   - Best for: backend teams exposing template download and workbook import over HTTP.
   - Output: prints the import result, created row count, uploaded result artifacts, and registered FastAPI routes.
10. `fastapi_reference/`
   - Read this if you want a copyable minimal reference project rather than a single-file integration sketch.
   - Shows a split between route, request/response schema, service, response builder, storage, and workbook schema layers.
   - Best for: teams integrating ExcelAlchemy into a real FastAPI backend.
   - Output: prints the import result, created row count, uploaded artifacts, registered route paths, and structured response sections.
   - Captured output: [`files/example-outputs/fastapi-reference.txt`](../files/example-outputs/fastapi-reference.txt)

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
  - `fastapi_reference/`

## Storage and Backend Integration

- `custom_storage.py`
  - Shows a minimal custom `ExcelStorage` implementation for export uploads.
- `export_workflow.py`
  - Shows a realistic export flow with artifact generation and upload.
- `minio_storage.py`
  - Shows the built-in Minio-backed storage path currently available in the 2.x line.
- `fastapi_upload.py`
  - Shows a FastAPI integration sketch for template download and workbook import.
- `fastapi_reference/`
  - Shows a minimal reference-project layout with route, service, storage, and schema modules.

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
uv run python examples/fastapi_upload.py
uv run python -m examples.fastapi_reference.app
```

If you want to run the FastAPI app itself, install FastAPI first and then run
your preferred ASGI server against `examples.fastapi_upload:app`.

For the reference-project version, use:

```bash
uv run uvicorn examples.fastapi_reference.app:app --reload
```

If you want to smoke-test the web integration without running a server, execute:

```bash
uv run python examples/fastapi_upload.py
```

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
- Fixed example output assets are generated by
  `scripts/generate_example_output_assets.py`.
