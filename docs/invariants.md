# Invariants

This document records important invariants and behavioral constraints that are visible in the repository today.
It is based on source code, tests, and existing documentation.

For API boundaries, see [`docs/public-api.md`](public-api.md).
For domain vocabulary, see [`docs/domain-model.md`](domain-model.md).
For component structure, see [`docs/architecture.md`](architecture.md).

## Related docs

- [../AGENTS.md](../AGENTS.md) for repository-local guidance on changing behavior safely.
- [repo-map.md](repo-map.md) for a directory-level map of the code and docs behind these constraints.
- [domain-model.md](domain-model.md) for the concepts these invariants attach to.
- [../src/excelalchemy/README.md](../src/excelalchemy/README.md) for the implementation view of the main package.
- [../tests/README.md](../tests/README.md) for where these invariants are enforced.

## 1. Public API invariants

- **Stable public imports come from the package root and a small set of public modules.**
  - Why it matters: new code and documentation should prefer the supported public surface instead of internal modules that may change without notice.
  - Relevant files: `docs/public-api.md`, `src/excelalchemy/__init__.py`, `src/excelalchemy/config.py`, `src/excelalchemy/metadata.py`, `src/excelalchemy/results.py`, `src/excelalchemy/exceptions.py`

- **`ExcelStorage` and `storage=...` are the recommended 2.x backend integration contract.**
  - Why it matters: storage is modeled as a protocol boundary, and new code should not treat Minio-specific config as the primary architecture.
  - Relevant files: `docs/public-api.md`, `MIGRATIONS.md`, `src/excelalchemy/core/storage_protocol.py`, `src/excelalchemy/config.py`

- **`ImportResult`, `CellErrorMap`, and `RowIssueMap` are first-class public result surfaces.**
  - Why it matters: API and frontend integrations are expected to build on these objects and their helper methods rather than internal runtime state.
  - Relevant files: `docs/result-objects.md`, `docs/api-response-cookbook.md`, `src/excelalchemy/results.py`, `tests/contracts/test_result_contract.py`

- **The recommended import inspection names are `worksheet_table`, `header_table`, `cell_error_map`, and `row_error_map`.**
  - Why it matters: these names are the forward-looking 2.x terminology; older aliases exist for compatibility but are not the preferred naming path.
  - Relevant files: `docs/public-api.md`, `MIGRATIONS.md`, `src/excelalchemy/core/alchemy.py`, `src/excelalchemy/core/import_session.py`

- **Template/export APIs return explicit Excel payload types.**
  - Why it matters: callers can rely on `download_template()` and `export()` returning prefixed data URLs, while `download_template_artifact()` and `export_artifact()` return binary-friendly `ExcelArtifact` objects.
  - Relevant files: `src/excelalchemy/core/abstract.py`, `src/excelalchemy/core/alchemy.py`, `src/excelalchemy/artifacts.py`, `tests/contracts/test_template_contract.py`, `tests/contracts/test_export_contract.py`

## 2. Behavioral invariants

- **Template generation does not require a configured storage backend.**
  - Why it matters: template rendering is a pure render path; only import workbook reads and upload paths depend on storage.
  - Relevant files: `tests/contracts/test_storage_contract.py`, `src/excelalchemy/core/alchemy.py`, `src/excelalchemy/core/storage.py`

- **A header-invalid import ends the flow without uploading a result workbook.**
  - Why it matters: invalid headers short-circuit before row execution and result-workbook upload.
  - Relevant files: `tests/contracts/test_import_contract.py`, `src/excelalchemy/core/import_session.py`, `src/excelalchemy/results.py`

- **A data-invalid import uploads a result workbook and reports a download URL.**
  - Why it matters: row-level failures are expected to produce a workbook that can be returned to users for correction.
  - Relevant files: `tests/contracts/test_import_contract.py`, `tests/contracts/test_storage_contract.py`, `src/excelalchemy/core/import_session.py`

- **Import result workbooks prepend result and reason columns and mark failures visually.**
  - Why it matters: the library’s failure feedback is workbook-facing, not just API-facing.
  - Relevant files: `tests/contracts/test_import_contract.py`, `tests/contracts/test_core_components_contract.py`, `src/excelalchemy/core/rows.py`, `src/excelalchemy/core/writer.py`

- **Explicit `storage` takes precedence over legacy Minio settings when both are supplied.**
  - Why it matters: this preserves the recommended storage abstraction path while still allowing legacy compatibility fields to coexist during migration.
  - Relevant files: `tests/contracts/test_storage_contract.py`, `tests/unit/test_config_options.py`, `src/excelalchemy/core/storage.py`, `src/excelalchemy/config.py`

