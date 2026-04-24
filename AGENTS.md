# AGENTS.md

## Related docs

- [README.md](README.md) for the user-facing overview and supported workflows.
- [docs/repo-map.md](docs/repo-map.md) for directory-level navigation.
- [docs/domain-model.md](docs/domain-model.md) for the library's main concepts and relationships.
- [docs/invariants.md](docs/invariants.md) for behavior that should not drift accidentally.
- [src/excelalchemy/README.md](src/excelalchemy/README.md) for implementation-oriented package structure.
- [tests/README.md](tests/README.md) for where behavior is protected.
- [examples/README.md](examples/README.md) for how examples should be interpreted.
- [plans/README.md](plans/README.md), [tech_debt/README.md](tech_debt/README.md), and [adr/README.md](adr/README.md) for execution planning, debt tracking, and architecture records.

## 1. Repository goal

- `ExcelAlchemy` is a schema-driven Python library for typed Excel import/export workflows built around Pydantic models.
- The repository centers on these user-facing flows:
  - template generation
  - workbook import validation
  - result workbook rendering
  - storage-backed upload/download
  - backend/API integration

## 2. Core domains and major components

- Package source: `src/excelalchemy/`
- Public facade and public surface:
  - `src/excelalchemy/__init__.py`
  - `src/excelalchemy/config.py`
  - `src/excelalchemy/metadata.py`
  - `src/excelalchemy/results.py`
  - `src/excelalchemy/exceptions.py`
  - `src/excelalchemy/artifacts.py`
- Internal workflow orchestration:
  - `src/excelalchemy/core/alchemy.py`
  - `src/excelalchemy/core/import_session.py`
  - `src/excelalchemy/core/schema.py`
  - `src/excelalchemy/core/headers.py`
  - `src/excelalchemy/core/rows.py`
  - `src/excelalchemy/core/executor.py`
  - `src/excelalchemy/core/rendering.py`
  - `src/excelalchemy/core/writer.py`
  - `src/excelalchemy/core/storage.py`
  - `src/excelalchemy/core/storage_protocol.py`
  - `src/excelalchemy/core/storage_minio.py`
  - `src/excelalchemy/core/table.py`
- Field semantics and type adapters:
  - `src/excelalchemy/codecs/`
- Pydantic integration boundary:
  - `src/excelalchemy/helper/pydantic.py`
- Locale and messages:
  - `src/excelalchemy/i18n/messages.py`
- Internal primitives and compatibility helpers:
  - `src/excelalchemy/_primitives/`
  - `src/excelalchemy/types/`
  - `src/excelalchemy/exc.py`
  - `src/excelalchemy/identity.py`
  - `src/excelalchemy/header_models.py`
  - `src/excelalchemy/const.py`
  - `src/excelalchemy/util/convertor.py`

## 3. Main entry points

- Main user entry point:
  - `excelalchemy.ExcelAlchemy`
- Main config entry points:
  - `excelalchemy.ImporterConfig`
  - `excelalchemy.ExporterConfig`
  - `excelalchemy.ImportMode`
- Main schema metadata entry points:
  - `excelalchemy.FieldMeta(...)`
  - `excelalchemy.ExcelMeta(...)`
- Main result entry points:
  - `excelalchemy.ImportResult`
  - `excelalchemy.CellErrorMap`
  - `excelalchemy.RowIssueMap`
- Main storage extension point:
  - `excelalchemy.ExcelStorage`
- Main runnable references:
  - `examples/README.md`
  - `examples/employee_import_workflow.py`
  - `examples/export_workflow.py`
  - `examples/custom_storage.py`
  - `examples/fastapi_reference/README.md`

## 4. Public API vs internal implementation

- Prefer these stable public modules in new code and docs:
  - `excelalchemy`
  - `excelalchemy.config`
  - `excelalchemy.metadata`
  - `excelalchemy.results`
  - `excelalchemy.exceptions`
  - `excelalchemy.codecs`
- Treat these as internal implementation details unless the task is explicitly about internals:
  - `excelalchemy.core.*`
  - `excelalchemy.helper.*`
  - `excelalchemy.i18n.*`
  - `excelalchemy._primitives.*`
