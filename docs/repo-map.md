# Repository Map

This file is a compact map of the `ExcelAlchemy` repository.
It is meant to help both humans and coding agents find the right files before making changes.

## Related docs

- [../README.md](../README.md) for the public-facing overview.
- [../AGENTS.md](../AGENTS.md) for repo-local editing guidance.
- [domain-model.md](domain-model.md) for the core concepts behind these directories.
- [invariants.md](invariants.md) for behavior that should stay stable.
- [../src/excelalchemy/README.md](../src/excelalchemy/README.md) for the implementation structure inside the main package.
- [../tests/README.md](../tests/README.md) and [../examples/README.md](../examples/README.md) for the executable contract surface.

## Top-Level Layout

- `src/`
  - Main package source for the library.
  - Most code changes should start here.
- `tests/`
  - Contract, integration, and unit coverage.
  - Use this to confirm intended behavior before changing code.
- `examples/`
  - Runnable reference workflows and a small FastAPI reference app.
  - These are part of the user-facing contract, not throwaway demos.
- `docs/`
  - Markdown documentation for architecture, public API, result objects, limits, performance, and onboarding.
- `scripts/`
  - Smoke checks and asset-generation helpers used to validate docs, examples, and package behavior.
- `files/`
  - Example workbooks and generated example outputs used by docs and smoke scripts.
- `images/`
  - Screenshots used by `README.md` and `README-pypi.md`.
- `.github/`
  - CI, publish workflows, and issue/PR templates.

## Important Root Files

- `README.md`
  - Main project overview and best entry point for understanding the library.
- `README-pypi.md`
  - PyPI-facing summary; should stay aligned with the main onboarding story.
- `README_cn.md`
  - Chinese-language README.
- `ABOUT.md`
  - Design rationale, architectural intent, and evolution notes.
- `MIGRATIONS.md`
  - Compatibility and upgrade guidance for the 2.x line.
- `CHANGELOG.md`
  - Release history and notable behavior/documentation changes.
- `AGENTS.md`
  - Agent-focused guidance for safe navigation and modification.
- `pyproject.toml`
  - Packaging, dependencies, Ruff, Pyright, and pytest configuration.
- `uv.lock`
  - Locked dependency state for `uv`.

## Package Source: `src/excelalchemy/`

- `src/excelalchemy/__init__.py`
  - Main public package surface.
  - Re-exports the facade, configs, codecs, result objects, exceptions, and common types.
- `src/excelalchemy/config.py`
  - Public configuration objects:
  - `ImporterConfig`
  - `ExporterConfig`
  - `ImportMode`
- `src/excelalchemy/metadata.py`
  - Public field metadata entry points:
  - `FieldMeta(...)`
  - `ExcelMeta(...)`
  - Also contains the layered metadata model behind `FieldMetaInfo`.
- `src/excelalchemy/results.py`
  - Public import result objects and API-friendly error maps:
  - `ImportResult`
  - `CellErrorMap`
  - `RowIssueMap`
- `src/excelalchemy/exceptions.py`
  - Public exceptions such as `ConfigError`, `ExcelCellError`, `ExcelRowError`, and `ProgrammaticError`.
- `src/excelalchemy/artifacts.py`
  - Public `ExcelArtifact` wrapper for bytes, data URLs, and related helpers.

## Internal Implementation: `src/excelalchemy/core/`

- `src/excelalchemy/core/alchemy.py`
  - Main facade implementation behind `excelalchemy.ExcelAlchemy`.
  - Good starting point for understanding how import, export, template generation, and storage fit together.
- `src/excelalchemy/core/import_session.py`
  - One-shot import runtime state and lifecycle.
  - Central to the import execution path.
- `src/excelalchemy/core/schema.py`
  - Builds flattened Excel-facing schema layout from Pydantic models.
- `src/excelalchemy/core/headers.py`
  - Parses and validates simple and merged workbook headers.
- `src/excelalchemy/core/rows.py`
  - Aggregates worksheet rows back into model-shaped payloads and tracks row/cell issues.
- `src/excelalchemy/core/executor.py`
  - Validates row payloads and dispatches create/update/create-or-update callbacks.
- `src/excelalchemy/core/rendering.py`
  - High-level rendering entry points for templates, exports, and import result workbooks.
- `src/excelalchemy/core/writer.py`
  - Lower-level workbook writing logic used by rendering.
- `src/excelalchemy/core/storage_protocol.py`
  - `ExcelStorage` protocol; the main storage extension point.
- `src/excelalchemy/core/storage.py`
  - Storage gateway resolution and fallback behavior.
- `src/excelalchemy/core/storage_minio.py`
  - Built-in Minio-backed storage implementation.
- `src/excelalchemy/core/table.py`
  - Internal `WorksheetTable` abstraction used instead of pandas.

