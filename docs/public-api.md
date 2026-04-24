# Public API Guide

This page summarizes which ExcelAlchemy modules are intended to be stable public
entry points, which ones remain compatibility shims for the 2.x line, and which
ones should be treated as internal implementation details.

If you want the quickest path into the library, start with
[`docs/getting-started.md`](getting-started.md).
If you want the import platform model first, see
[`docs/platform-architecture.md`](platform-architecture.md)
and
[`docs/runtime-model.md`](runtime-model.md).
If you want a role-based reading path, see
[`docs/integration-roadmap.md`](integration-roadmap.md).
If you want concrete repository examples, see
[`examples/README.md`](../examples/README.md)
and
[`docs/examples-showcase.md`](examples-showcase.md).
If you want result-object guidance for backend or frontend integration, see
[`docs/result-objects.md`](result-objects.md).
If you want copyable backend response shapes, see
[`docs/api-response-cookbook.md`](api-response-cookbook.md).

## Import Platform At A Glance

The stable public import workflow in the 2.x line is:

1. template authoring
2. preflight gate
3. import runtime
4. result intelligence
5. artifact and delivery

This page documents the public APIs that participate in those stages.
It does not replace the more detailed platform docs:

- [`docs/platform-architecture.md`](platform-architecture.md)
- [`docs/runtime-model.md`](runtime-model.md)
- [`docs/integration-blueprints.md`](integration-blueprints.md)

## Stable Public Modules

These modules are the recommended import paths for application code:

- `excelalchemy`
  The package root re-exports the most common public types, codecs, config
  objects, and result models.
- `excelalchemy.config`
  Public workflow configuration objects such as `ImporterConfig`,
  `ExporterConfig`, and `ImportMode`.
- `excelalchemy.metadata`
  Public metadata entry points such as `FieldMeta(...)`, `ExcelMeta(...)`, and
  `PatchFieldMeta`.
  Template guidance metadata such as `hint=` and `example_value=` is part of
  this additive public surface.
- `excelalchemy.results`
  Structured import result models such as `ImportResult`,
  `ValidateResult`, `ValidateHeaderResult`, `ImportPreflightResult`, and
  `ImportPreflightStatus`.
- `excelalchemy.exceptions`
  Stable exception module for `ConfigError`, `ExcelCellError`,
  `ExcelRowError`, and `ProgrammaticError`.
- `excelalchemy.codecs`
  Public codec namespace for built-in Excel field codecs.

## Stable Public Protocols And Concepts

- `ExcelStorage`
  The recommended backend integration contract for workbook IO.
- `storage=...`
  The recommended backend configuration pattern in the 2.x line.
- `ExcelArtifact`
  The recommended return shape when you need bytes, base64, or data URLs.
- `ExcelAlchemy.import_data(..., on_event=...)`
  The additive public hook for synchronous import lifecycle events during one
  import run.
- `ExcelAlchemy.preflight_import(...)`
  The additive public hook for lightweight structural validation before full
  import execution.
- import inspection names:
  Prefer `worksheet_table`, `header_table`, `cell_error_map`, and
  `row_error_map` when reading import-run state from the facade.
- structured error access:
  Prefer `CellErrorMap` and `RowIssueMap` helpers such as `to_api_payload()`
  when you need frontend-friendly or API-friendly validation output.
  The stable helper set also includes `records()`, `summary_by_field()`,
  `summary_by_row()`, and `summary_by_code()` where applicable.
  For a compact retry-oriented payload, `excelalchemy.results` also exposes
  `build_frontend_remediation_payload(...)` as an additive helper.

## Stable Public Surface By Platform Stage

### Template authoring

- schema models declared with Pydantic
- `FieldMeta(...)`
- `ExcelMeta(...)`
- template generation methods on `ExcelAlchemy`
- `ExcelArtifact` when you need template bytes, base64, or data URLs

### Preflight gate

- `ExcelAlchemy.preflight_import(...)`
- `ImportPreflightResult`
- `ImportPreflightStatus`

### Import runtime

- `ExcelAlchemy.import_data(..., on_event=...)`
- `ImporterConfig`
- `ImportMode`
- `ImporterConfig.for_create(...)`
- `ImporterConfig.for_update(...)`
- `ImporterConfig.for_create_or_update(...)`

Important boundary:

- `on_event=...` is an additive synchronous observability hook
- it is not a separate async or job execution model
- platform docs use stage labels such as `Rows Processed`
- the concrete runtime event name emitted today is `row_processed`

### Result intelligence

This is the platform-stage label for the post-import consumption layer.
The concrete stable public surfaces remain the result objects and helpers below.

- `ImportResult`
- `CellErrorMap`
- `RowIssueMap`
- `build_frontend_remediation_payload(...)`
- facade inspection names:
  `worksheet_table`, `header_table`, `cell_error_map`, `row_error_map`

Important boundary:

- remediation payloads are opt-in additions on top of the stable result
  surfaces
- they do not replace `ImportResult.to_api_payload()` or the issue-map payloads

