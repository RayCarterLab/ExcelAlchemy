# Architecture Boundaries

This file defines the public and implementation boundaries agents must respect
in `ExcelAlchemy`.

## Version Scope

For tasks explicitly scoped to ExcelAlchemy 3.0, follow
[`docs/agent/v3-prd.md`](v3-prd.md). In that scope, compatibility imports,
deprecated paths, warning behavior, and legacy configuration fields are not
protected unless a 3.0 task reintroduces them as current API.

The 3.0 module layout must use concrete responsibility names. Do not introduce
generic package names such as `_internal`.

## Public And Agent-Stable Surfaces

For application-facing public API guidance, use
[`docs/public-api.md`](../public-api.md). For agent work, prefer these stable
modules and ownership surfaces when editing current code and docs:

- `excelalchemy`
- `excelalchemy.config`
- `excelalchemy.columns`
- `excelalchemy.workbook_fields`
- `excelalchemy.results`
- `excelalchemy.errors`
- `excelalchemy.storage`
- `excelalchemy.codecs`
- `excelalchemy.policies`
- `excelalchemy.messages`

Some modules in this list, such as `excelalchemy.workbook_fields`,
`excelalchemy.messages`, and `excelalchemy.policies`, are stable ownership
surfaces for agents and maintainers but are not ordinary application-facing
entry points.

Primary public entry points:

- `excelalchemy.ExcelAlchemy`
- `excelalchemy.ImporterConfig`
- `excelalchemy.ExporterConfig`
- `excelalchemy.ImportMode`
- `excelalchemy.ExcelColumn(...)`
- codec helpers such as `excelalchemy.DateCodec`, `excelalchemy.EmailCodec`,
  `excelalchemy.NumberCodec`, and `excelalchemy.TextCodec`
- `excelalchemy.ImportResult`
- `excelalchemy.CellErrorMap`
- `excelalchemy.RowIssueMap`
- `excelalchemy.ExcelStorage`

## Implementation Surface

Prefer concrete responsibility modules when editing implementation code:

- `excelalchemy.adapters.*`
- `excelalchemy.schema.*`
- `excelalchemy.workbook.*`
- `excelalchemy.runtime.*`
- `excelalchemy.rendering.*`
- `excelalchemy.primitives.*`

The old `excelalchemy.core.*`, `excelalchemy.helper.*`,
`excelalchemy.i18n.*`, and `excelalchemy._primitives.*` packages are removed.
Do not recreate them as compatibility bridges.

## Removed Compatibility Surface

These 2.x compatibility imports are removed in 3.0 and must not be restored as
shims:

- `excelalchemy.exc`
- `excelalchemy.identity`
- `excelalchemy.header_models`
- `excelalchemy.const`
- `excelalchemy.types.*`
- `excelalchemy.metadata` (use `excelalchemy.workbook_fields`)
- `excelalchemy.util.convertor`
- `excelalchemy.core.*`
- `excelalchemy.helper.*`
- `excelalchemy.i18n.*`
- `excelalchemy._primitives.*`

The facade aliases `df`, `header_df`, `cell_errors`, and `row_errors` are also
removed. Config fields `minio`, `bucket_name`, and `url_expires` are not valid
3.0 config fields; construct an `ExcelStorage` implementation and pass it as
`storage=...`.

## Naming Preferences

Use current 3.0 terminology in new code and docs:

- `storage=...` with an explicit `ExcelStorage` implementation
- `worksheet_table` over `df`
- `header_table` over `header_df`
- `cell_error_map` over `cell_errors`
- `row_error_map` over `row_errors`
- `excel_codec` over `value_type`
- `Annotated[T, ExcelColumn(...)]` over wrapper field factories
- `TextCodec` over `StringCodec`
- `SingleChoiceCodec` / `MultiChoiceCodec` over frontend-control names such as
  radio or checkbox