- Treat these as 2.x compatibility-only imports:
  - `excelalchemy.exc`
  - `excelalchemy.identity`
  - `excelalchemy.header_models`
  - `excelalchemy.types.*`
  - `excelalchemy.util.convertor`
- Current 2.x storage seam:
  - `ExcelStorage` is public
  - custom `read_excel_table(...)` implementations currently return `WorksheetTable` from `src/excelalchemy/core/table.py`
  - treat that as a narrow extension seam, not as a general reason to import `excelalchemy.core.*` in application code
- In new code and docs, prefer:
  - `storage=...` over `minio=...`, `bucket_name=...`, `url_expires=...`
  - `worksheet_table` over `df`
  - `header_table` over `header_df`
  - `cell_error_map` over `cell_errors`
  - `row_error_map` over `row_errors`

## 5. Important constraints and invariants

- Stable public behavior is protected primarily by:
  - `tests/contracts/`
  - `tests/integration/`
- Examples are part of the user-facing contract:
  - `tests/integration/test_examples_smoke.py`
  - `scripts/smoke_examples.py`
- Result payloads and API-facing shapes are treated as stable 2.x surfaces:
  - `src/excelalchemy/results.py`
  - `docs/result-objects.md`
  - `docs/api-response-cookbook.md`
  - `scripts/smoke_api_payload_snapshot.py`
  - `files/example-outputs/import-failure-api-payload.json`
- Storage is a protocol boundary, not a Minio-only architecture:
  - `src/excelalchemy/core/storage_protocol.py`
  - `src/excelalchemy/core/storage.py`
  - `src/excelalchemy/core/storage_minio.py`
- The repo has explicitly moved away from pandas-first internals:
  - runtime workbook tables use `WorksheetTable`
  - see `src/excelalchemy/core/table.py`
- Locale behavior is explicit:
  - workbook-facing display locale supports `zh-CN` and `en`
  - runtime exceptions/messages are English-first in 2.x
  - see `docs/locale.md`
- Formula handling is server-side and `openpyxl`-based:
  - the library reads stored workbook values and does not run Excel
  - see `docs/limitations.md`
- Backward compatibility is active in 2.x:
  - deprecated modules and aliases still exist
  - legacy Minio config still works but emits deprecation warnings
  - see `MIGRATIONS.md`, `docs/public-api.md`, and `tests/unit/test_deprecation_policy.py`

## 6. Safe modification areas

- Documentation and cross-links:
  - `README.md`
  - `README-pypi.md`
  - `docs/*.md`
  - `examples/README.md`
  - `examples/fastapi_reference/README.md`
- Example scripts and reference app when the public usage story changes:
  - `examples/*.py`
  - `examples/fastapi_reference/*`
- Tests and fixtures that clarify intended behavior:
  - `tests/contracts/`
  - `tests/integration/`
  - `tests/unit/`
  - `tests/support/`
- Isolated field-type behavior when the change is codec-specific:
  - one module under `src/excelalchemy/codecs/`
  - matching tests under `tests/unit/codecs/`

## 7. Areas requiring extra caution

- Package root exports:
  - `src/excelalchemy/__init__.py`
  - changes here affect public imports directly
- Public config, metadata, results, and exceptions:
  - `src/excelalchemy/config.py`
  - `src/excelalchemy/metadata.py`
  - `src/excelalchemy/results.py`
  - `src/excelalchemy/exceptions.py`
- Core orchestration:
  - `src/excelalchemy/core/alchemy.py`
  - `src/excelalchemy/core/import_session.py`
  - `src/excelalchemy/core/schema.py`
  - `src/excelalchemy/core/headers.py`
  - `src/excelalchemy/core/rows.py`
  - `src/excelalchemy/core/executor.py`
- Storage boundary and compatibility behavior:
  - `src/excelalchemy/core/storage.py`
  - `src/excelalchemy/core/storage_protocol.py`
  - `src/excelalchemy/core/storage_minio.py`
  - `tests/contracts/test_storage_contract.py`
  - `tests/unit/test_config_options.py`
