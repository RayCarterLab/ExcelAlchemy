# Repository Map

This file is a compact map of the `ExcelAlchemy` repository.
It is meant to help both humans and coding agents find the right files before making changes.

## Related docs

- [../README.md](../README.md) for the public-facing overview.
- [../AGENTS.md](../AGENTS.md) for repo-local editing guidance.
- [agent/coding-agent-guide.md](agent/coding-agent-guide.md) for a
  coding-agent-oriented project brief.
- [domain-model.md](domain-model.md) for the core concepts behind these directories.
- [agent/invariants.md](agent/invariants.md) for behavior that should stay stable.
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
  - Human documentation, agent rules, history, release notes, and technical debt records.
- `harness/`
  - Agent-facing deterministic runtime, machine-readable context, local tools,
    evaluators, task plans, and ignored run artifacts.
- `scripts/`
  - Smoke checks and asset-generation helpers used to validate docs, examples, and package behavior.
- `.github/`
  - CI, publish workflows, and issue/PR templates.

## Important Root Files

- `README.md`
  - Main project overview and best entry point for understanding the library.
- `README-pypi.md`
  - PyPI-facing summary; should stay aligned with the main onboarding story.
- `README_cn.md`
  - Chinese-language README.
- `CHANGELOG.md`
  - Release history and notable behavior/documentation changes.
- `AGENTS.md`
  - Agent-focused guidance for safe navigation and modification.
- `docs/agent/coding-agent-guide.md`
  - Coding-agent-oriented project brief, public contract summary, and task routing guide.
- `pyproject.toml`
  - Packaging, dependencies, Ruff, Pyright, and pytest configuration.
- `uv.lock`
  - Locked dependency state for `uv`.

## Package Source: `src/excelalchemy/`

- `src/excelalchemy/__init__.py`
  - Main public package surface.
  - Re-exports the facade, configs, codecs, result objects, errors, and common types.
- `src/excelalchemy/config/`
  - Public configuration objects:
  - `ImporterConfig`
  - `ExporterConfig`
  - `ImportMode`
- `src/excelalchemy/columns.py`
  - Public `ExcelColumn(...)` declaration helper and immutable column specs.
- `src/excelalchemy/field_metadata/`
  - Resolved runtime metadata model behind `FieldMetaInfo`.
- `src/excelalchemy/results/`
  - Public import result objects and API-friendly error maps:
  - `ImportResult`
  - `CellErrorMap`
  - `RowIssueMap`
- `src/excelalchemy/errors.py`
  - Public exceptions such as `ConfigError`, `ExcelCellError`, `ExcelRowError`, and `ProgrammaticError`.
- `src/excelalchemy/artifacts.py`
  - Public `ExcelArtifact` wrapper for bytes, data URLs, and related helpers.

## Implementation Areas: `src/excelalchemy/`

- `src/excelalchemy/runtime/facade.py`
  - Main facade implementation behind `excelalchemy.ExcelAlchemy`.
  - Good starting point for understanding how import, export, template generation, and storage fit together.
- `src/excelalchemy/runtime/import_session.py`
  - One-shot import runtime state and lifecycle.
  - Central to the import execution path.
- `src/excelalchemy/runtime/preflight.py`
  - Read-only structural preflight workflow.
- `src/excelalchemy/schema/layout.py`
  - Builds flattened Excel-facing schema layout from Pydantic models.
- `src/excelalchemy/worksheet/header.py`
  - Normalized worksheet header record.
- `src/excelalchemy/worksheet/header_parser.py`
  - Parses simple and merged worksheet headers.
- `src/excelalchemy/worksheet/header_validator.py`
  - Validates parsed worksheet headers against schema layout.
- `src/excelalchemy/runtime/rows.py`
  - Aggregates worksheet rows back into model-shaped payloads and tracks row/cell issues.
- `src/excelalchemy/runtime/executor.py`
  - Validates row payloads and dispatches create/update/create-or-update callbacks.
- `src/excelalchemy/rendering/renderer.py`
  - High-level rendering entry points for templates, exports, and import result workbooks.
- `src/excelalchemy/rendering/writer.py`
  - Lower-level workbook writing logic used by rendering.
- `src/excelalchemy/storage/`
  - `ExcelStorage` protocol; the main storage extension point.
