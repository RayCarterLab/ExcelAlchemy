# Examples

This directory contains runnable examples for the current 2.x API shape.
Use them to understand how the library is intended to be used from application code.

## Related docs

- [../README.md](../README.md) for the main user-facing overview.
- [../docs/public-api.md](../docs/public-api.md) for the supported public import surface.
- [../docs/repo-map.md](../docs/repo-map.md) for where examples fit into the repository.
- [../src/excelalchemy/README.md](../src/excelalchemy/README.md) for the implementation details behind the public workflows shown here.
- [../tests/README.md](../tests/README.md) for the smoke and integration coverage that treats examples as contract material.

## What These Examples Demonstrate

- The recommended public API path:
  - public imports from `excelalchemy`
  - `storage=...` as the preferred backend integration path
  - facade methods on `ExcelAlchemy`
- The main user-facing workflows in this repository:
  - schema declaration
  - template generation
  - import validation
  - create-or-update import
  - export generation
  - storage integration
  - backend/API integration

## Example Groups

### Core workflow demos

- `examples/annotated_schema.py`
  - Demonstrates the modern `Annotated[..., Field(...), ExcelMeta(...)]` declaration style.
  - Shows additive template UX metadata such as `hint=` and `example_value=`.
  - Type: demo of the recommended declaration style.

- `examples/employee_import_workflow.py`
  - Demonstrates the basic import flow from template generation through preflight, lifecycle-event observation, and import result handling.
  - Type: runnable workflow demo.

- `examples/create_or_update_import.py`
  - Demonstrates `ImporterConfig.for_create_or_update(...)`.
  - Type: runnable workflow demo.

- `examples/export_workflow.py`
  - Demonstrates export artifact generation and upload behavior.
  - Type: runnable workflow demo.

### Field-family demos

- `examples/date_and_range_fields.py`
  - Demonstrates date, date range, number range, and money-style workbook fields.
  - Type: focused field-behavior demo.

- `examples/selection_fields.py`
  - Demonstrates option-driven field families such as radio, tree, organization, and staff selection fields.
  - Type: focused field-behavior demo.

### Storage and compatibility examples

- `examples/custom_storage.py`
  - Demonstrates a minimal custom `ExcelStorage` implementation.
  - Type: reference integration example.

- `examples/minio_storage.py`
  - Demonstrates the built-in Minio path that still exists in the current 2.x line.
  - Type: compatibility example, not the preferred new-code path.

### Backend integration examples

- `examples/fastapi_upload.py`
  - Demonstrates a compact FastAPI integration sketch.
  - Type: lightweight integration demo.

- `examples/fastapi_reference/`
  - Demonstrates a more structured FastAPI-oriented reference layout with route, service, response, schema, and storage separation.
  - Type: reference integration example.

## How These Examples Should Be Used

- Use them as:
  - runnable demonstrations of the current recommended API shape
  - copyable starting points for integration work
  - smoke-tested examples of how the public facade is expected to behave

- Do not treat them as:
  - internal architecture documentation
  - the only supported way to structure an application
  - a guarantee that every example pattern is equally preferred

## What An Agent Should Infer

- The examples are part of the user-facing contract of this repository.
- The examples generally reflect the preferred 2.x usage story.
- `examples/custom_storage.py` and `examples/fastapi_reference/` are the best examples for real integration patterns.
- `examples/custom_storage.py` is the narrow case where application-side example code currently touches `src/excelalchemy/core/table.py`, because `ExcelStorage.read_excel_table(...)` uses `WorksheetTable` in the 2.x line.
- `examples/minio_storage.py` is intentionally a compatibility-oriented example for the current 2.x line.

## What An Agent Should Not Infer

- Do not infer that internal modules under `src/excelalchemy/core/` are the intended application import path just because an example touches a low-level concept.
- Do not generalize the imports in `examples/minio_storage.py` into the recommended application API; that example exists to show the built-in Minio compatibility path.
- Do not infer that legacy Minio config fields are the preferred new-code path; the repo docs prefer `storage=...`.
- Do not infer that examples are exploratory or disposable; they are covered by smoke-style tests.
- Do not infer that example output text can change freely; docs and generated assets depend on it.

## When Example Changes Require Other Updates

- If example behavior changes, also inspect:
  - `tests/integration/test_examples_smoke.py`
  - `scripts/smoke_examples.py`
  - `docs/examples-showcase.md`
  - `README.md`
  - `README-pypi.md`

- If printed example output changes intentionally, also update:
  - `files/example-outputs/`
  - `scripts/generate_example_output_assets.py`
  - `scripts/smoke_docs_assets.py`

- If example API payloads or integration response shapes change, also inspect:
  - `docs/result-objects.md`
  - `docs/api-response-cookbook.md`
  - `examples/fastapi_reference/README.md`

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

If you want the visual showcase and captured outputs that correspond to these examples, see:

- `docs/examples-showcase.md`
- `files/example-outputs/`