- explicit choice helper parameters over organization/staff/tree wrapper codecs
- codec methods `build_comment`, `parse_input`, `format_display_value`,
  `normalize_import_value`, and `column_items`

## Component Ownership

Use these ownership boundaries when deciding where a change belongs:

- Facade: `src/excelalchemy/runtime/facade.py` owns the user-facing workflow and
  coordinates template generation, import, export, and upload.
- Schema: `src/excelalchemy/schema/layout.py` extracts Excel-facing layout from
  Pydantic models, expands composite fields, and validates ordering.
- Headers: `src/excelalchemy/workbook/headers.py` parses simple and merged headers
  and validates workbook header rows against schema layout.
- Rows: `src/excelalchemy/runtime/rows.py` aggregates flattened worksheet rows
  back into model-shaped payloads and maps row/cell issues to workbook
  coordinates.
- Executor: `src/excelalchemy/runtime/executor.py` validates row payloads and
  dispatches create, update, and create-or-update callbacks.
- Import session: `src/excelalchemy/runtime/import_session.py` owns one import
  run's lifecycle, mutable runtime state, and structured lifecycle events.
- Rendering and writer: `src/excelalchemy/rendering/renderer.py` and
  `src/excelalchemy/rendering/writer.py` turn worksheet tables into workbook
  payloads, comments, colors, result columns, and hint text.
- Storage: `src/excelalchemy/storage/`, `src/excelalchemy/storage/gateway.py`,
  and `src/excelalchemy/storage/minio.py` define and resolve storage behavior.
- Columns: `src/excelalchemy/columns.py` owns `ExcelColumn(...)` declarations.
- Workbook fields: `src/excelalchemy/workbook_fields/` owns resolved
  Excel-facing field presentation and runtime state.
- Pydantic integration: `src/excelalchemy/adapters/pydantic.py` shields the rest
  of the codebase from Pydantic-version details.
- Messages: `src/excelalchemy/messages.py` separates runtime
  messages from workbook display text.

## Extension Points

- Custom storage: implement `ExcelStorage` for non-Minio backends.
- Custom field codecs: implement `ExcelFieldCodec` or
  `CompositeExcelFieldCodec` for custom workbook semantics.
- Field declaration style: use ordinary Python types with
  `Annotated[T, ExcelColumn(...)]`. Put workbook-specific parsing behavior in
  `ExcelColumn(codec=...)`, not in the Python type annotation.
- Data conversion: use `data_converter` when workbook schema and backend
  payload shape differ.
- Locale: use `locale='zh-CN' | 'en'` for workbook-facing display text.

## Architectural Intent

Preserve these seams:

- facade vs collaborators
- workbook field semantics vs validation backend
- storage protocol vs concrete storage
- workbook display text vs runtime messages

## High-Risk Files

Before changing these files, inspect related tests and docs:

- `src/excelalchemy/__init__.py`
- `src/excelalchemy/config/`
- `src/excelalchemy/workbook_fields/`
- `src/excelalchemy/results/`
- `src/excelalchemy/errors.py`
- `src/excelalchemy/runtime/facade.py`
- `src/excelalchemy/runtime/import_session.py`
- `src/excelalchemy/schema/layout.py`
- `src/excelalchemy/workbook/headers.py`
- `src/excelalchemy/runtime/rows.py`
- `src/excelalchemy/runtime/executor.py`
- `src/excelalchemy/rendering/renderer.py`
- `src/excelalchemy/rendering/writer.py`
- `src/excelalchemy/storage/`
- `src/excelalchemy/storage/gateway.py`
- `src/excelalchemy/storage/minio.py`
- `src/excelalchemy/messages.py`

## Documentation Updates

Update documentation when behavior, API shape, examples, payloads, migration
guidance, or operational limits change.

Required updates by change type:

- Onboarding or recommended API shape: `README.md`, `README-pypi.md`.
- Public vs internal boundaries: `docs/public-api.md`.
- Migration guidance or deprecated paths: `docs/migrations.md`.
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