- `src/excelalchemy/storage/gateway.py`
  - Storage gateway resolution and missing-storage fallback behavior.
- `src/excelalchemy/storage/minio.py`
  - Built-in Minio-backed storage implementation.
- `src/excelalchemy/worksheet/table.py`
  - Internal `WorksheetTable` abstraction used instead of pandas.

## Field Codecs: `src/excelalchemy/codecs/`

- `src/excelalchemy/codecs/field_codec.py`
  - Base codec abstractions and immutable helper specs:
  - `ExcelFieldCodec`
  - `CompositeExcelFieldCodec`
  - `ExcelFieldCodecSpec`
- `src/excelalchemy/codecs/*.py`
  - Built-in codec implementations and public helper factories. Internal
    implementations use `*FieldCodec`; public helpers use `*Codec`.
  - `text.py`
  - `number.py`
  - `date.py`
  - `date_range.py`
  - `email.py`
  - `phone_number.py`
  - `url.py`
  - `choice.py`
- `src/excelalchemy/codecs/__init__.py`
  - Public built-in codec helper exports.

## Internal Support Modules

- `src/excelalchemy/adapters/pydantic.py`
  - Pydantic adaptation boundary.
  - Important for metadata extraction and mapping validation errors back into ExcelAlchemy errors.
- `src/excelalchemy/messages.py`
  - Runtime and workbook display messages.
  - Important when changing wording, message keys, or locale behavior.
- `src/excelalchemy/primitives/`
  - Internal constants, identity wrappers, and payload aliases.
  - Important files include:
  - `src/excelalchemy/primitives/constants.py`
  - `src/excelalchemy/primitives/identity.py`
  - `src/excelalchemy/primitives/payloads.py`

## Removed 2.x Compatibility Layer

The 3.0 codebase no longer contains the old compatibility modules
`excelalchemy.types`, `excelalchemy.exc`, `excelalchemy.identity`,
`excelalchemy.header_models`, `excelalchemy.const`, or
`excelalchemy.util.convertor`. It also no longer contains the transitional
bridge packages `excelalchemy.core`, `excelalchemy.helper`, `excelalchemy.i18n`,
or `excelalchemy._primitives`.

These compatibility paths are removed in 3.0.

## Documentation: `docs/`

- `docs/getting-started.md`
  - Fastest path for new users.
- `docs/about.md`
  - Design rationale, architectural intent, and evolution notes.
- `docs/migrations.md`
  - Compatibility and upgrade guidance.
- `docs/public-api.md`
  - Stable public modules and removed 2.x paths.
- `docs/platform-code-mapping.md`
  - Human platform-to-code ownership map.
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
- `docs/agent/`
  - Authoritative agent workflow, boundary, invariant, testing, and review rules.
  - Start with `docs/agent/coding-agent-guide.md` when a coding agent needs the
    project-level README equivalent before choosing files.
- `docs/history/`
  - Archived plans and historical ADRs; not current rules.
- `docs/tech-debt/`
  - Maintenance debt records.

## Examples: `examples/`

- `examples/README.md`
  - Recommended reading order for examples.
- `examples/annotated_schema.py`
  - Current `Annotated[..., ExcelColumn(...)]` declaration style.
- `examples/employee_import_workflow.py`
  - Core import workflow.
- `examples/create_or_update_import.py`
  - Create-or-update import mode.
- `examples/export_workflow.py`
  - Export flow and artifact upload behavior.
- `examples/custom_storage.py`
  - Minimal custom `ExcelStorage` example.
  - Shows the storage seam where readers return `WorksheetTable`.
- `examples/minio_storage.py`
  - Built-in Minio-compatible storage example.
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
  - `storage/`
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

- `docs/assets/images/`
  - Screenshots used by `README.md`, `README-pypi.md`, and `docs/examples-showcase.md`.
- `docs/assets/example-outputs/`
  - Generated text and JSON outputs referenced by docs and smoke scripts.
- `docs/assets/workbooks/portfolio/`
  - Generated portfolio/demo workbook assets used by documentation screenshots.
- `docs/assets/workbooks/legacy/`
  - Legacy workbook samples kept as documentation assets.

## Agent Harness: `harness/`

- `harness/loop.py`
  - Deterministic workflow controller and structured agent output schemas.