- **Uploaded workbook payloads remain binary `.xlsx` content, not prefixed data URLs.**
  - Why it matters: storage backends are expected to receive workbook bytes, not browser-oriented `data:` URL strings.
  - Relevant files: `tests/contracts/test_storage_contract.py`, `src/excelalchemy/core/storage_minio.py`, `src/excelalchemy/util/file.py`

- **Each import run reloads workbook state and tracks a fresh session snapshot.**
  - Why it matters: the facade is long-lived, but import runtime state is one-shot and should not leak from one run into the next.
  - Relevant files: `tests/contracts/test_import_contract.py`, `src/excelalchemy/core/import_session.py`, `src/excelalchemy/core/alchemy.py`

- **Generated templates do not rely on Excel data-validation rules.**
  - Why it matters: workbook guidance is encoded in comments, formatting, and runtime validation rather than native Excel validation lists/rules.
  - Relevant files: `tests/contracts/test_template_contract.py`, `src/excelalchemy/core/rendering.py`, `src/excelalchemy/core/writer.py`

## 3. Data and contract invariants

- **Excel metadata is attached to Pydantic fields without turning the field object into `FieldMetaInfo`.**
  - Why it matters: metadata remains decoupled from Pydantic field internals, which is part of the repository’s Pydantic v2 boundary design.
  - Relevant files: `tests/contracts/test_pydantic_contract.py`, `src/excelalchemy/metadata.py`, `src/excelalchemy/helper/pydantic.py`

- **Schema extraction flattens composite fields into ordered unique labels, keys, and offsets.**
  - Why it matters: merged headers, error targeting, and row reconstruction all depend on this flattened layout being stable and explicit.
  - Relevant files: `tests/contracts/test_pydantic_contract.py`, `tests/contracts/test_core_components_contract.py`, `src/excelalchemy/core/schema.py`, `src/excelalchemy/metadata.py`

- **Repeated child labels are valid when they belong to different parent labels.**
  - Why it matters: merged headers are identified by parent-plus-child identity, not by child label alone.
  - Relevant files: `tests/contracts/test_core_components_contract.py`, `src/excelalchemy/core/headers.py`, `src/excelalchemy/_primitives/header_models.py`

- **Row aggregation reconstructs composite columns back into parent-shaped payloads.**
  - Why it matters: flattened worksheet columns are not the final import payload; they must be grouped back into the logical model structure before validation and callbacks.
  - Relevant files: `tests/contracts/test_core_components_contract.py`, `src/excelalchemy/core/rows.py`

- **Storage readers are expected to return `WorksheetTable` from `src/excelalchemy/core/table.py` and preserve merged-header gaps as empty cells.**
  - Why it matters: header parsing depends on structural empties being preserved instead of collapsed away, and custom storage implementations follow the same table contract in the current 2.x line.
  - Relevant files: `tests/contracts/test_storage_contract.py`, `src/excelalchemy/core/storage_protocol.py`, `src/excelalchemy/core/storage_minio.py`, `src/excelalchemy/core/table.py`, `examples/custom_storage.py`

- **`ImportResult` has exactly three top-level result states: `SUCCESS`, `HEADER_INVALID`, and `DATA_INVALID`.**
  - Why it matters: downstream integrations and status helpers rely on this fixed result vocabulary.
  - Relevant files: `src/excelalchemy/results.py`, `tests/contracts/test_result_contract.py`

- **`ImportResult.from_validate_header_result(...)` is only valid for failed header validation.**
  - Why it matters: header validation and import execution are separate phases, and the conversion helper is intentionally constrained to invalid-header outcomes.
  - Relevant files: `tests/contracts/test_result_contract.py`, `src/excelalchemy/results.py`

- **Pydantic field-level validation errors become `ExcelCellError`; model-level validation errors become `ExcelRowError`.**
  - Why it matters: the library preserves the distinction between cell-specific problems and row-wide business-rule failures.
  - Relevant files: `tests/contracts/test_pydantic_contract.py`, `src/excelalchemy/helper/pydantic.py`, `src/excelalchemy/exceptions.py`

- **Missing-field and field-format validation messages are normalized into workbook-facing ExcelAlchemy errors.**
  - Why it matters: the repo treats error wording as part of the import contract rather than exposing raw Pydantic messages directly.
  - Relevant files: `tests/contracts/test_pydantic_contract.py`, `src/excelalchemy/helper/pydantic.py`

## 4. Localization and formatting invariants

