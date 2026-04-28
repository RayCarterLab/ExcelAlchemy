# Architecture Boundaries

This file defines the public, internal, and compatibility boundaries agents must
respect in `ExcelAlchemy`.

## Public Surface

Prefer these stable public modules in new code and docs:

- `excelalchemy`
- `excelalchemy.config`
- `excelalchemy.metadata`
- `excelalchemy.results`
- `excelalchemy.exceptions`
- `excelalchemy.codecs`

Primary public entry points:

- `excelalchemy.ExcelAlchemy`
- `excelalchemy.ImporterConfig`
- `excelalchemy.ExporterConfig`
- `excelalchemy.ImportMode`
- `excelalchemy.FieldMeta(...)`
- `excelalchemy.ExcelMeta(...)`
- `excelalchemy.ImportResult`
- `excelalchemy.CellErrorMap`
- `excelalchemy.RowIssueMap`
- `excelalchemy.ExcelStorage`

## Internal Surface

Treat these as internal implementation details unless the task explicitly
targets internals:

- `excelalchemy.core.*`
- `excelalchemy.helper.*`
- `excelalchemy.i18n.*`
- `excelalchemy._primitives.*`

Do not present internal modules as stable application-facing API in docs or
examples.

## Compatibility Surface

Treat these as 2.x compatibility-only imports:

- `excelalchemy.exc`
- `excelalchemy.identity`
- `excelalchemy.header_models`
- `excelalchemy.types.*`
- `excelalchemy.util.convertor`

Backward compatibility is active in the 2.x line. Do not remove compatibility
imports, deprecated paths, aliases, or warning behavior casually.

## Naming Preferences

Use current 2.x terminology in new code and docs:

- `storage=...` over `minio=...`, `bucket_name=...`, `url_expires=...`
- `worksheet_table` over `df`
- `header_table` over `header_df`
- `cell_error_map` over `cell_errors`
- `row_error_map` over `row_errors`

## Component Ownership

Use these ownership boundaries when deciding where a change belongs:

- Facade: `src/excelalchemy/core/alchemy.py` owns the user-facing workflow and
  coordinates template generation, import, export, and upload.
- Schema: `src/excelalchemy/core/schema.py` extracts Excel-facing layout from
  Pydantic models, expands composite fields, and validates ordering.
- Headers: `src/excelalchemy/core/headers.py` parses simple and merged headers
  and validates workbook header rows against schema layout.
- Rows: `src/excelalchemy/core/rows.py` aggregates flattened worksheet rows
  back into model-shaped payloads and maps row/cell issues to workbook
  coordinates.
- Executor: `src/excelalchemy/core/executor.py` validates row payloads and
  dispatches create, update, and create-or-update callbacks.
- Import session: `src/excelalchemy/core/import_session.py` owns one import
  run's lifecycle, mutable runtime state, and structured lifecycle events.
- Rendering and writer: `src/excelalchemy/core/rendering.py` and
  `src/excelalchemy/core/writer.py` turn worksheet tables into workbook
  payloads, comments, colors, result columns, and hint text.
- Storage: `src/excelalchemy/core/storage_protocol.py`,
  `src/excelalchemy/core/storage.py`, and
  `src/excelalchemy/core/storage_minio.py` define and resolve storage behavior.
- Metadata: `src/excelalchemy/metadata.py` owns `FieldMeta(...)`,
  `ExcelMeta(...)`, compatibility metadata facades, and Excel-facing field
  presentation state.
- Pydantic integration: `src/excelalchemy/helper/pydantic.py` shields the rest
  of the codebase from Pydantic-version details.
- Internationalization: `src/excelalchemy/i18n/messages.py` separates runtime
  messages from workbook display text.

## Extension Points

- Custom storage: implement `ExcelStorage` for non-Minio backends.
- Custom field codecs: implement `ExcelFieldCodec` or
  `CompositeExcelFieldCodec` for custom workbook semantics.
- Field declaration styles: both `FieldMeta(...)` and
  `Annotated[T, Field(...), ExcelMeta(...)]` are supported.
- Data conversion: use `data_converter` when workbook schema and backend
  payload shape differ.
- Locale: use `locale='zh-CN' | 'en'` for workbook-facing display text.

## Architectural Intent

Preserve these seams:

- facade vs collaborators
- metadata vs validation backend
- storage protocol vs concrete storage
- workbook display text vs runtime messages

## High-Risk Files

Before changing these files, inspect related tests and docs:

- `src/excelalchemy/__init__.py`
- `src/excelalchemy/config.py`
- `src/excelalchemy/metadata.py`
- `src/excelalchemy/results.py`
- `src/excelalchemy/exceptions.py`
- `src/excelalchemy/core/alchemy.py`
- `src/excelalchemy/core/import_session.py`
- `src/excelalchemy/core/schema.py`
- `src/excelalchemy/core/headers.py`
- `src/excelalchemy/core/rows.py`
- `src/excelalchemy/core/executor.py`
- `src/excelalchemy/core/storage.py`
- `src/excelalchemy/core/storage_protocol.py`
- `src/excelalchemy/core/storage_minio.py`
- `src/excelalchemy/i18n/messages.py`
- `src/excelalchemy/types/`
- `src/excelalchemy/exc.py`
- `src/excelalchemy/identity.py`
- `src/excelalchemy/header_models.py`
- `src/excelalchemy/util/convertor.py`

## Documentation Updates

Update documentation when behavior, API shape, examples, payloads, migration
guidance, or operational limits change.

Required updates by change type:

- Onboarding or recommended API shape: `README.md`, `README-pypi.md`.
- Public vs internal boundaries: `docs/public-api.md`.
- Migration guidance or deprecated paths: `MIGRATIONS.md`.
- Component responsibilities and agent rules:
  `docs/agent/architecture-boundaries.md`.
- Human platform/code mapping: `docs/platform-architecture.md` and
  `docs/platform-code-mapping.md`.
- Result objects or API payloads: `docs/result-objects.md`,
  `docs/api-response-cookbook.md`.
- Locale behavior or message policy: `docs/locale.md`.
- Runtime limits or performance expectations: `docs/limitations.md`,
  `docs/performance.md`.
- Examples or reference app layout: `examples/README.md`,
  `examples/fastapi_reference/README.md`.
- Captured example outputs: regenerate with
  `scripts/generate_example_output_assets.py` and validate with smoke scripts.

Do not invent new documentation-site, release, or smoke-test workflows that are
not already represented by `docs/`, `scripts/`, and `.github/workflows/`.