- Compatibility shims and deprecation policy:
  - `src/excelalchemy/types/`
  - `src/excelalchemy/exc.py`
  - `src/excelalchemy/identity.py`
  - `src/excelalchemy/header_models.py`
  - `src/excelalchemy/util/convertor.py`
  - `tests/unit/test_deprecation_policy.py`
- Locale and message wording:
  - `src/excelalchemy/i18n/messages.py`
  - `docs/locale.md`
- Generated outputs and docs smoke dependencies:
  - `files/example-outputs/`
  - `scripts/generate_example_output_assets.py`
  - `scripts/smoke_docs_assets.py`
  - `scripts/smoke_api_payload_snapshot.py`

## 8. Preferred workflow for making changes

- Start from the repo docs that define the area you are changing:
  - `README.md`
  - `docs/architecture.md`
  - `docs/public-api.md`
  - `docs/result-objects.md`
  - `docs/api-response-cookbook.md`
  - `docs/locale.md`
  - `docs/limitations.md`
- Read the matching contract and integration tests before changing behavior:
  - `tests/contracts/`
  - `tests/integration/`
- Prefer the recommended 2.x constructors and API shapes already used in examples:
  - `ImporterConfig.for_create`
  - `ImporterConfig.for_update`
  - `ImporterConfig.for_create_or_update`
  - `ExporterConfig.for_storage`
- Keep new code on stable public imports unless the task is explicitly internal.
- When behavior changes, update:
  - source
  - the nearest tests
  - the docs/examples that teach that behavior
  - generated assets or smoke expectations if needed
- Validate with the repo’s normal commands:
  - `uv run ruff format --check .`
  - `uv run ruff check .`
  - `uv run pyright`
  - `uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests`
  - `uv run python scripts/smoke_package.py`
  - `uv run python scripts/smoke_examples.py`
  - `uv run python scripts/smoke_docs_assets.py`
  - `uv run python scripts/smoke_api_payload_snapshot.py`

## 9. Documentation that must be updated when behavior changes

- Update `README.md` and `README-pypi.md` when the onboarding story, examples, or recommended API shape changes.
- Update `docs/public-api.md` when stable vs internal vs compatibility boundaries change.
- Update `MIGRATIONS.md` when migration guidance, deprecated paths, or recommended replacements change.
- Keep GitHub release notes concise and readable; detailed release documentation can live under `docs/releases/`.
- Update `docs/architecture.md` when component responsibilities or workflow boundaries change.
- Update `docs/result-objects.md` and `docs/api-response-cookbook.md` when result objects or payload shapes change.
- Update `docs/locale.md` when locale behavior or message policy changes.
- Update `docs/limitations.md` or `docs/performance.md` when operational constraints or runtime expectations change.
- Update `examples/README.md` and `examples/fastapi_reference/README.md` when examples or reference layouts change.
- Regenerate `files/example-outputs/` with `scripts/generate_example_output_assets.py` when captured example output changes intentionally.
- Keep `scripts/smoke_docs_assets.py` and `scripts/smoke_api_payload_snapshot.py` passing after doc or payload changes.

## 10. Prohibited or discouraged changes

- Do not present internal modules under `excelalchemy.core.*`, `excelalchemy.helper.*`, `excelalchemy.i18n.*`, or `excelalchemy._primitives.*` as stable application-facing API in docs or examples.
- Do not reintroduce pandas-first internals or docs; the repo explicitly uses `openpyxl + WorksheetTable`.
- Do not hard-wire Minio into the core architecture; storage is modeled as `ExcelStorage`.
- Do not remove compatibility imports, deprecated module paths, or old facade aliases casually; 2.x still documents and tests them.
- Do not switch new docs/examples back to legacy config names when `storage=...` is sufficient.
- Do not invent new documentation-site, release, or smoke-test workflows that are not already represented by `docs/`, `scripts/`, and `.github/workflows/`.
- Do not make claims in docs/examples that conflict with `docs/limitations.md`, `docs/locale.md`, or the tested result payloads.