- **Runtime exception messages are English-first in the 2.x line.**
  - Why it matters: Python-facing error text is intentionally stabilized in English even when workbook-facing text is localized.
  - Relevant files: `docs/locale.md`, `MIGRATIONS.md`, `src/excelalchemy/i18n/messages.py`

- **Workbook display locales currently support `zh-CN` and `en`, with `zh-CN` as the default workbook locale.**
  - Why it matters: workbook text is locale-aware, but the supported locale set is intentionally narrow and explicit today.
  - Relevant files: `docs/locale.md`, `src/excelalchemy/config.py`, `src/excelalchemy/i18n/messages.py`

- **Workbook-facing text falls back to the workbook default locale, while runtime and diagnostics fall back to English.**
  - Why it matters: different message layers have different fallback policies, and callers should not assume one global locale switch covers all output.
  - Relevant files: `docs/locale.md`, `src/excelalchemy/i18n/messages.py`

- **Workbook display locale controls import instructions, header comments, result/reason labels, row status text, and workbook-facing value text.**
  - Why it matters: localization is not limited to a few labels; it affects the visible workbook contract.
  - Relevant files: `docs/locale.md`, `tests/contracts/test_template_contract.py`, `tests/contracts/test_import_contract.py`, `src/excelalchemy/core/alchemy.py`, `src/excelalchemy/core/writer.py`

- **Developer diagnostics use named loggers and stable English log messages.**
  - Why it matters: logs are treated as a developer/operator surface distinct from API payloads and workbook display text.
  - Relevant files: `docs/locale.md`, `tests/unit/test_diagnostics_logging.py`, `src/excelalchemy/_primitives/diagnostics.py`, `src/excelalchemy/codecs/base.py`

- **Required template headers are visually distinguished and annotated with comments.**
  - Why it matters: user guidance in the workbook is part of the contract, not an optional extra.
  - Relevant files: `tests/contracts/test_template_contract.py`, `src/excelalchemy/metadata.py`, `src/excelalchemy/core/writer.py`, `src/excelalchemy/const.py`

- **Import result workbooks highlight failed cells in red.**
  - Why it matters: workbook feedback must remain visible and actionable for users correcting invalid rows.
  - Relevant files: `tests/contracts/test_import_contract.py`, `src/excelalchemy/core/writer.py`, `src/excelalchemy/const.py`

- **`excelalchemy.const` compatibility constants represent stable `zh-CN` defaults, not the full locale policy.**
  - Why it matters: locale-aware behavior should be driven by config locale, not by reading those constants as the source of truth.
  - Relevant files: `docs/locale.md`, `src/excelalchemy/const.py`, `src/excelalchemy/config.py`

## 5. Backward compatibility expectations

- **Deprecated compatibility modules remain available in the 2.x line but emit explicit deprecation warnings.**
  - Why it matters: migration paths are still supported, but callers are expected to move toward the newer public module layout.
  - Relevant files: `docs/public-api.md`, `MIGRATIONS.md`, `tests/unit/test_deprecation_policy.py`, `src/excelalchemy/types/`, `src/excelalchemy/exc.py`, `src/excelalchemy/identity.py`, `src/excelalchemy/header_models.py`

- **The `excelalchemy.types.*` compatibility namespace is scheduled for removal in ExcelAlchemy 3.0.**
  - Why it matters: it is preserved for 2.x migrations only and should not be treated as a long-term public namespace.
  - Relevant files: `docs/public-api.md`, `MIGRATIONS.md`, `tests/unit/test_deprecation_policy.py`

- **Legacy Minio config fields still work in 2.x, but they emit deprecation warnings and are no longer the recommended path.**
  - Why it matters: existing integrations continue to function, but new code should move to `storage=...`.
  - Relevant files: `MIGRATIONS.md`, `docs/public-api.md`, `tests/unit/test_config_options.py`, `src/excelalchemy/config.py`

- **Older import-inspection aliases remain available in 2.x.**
  - Why it matters: `df`, `header_df`, `cell_errors`, and `row_errors` still work as compatibility paths, even though the clearer names are preferred in new code.
  - Relevant files: `docs/public-api.md`, `MIGRATIONS.md`, `src/excelalchemy/core/alchemy.py`, `src/excelalchemy/core/import_session.py`

- **Compatibility warnings are expected to point to replacement import paths.**
  - Why it matters: the deprecation layer is not just a warning mechanism; it is part of the migration guidance built into the codebase.
  - Relevant files: `tests/unit/test_deprecation_policy.py`, `src/excelalchemy/_primitives/deprecation.py`, `src/excelalchemy/util/convertor.py`
