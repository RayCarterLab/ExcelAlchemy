# Public API Guide

This page summarizes which ExcelAlchemy modules are intended to be stable public
entry points, which ones remain compatibility shims for the 2.x line, and which
ones should be treated as internal implementation details.

If you want the quickest path into the library, start with
[`docs/getting-started.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/getting-started.md).
If you want concrete repository examples, see
[`examples/README.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/README.md)
and
[`docs/examples-showcase.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/examples-showcase.md).
If you want result-object guidance for backend or frontend integration, see
[`docs/result-objects.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/result-objects.md).
If you want copyable backend response shapes, see
[`docs/api-response-cookbook.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/api-response-cookbook.md).

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
- `excelalchemy.results`
  Structured import result models such as `ImportResult`,
  `ValidateResult`, and `ValidateHeaderResult`.
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
- import inspection names:
  Prefer `worksheet_table`, `header_table`, `cell_error_map`, and
  `row_error_map` when reading import-run state from the facade.
- structured error access:
  Prefer `CellErrorMap` and `RowIssueMap` helpers such as `to_api_payload()`
  when you need frontend-friendly or API-friendly validation output.
  The stable helper set also includes `records()`, `summary_by_field()`,
  `summary_by_row()`, and `summary_by_code()` where applicable.

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

If you are building API responses from import failures, the recommended public
result helpers are:

- `CellErrorMap.to_api_payload()`
- `RowIssueMap.to_api_payload()`
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

- [`examples/custom_storage.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/custom_storage.py)
- [`examples/export_workflow.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/export_workflow.py)
- [`docs/getting-started.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/getting-started.md)

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