## Field Codecs: `src/excelalchemy/codecs/`

- `src/excelalchemy/codecs/base.py`
  - Base codec abstractions:
  - `ExcelFieldCodec`
  - `CompositeExcelFieldCodec`
- `src/excelalchemy/codecs/*.py`
  - Built-in field codec implementations behind public aliases such as `Email`, `NumberRange`, and `DateRange`:
  - `string.py`
  - `number.py`
  - `date.py`
  - `date_range.py`
  - `money.py`
  - `email.py`
  - `phone_number.py`
  - `url.py`
  - `radio.py`
  - `multi_checkbox.py`
  - `organization.py`
  - `staff.py`
  - `tree.py`
- `src/excelalchemy/codecs/__init__.py`
  - Small registry helpers for choice-oriented codecs.

## Internal Support Modules

- `src/excelalchemy/helper/pydantic.py`
  - Pydantic adaptation boundary.
  - Important for metadata extraction and mapping validation errors back into ExcelAlchemy errors.
- `src/excelalchemy/i18n/messages.py`
  - Runtime and workbook display messages.
  - Important when changing wording, message keys, or locale behavior.
- `src/excelalchemy/_primitives/`
  - Internal constants, identity wrappers, payload aliases, diagnostics, and deprecation helpers.
  - Important files include:
  - `src/excelalchemy/_primitives/constants.py`
  - `src/excelalchemy/_primitives/identity.py`
  - `src/excelalchemy/_primitives/payloads.py`
  - `src/excelalchemy/_primitives/diagnostics.py`
  - `src/excelalchemy/_primitives/deprecation.py`
  - `src/excelalchemy/_primitives/header_models.py`

## Compatibility Layer

- `src/excelalchemy/types/`
  - Deprecated compatibility namespace retained in the 2.x line.
- `src/excelalchemy/exc.py`
  - Compatibility shim for `excelalchemy.exceptions`.
- `src/excelalchemy/identity.py`
  - Compatibility shim for root-level identity exports.
- `src/excelalchemy/header_models.py`
  - Compatibility shim for internal header models.
- `src/excelalchemy/const.py`
  - Compatibility/low-level constants surface.
- `src/excelalchemy/util/convertor.py`
  - Deprecated compatibility shim for `excelalchemy.util.converter`.

These compatibility paths remain in the 2.x line, but they are not the preferred starting points for new code.

## Documentation: `docs/`

- `docs/getting-started.md`
  - Fastest path for new users.
- `docs/public-api.md`
  - Stable public modules vs compatibility vs internal modules.
- `docs/architecture.md`
  - Component map and workflow map.
- `docs/result-objects.md`
  - Import result objects and API-facing error maps.
- `docs/api-response-cookbook.md`
  - Example backend response shapes.
- `docs/locale.md`
  - Locale policy for workbook-facing text and runtime messages.
- `docs/limitations.md`
  - Practical runtime limits and non-goals.
- `docs/performance.md`
  - Operational expectations and performance notes.
- `docs/integration-roadmap.md`
  - Role-based reading path.
- `docs/tool-comparison.md`
  - Positioning against other tool categories.
- `docs/repo-map.md`
  - This repository map.
- `docs/releases/`
  - Release notes for specific versions.

## Examples: `examples/`

- `examples/README.md`
  - Recommended reading order for examples.
- `examples/annotated_schema.py`
  - Modern `Annotated[..., ExcelMeta(...)]` declaration style.
- `examples/employee_import_workflow.py`
  - Core import workflow.
- `examples/create_or_update_import.py`
  - Create-or-update import mode.
- `examples/export_workflow.py`
  - Export flow and artifact upload behavior.
- `examples/custom_storage.py`
  - Minimal custom `ExcelStorage` example.
  - Also shows the current 2.x storage seam where readers return `WorksheetTable` from `src/excelalchemy/core/table.py`.
- `examples/minio_storage.py`
  - Built-in Minio path example for the current 2.x line.
  - Uses internal storage modules to demonstrate the built-in Minio compatibility path, not the preferred new-code API shape.
- `examples/fastapi_upload.py`
  - Single-file FastAPI integration sketch.
- `examples/fastapi_reference/`
  - More complete reference layout for a backend integration:
  - `app.py`
  - `models.py`
  - `schemas.py`
  - `responses.py`
  - `presenters.py`
  - `services.py`
  - `storage.py`
  - `README.md`

## Tests: `tests/`

- `tests/contracts/`
  - Public behavior and compatibility contracts.
  - Best starting point for understanding what should remain stable.
- `tests/integration/`
  - Workflow-level and example-level tests.
- `tests/unit/`
  - Focused logic tests for codecs, metadata, config, diagnostics, and other helpers.
- `tests/support/`
  - Shared test models, fixtures, in-memory storage, and workbook helpers.