- `harness/state.py`
  - Serializable run state, step records, retry state, and fix-context aggregation.
- `harness/runner.py`
  - Public entry point for running one harness task.
- `harness/context.py`
  - Loader for machine-readable context under `harness/context_data/`.
- `harness/context_data/`
  - Runtime instruction, architecture, and validation context loaded by the harness.
- `harness/evaluators/`
  - Local evaluation adapters used by the deterministic harness.
- `harness/tools/`
  - Harness-facing deterministic local tool definitions and adapters.
- `harness/plans/`
  - Harness task-plan template plus active/archive runtime plan artifacts.
- `harness/runs/`
  - Ignored harness run-state artifacts.

## Public API vs Internal Implementation

- Public API starting points:
  - `src/excelalchemy/__init__.py`
  - `src/excelalchemy/config/`
  - `src/excelalchemy/field_metadata/`
  - `src/excelalchemy/results/`
  - `src/excelalchemy/errors.py`
  - `src/excelalchemy/codecs/`
- Internal implementation starting points:
  - `src/excelalchemy/runtime/facade.py`
  - `src/excelalchemy/runtime/import_session.py`
  - `src/excelalchemy/schema/layout.py`
  - `src/excelalchemy/worksheet/header_parser.py`
  - `src/excelalchemy/worksheet/header_validator.py`
  - `src/excelalchemy/runtime/rows.py`
  - `src/excelalchemy/runtime/executor.py`

## Most Important Code Paths

- Public facade and configuration:
  - `src/excelalchemy/__init__.py`
  - `src/excelalchemy/config/`
  - `src/excelalchemy/field_metadata/`
  - `src/excelalchemy/results/`
- Import flow:
  - `src/excelalchemy/runtime/facade.py`
  - `src/excelalchemy/runtime/import_session.py`
  - `src/excelalchemy/worksheet/header_parser.py`
  - `src/excelalchemy/worksheet/header_validator.py`
  - `src/excelalchemy/runtime/rows.py`
  - `src/excelalchemy/runtime/executor.py`
  - `src/excelalchemy/adapters/pydantic.py`
- Export and template generation:
  - `src/excelalchemy/runtime/facade.py`
  - `src/excelalchemy/schema/layout.py`
  - `src/excelalchemy/rendering/renderer.py`
  - `src/excelalchemy/rendering/writer.py`
  - `src/excelalchemy/codecs/`
- Storage integration:
  - `src/excelalchemy/storage/`
  - `src/excelalchemy/storage/gateway.py`
  - `src/excelalchemy/storage/minio.py`
  - `src/excelalchemy/worksheet/table.py`
  - `examples/custom_storage.py`
- Result payloads and API responses:
  - `src/excelalchemy/results/`
  - `docs/result-objects.md`
  - `docs/api-response-cookbook.md`

## Likely Starting Points for Common Tasks

- Understanding the public API:
  - `README.md`
  - `docs/getting-started.md`
  - `docs/public-api.md`
  - `src/excelalchemy/__init__.py`
  - `src/excelalchemy/config/`
  - `src/excelalchemy/field_metadata/`
  - `src/excelalchemy/results/`

- Understanding import flow:
  - `docs/platform-code-mapping.md`
  - `examples/employee_import_workflow.py`
  - `src/excelalchemy/runtime/facade.py`
  - `src/excelalchemy/runtime/import_session.py`
  - `src/excelalchemy/worksheet/header_parser.py`
  - `src/excelalchemy/worksheet/header_validator.py`
  - `src/excelalchemy/runtime/rows.py`
  - `src/excelalchemy/runtime/executor.py`
  - `tests/contracts/test_import_contract.py`

- Understanding export and template generation:
  - `examples/export_workflow.py`
  - `src/excelalchemy/runtime/facade.py`
  - `src/excelalchemy/schema/layout.py`
  - `src/excelalchemy/rendering/renderer.py`
  - `src/excelalchemy/rendering/writer.py`
  - `tests/contracts/test_template_contract.py`
  - `tests/contracts/test_export_contract.py`

- Understanding storage integration:
  - `docs/public-api.md`
  - `src/excelalchemy/storage/`
  - `src/excelalchemy/storage/gateway.py`
  - `src/excelalchemy/storage/minio.py`
  - `src/excelalchemy/worksheet/table.py`
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