### Artifact and delivery

- `ExcelArtifact`
- `ExcelStorage`
- `storage=...`
- result workbook URL exposure through `ImportResult`

## Compatibility Modules In 2.x

These imports still work in the 2.x line, but should be treated as migration
paths rather than long-term public module choices:

- `excelalchemy.exc`
  Deprecated compatibility layer. Prefer `excelalchemy.exceptions`.
- `excelalchemy.identity`
  Deprecated compatibility layer. Prefer imports from the package root.
- `excelalchemy.header_models`
  Compatibility layer; application code should not depend on it.
- `excelalchemy.types.*`
  Deprecated compatibility namespace retained for 2.x migrations.
- `excelalchemy.util.convertor`
  Deprecated compatibility import. Prefer `excelalchemy.util.converter`.

## Internal Modules

These modules may change without notice and should not be imported directly in
application code:

- `excelalchemy.core.*`
- `excelalchemy.helper.*`
- `excelalchemy.i18n.*`
- `excelalchemy._primitives.*`

The internals are intentionally allowed to evolve as the 2.x architecture
continues to consolidate.

## Recommended Import Style

Prefer imports like:

```python
from excelalchemy import ExcelAlchemy, ExcelMeta, FieldMeta, ImporterConfig, ValidateResult
from excelalchemy.config import ExporterConfig, ImportMode
from excelalchemy.exceptions import ConfigError
```

For most application code, these are the recommended import paths:

- `from excelalchemy import ...`
  Use this for the common public types, codecs, result models, and facade.
- `from excelalchemy.config import ...`
  Use this when you need workflow configuration types such as `ExporterConfig`
  or `ImportMode`.
- `from excelalchemy.exceptions import ...`
  Use this when you catch or surface library-level exceptions.
- `from excelalchemy.metadata import ...`
  Use this if you want the dedicated metadata entry points directly.
- `from excelalchemy.results import ...`
  Use this if you need result models or richer error-map helper types directly.

For synchronous job-style progress reporting, you can attach an event callback
to the existing import call:

```python
job_state = {'status': 'pending', 'processed_rows': 0, 'total_rows': 0}

def handle_import_event(event: dict[str, object]) -> None:
    if event['event'] == 'started':
        job_state['status'] = 'running'
    elif event['event'] == 'row_processed':
        job_state['processed_rows'] = event['processed_row_count']
        job_state['total_rows'] = event['total_row_count']
    elif event['event'] == 'completed':
        job_state['status'] = 'completed'
        job_state['result'] = event['result']
    elif event['event'] == 'failed':
        job_state['status'] = 'failed'

result = await alchemy.import_data(
    'employees.xlsx',
    'employee-import-result.xlsx',
    on_event=handle_import_event,
)
```

This is still a synchronous import. The callback runs inline during normal
header validation, row execution, and result rendering, which makes it useful
for service-layer progress tracking without introducing a new execution model.

If you are building API responses from import failures, the recommended public
result helpers are:

- `CellErrorMap.to_api_payload()`
- `RowIssueMap.to_api_payload()`
- `build_frontend_remediation_payload(...)`
- `CellErrorMap.records()`
- `RowIssueMap.records()`
- `CellErrorMap.summary_by_field()`
- `CellErrorMap.summary_by_row()`
- `CellErrorMap.summary_by_code()`
- `RowIssueMap.summary_by_row()`
- `RowIssueMap.summary_by_code()`

Avoid depending on implementation details such as:

```python
from excelalchemy.core.alchemy import ExcelAlchemy
from excelalchemy.core.headers import ExcelHeaderParser
from excelalchemy._primitives.identity import UniqueLabel
```

## Recommended Backend Configuration Path

For the stable 2.x line, the recommended backend integration path is:

```python
storage=...
```

The `storage` object should implement `ExcelStorage`.

The older built-in Minio fields:

- `minio=...`
- `bucket_name=...`
- `url_expires=...`

still work in 2.x as compatibility paths, but they are no longer the
recommended public API shape and now emit deprecation warnings.

If you need concrete examples of the recommended storage path, see:

- [`examples/custom_storage.py`](../examples/custom_storage.py)
- [`examples/export_workflow.py`](../examples/export_workflow.py)
- [`docs/getting-started.md`](getting-started.md)

## Deprecation Direction

The 2.x line keeps compatibility shims to support migration, but the long-term
direction is:

- public API from `excelalchemy`, `excelalchemy.config`,
  `excelalchemy.metadata`, `excelalchemy.results`, `excelalchemy.exceptions`,
  and `excelalchemy.codecs`
- backend integration through `ExcelStorage`
- internal orchestration and helper modules treated as implementation details

For import-run state naming, the long-term direction is also:

- clear facade inspection names such as `worksheet_table`, `header_table`,
  `cell_error_map`, and `row_error_map`
- older aliases such as `df`, `header_df`, `cell_errors`, and `row_errors`
  retained only as 2.x compatibility paths