- `tests/files/`
  - Workbook fixtures used by tests.

## Scripts: `scripts/`

- `scripts/smoke_package.py`
  - Installed-package smoke test.
- `scripts/smoke_examples.py`
  - Example smoke test.
- `scripts/smoke_docs_assets.py`
  - Docs and generated asset smoke test.
- `scripts/smoke_api_payload_snapshot.py`
  - Stable payload snapshot smoke test.
- `scripts/generate_example_output_assets.py`
  - Regenerates captured example output assets.
- `scripts/generate_portfolio_assets.py`
  - Generates portfolio/demo assets.

## Supporting Assets

- `files/example-outputs/`
  - Generated text and JSON outputs referenced by docs and smoke scripts.
- `files/*.xlsx`
  - Example workbook assets.
- `images/`
  - Screenshots shown in README files.

## Public API vs Internal Implementation

- Public API starting points:
  - `src/excelalchemy/__init__.py`
  - `src/excelalchemy/config.py`
  - `src/excelalchemy/metadata.py`
  - `src/excelalchemy/results.py`
  - `src/excelalchemy/exceptions.py`
  - `src/excelalchemy/codecs/`
- Internal implementation starting points:
  - `src/excelalchemy/core/alchemy.py`
  - `src/excelalchemy/core/import_session.py`
  - `src/excelalchemy/core/schema.py`
  - `src/excelalchemy/core/headers.py`
  - `src/excelalchemy/core/rows.py`
  - `src/excelalchemy/core/executor.py`

## Most Important Code Paths

- Public facade and configuration:
  - `src/excelalchemy/__init__.py`
  - `src/excelalchemy/config.py`
  - `src/excelalchemy/metadata.py`
  - `src/excelalchemy/results.py`
- Import flow:
  - `src/excelalchemy/core/alchemy.py`
  - `src/excelalchemy/core/import_session.py`
  - `src/excelalchemy/core/headers.py`
  - `src/excelalchemy/core/rows.py`
  - `src/excelalchemy/core/executor.py`
  - `src/excelalchemy/helper/pydantic.py`
- Export and template generation:
  - `src/excelalchemy/core/alchemy.py`
  - `src/excelalchemy/core/schema.py`
  - `src/excelalchemy/core/rendering.py`
  - `src/excelalchemy/core/writer.py`
  - `src/excelalchemy/codecs/`
- Storage integration:
  - `src/excelalchemy/core/storage_protocol.py`
  - `src/excelalchemy/core/storage.py`
  - `src/excelalchemy/core/storage_minio.py`
  - `src/excelalchemy/core/table.py`
  - `examples/custom_storage.py`
- Result payloads and API responses:
  - `src/excelalchemy/results.py`
  - `docs/result-objects.md`
  - `docs/api-response-cookbook.md`

## Likely Starting Points for Common Tasks

- Understanding the public API:
  - `README.md`
  - `docs/getting-started.md`
  - `docs/public-api.md`
  - `src/excelalchemy/__init__.py`
  - `src/excelalchemy/config.py`
  - `src/excelalchemy/metadata.py`
  - `src/excelalchemy/results.py`

- Understanding import flow:
  - `docs/architecture.md`
  - `examples/employee_import_workflow.py`
  - `src/excelalchemy/core/alchemy.py`
  - `src/excelalchemy/core/import_session.py`
  - `src/excelalchemy/core/headers.py`
  - `src/excelalchemy/core/rows.py`
  - `src/excelalchemy/core/executor.py`
  - `tests/contracts/test_import_contract.py`

- Understanding export and template generation:
  - `examples/export_workflow.py`
  - `src/excelalchemy/core/alchemy.py`
  - `src/excelalchemy/core/schema.py`
  - `src/excelalchemy/core/rendering.py`
  - `src/excelalchemy/core/writer.py`
  - `tests/contracts/test_template_contract.py`
  - `tests/contracts/test_export_contract.py`

- Understanding storage integration:
  - `docs/public-api.md`
  - `src/excelalchemy/core/storage_protocol.py`
  - `src/excelalchemy/core/storage.py`
  - `src/excelalchemy/core/storage_minio.py`
  - `src/excelalchemy/core/table.py`
  - `examples/custom_storage.py`
  - `tests/contracts/test_storage_contract.py`

- Understanding tests:
  - `tests/contracts/`
  - `tests/integration/`
  - `tests/unit/`
  - `tests/support/`
  - Start with:
  - `tests/contracts/test_import_contract.py`
  - `tests/contracts/test_export_contract.py`
  - `tests/contracts/test_template_contract.py`
  - `tests/contracts/test_storage_contract.py`
  - `tests/contracts/test_result_contract.py`
  - `tests/contracts/test_pydantic_contract.py`
