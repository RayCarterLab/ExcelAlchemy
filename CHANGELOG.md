# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog and versioned according to PEP 440.

## [2.4.0] - 2026-04-24

### Added

- Added `docs/platform-architecture.md`
- Added `docs/runtime-model.md`
- Added `docs/integration-blueprints.md`

### Changed

- Improved the documentation structure for the import platform model
- Unified repository-facing terminology around the import workflow
- Clarified the import workflow as:
  - template authoring
  - preflight gate
  - import runtime
  - result intelligence
  - artifact and delivery

### Internal

- Completed minimal platform alignment for docs and low-risk code comments
- Improved documentation cross-linking across README, API, result, and
  integration docs

## [2.3.0] - 2026-04-23

This release continues the stable 2.x line with a more complete import
workflow: clearer template guidance before upload, lightweight structural
preflight before execution, synchronous lifecycle visibility during import, and
compact remediation-oriented payloads after failures.

### Added

- Added additive template UX metadata support through `hint=` and
  `example_value=` so generated header comments can provide clearer workbook
  input guidance
- Added `ExcelAlchemy.preflight_import(...)` for lightweight structural import
  validation before full import execution
- Added `ImportPreflightResult` and `ImportPreflightStatus` as stable public
  preflight result types
- Added additive `on_event=` support on `ExcelAlchemy.import_data(...)` for
  synchronous import lifecycle callbacks
- Added `build_frontend_remediation_payload(...)` for compact retry-oriented
  remediation payloads alongside the existing import result surfaces
- Added a dedicated `WorksheetNotFoundError` exception so sheet-missing
  preflight classification does not rely on backend-specific message parsing

### Changed

- Extended the import workflow so applications can combine template guidance,
  preflight validation, lifecycle event observation, and remediation payloads
  without replacing the existing full import API
- Kept `ExcelAlchemy.import_data(...)` as the full validation and execution
  path while clarifying that `preflight_import(...)` is structural only
- Updated storage-backed workbook reading so preflight maps only explicit
  worksheet-missing failures to `SHEET_MISSING` and re-raises unrelated
  storage/runtime failures
- Refined template comment rendering for single-staff guidance formatting
- Expanded contract coverage for:
  - preflight header validation
  - missing and extra field handling
  - row-count estimation
  - import lifecycle event payloads
  - remediation payload behavior

### Documentation

- Updated `README.md`, `README-pypi.md`, and onboarding docs to describe the
  additive template guidance metadata
- Updated `docs/getting-started.md` with practical preflight usage guidance and
  a `preflight -> import` workflow example
- Updated `docs/public-api.md` and `docs/result-objects.md` to document
  `preflight_import(...)`, `ImportPreflightResult`, lifecycle callbacks, and
  remediation payload helpers
- Updated `docs/architecture.md`, `docs/domain-model.md`, examples, and
  reference-app guidance to reflect the broader import workflow story
- Added design plans under `plans/` for:
  - template UX metadata v1
  - job-friendly import lifecycle events v1
  - import preflight v1
  - front-end remediation payload v1

## [2.2.8] - 2026-04-05

This release continues the stable 2.x line with a clearer integration reading
path, stronger API payload smoke verification, and a more production-shaped
reference-app release flow.

### Added

- Added `docs/integration-roadmap.md` to give new adopters a role-based reading
  path for first-time integration, backend APIs, frontend error rendering, and
  migration work
- Added `scripts/smoke_api_payload_snapshot.py` and a generated
  `import-failure-api-payload.json` snapshot under `files/example-outputs/`

### Changed

- Expanded release smoke so wheel and source-distribution verification now
  compare a stable import-failure API payload snapshot instead of only checking
  ad hoc fields
- Extended release verification so installed-package smoke runs the
  `examples.fastapi_reference.app` demo directly after dependency installation
- Cross-linked the new integration roadmap from onboarding, API-facing, and
  PyPI-facing docs

### Compatibility Notes

- No public import or export workflow API was removed in this release
- `ImportResult`, `CellErrorMap`, and `RowIssueMap` remain the stable public
  result objects for 2.x integrations
- `storage=...` remains the recommended 2.x backend configuration path

### Release Summary

- new users now have a clearer “what to read first” path
- release smoke now checks a stable import-failure payload shape
- installed-package verification exercises the FastAPI reference app more
  directly

## [2.2.7] - 2026-04-04

This release continues the stable 2.x line with stronger API-facing result
payloads, a more complete FastAPI reference application, harder install-time
smoke verification, and more consistent codec diagnostics.

### Added

- Added `docs/api-response-cookbook.md` with copyable success, data-invalid,
  and header-invalid response shapes for backend integrations
- Added request and response contract modules for the FastAPI reference app
  under `examples/fastapi_reference/schemas.py` and
  `examples/fastapi_reference/responses.py`
- Added `scripts/smoke_docs_assets.py` to verify showcase assets and critical
  result-object/showcase documentation entry points
- Added logger consistency tests for codec fallback diagnostics

### Changed

- Extended `ImportResult`, `CellErrorMap`, and `RowIssueMap` payload guidance
  so `code`, `message_key`, `message`, and `display_message` have clearer and
  more stable frontend-facing roles
- Strengthened `CellErrorMap` and `RowIssueMap` with summary helpers for
  aggregation by field, row, and machine-readable code
- Made `ImportResult.to_api_payload()` a stable top-level integration surface
  for success, data-invalid, and header-invalid responses
- Expanded the FastAPI reference app into a more copyable minimal application
  with request schema, response schema, structured response builder, and
  cookbook-aligned payloads
- Hardened release smoke verification so installed-package checks now cover:
  - successful imports
  - failed imports
  - structured error payloads
  - example asset generation
  - result-object and showcase docs
  - FastAPI reference HTTP behavior after dependency installation
- Unified codec fallback logging under the `excelalchemy.codecs` logger and
  aligned warning wording across option, parse, and render fallbacks

### Fixed

- Fixed the runnable FastAPI example and the FastAPI reference app so their
  runtime type annotations work correctly when optional web dependencies are
  actually installed
- Fixed stale integration-test expectations after the improved business-facing
  validation messages landed

### Compatibility Notes

- No public import or export workflow API was removed in this release
- `ImportResult`, `CellErrorMap`, and `RowIssueMap` remain the stable public
  result objects for 2.x integrations
- `storage=...` remains the recommended 2.x backend configuration path
- Legacy built-in Minio fields remain part of the 2.x compatibility surface

### Release Summary

- API response payloads are easier to consume from frontends and backend
  clients
- the FastAPI reference project now looks more like a copyable minimal app
- release smoke checks now verify docs, assets, failed-import payloads, and
  installed FastAPI integrations
- codec diagnostics are more consistent and easier to filter by logger

## [2.2.6] - 2026-04-04

This release continues the stable 2.x line with stronger consumer-facing
result-object guidance, a copyable FastAPI reference project, harder release
smoke validation, and clearer codec fallback diagnostics.

### Added

- Added `docs/result-objects.md` to explain how to read `ImportResult`,
  `CellErrorMap`, and `RowIssueMap` and how to expose them through backend APIs
- Added a copyable FastAPI reference project under `examples/fastapi_reference`
  with separate route, service, storage, and schema modules
- Added a captured output artifact for the FastAPI reference project and linked
  it from the examples docs and showcase

### Changed

- Extended `docs/getting-started.md`, `docs/public-api.md`,
  `docs/examples-showcase.md`, and the README entry points so the result
  objects and API integration path are easier to discover
- Strengthened package smoke verification by validating both successful and
  failed imports, including structured `cell_error_map` and `row_error_map`
  payloads
- Expanded example smoke coverage so the FastAPI reference project is exercised
  directly alongside the existing script-style examples
- Polished codec fallback warnings so parse failures now produce clearer
  developer-facing diagnostics with field labels and cleaner exception reasons

### Compatibility Notes

- No public import or export workflow API was removed in this release
- `ImportResult`, `CellErrorMap`, and `RowIssueMap` remain the stable public
  result objects for 2.x integrations
- The FastAPI reference project is additive guidance and does not change the
  public API surface
- `storage=...` remains the recommended 2.x backend configuration path

### Release Summary

- result objects are now documented as first-class API integration surfaces
- the repository now includes a copyable FastAPI reference-project layout
- release smoke verification checks successful imports, failed imports, and
  structured error payloads
- codec fallback warnings are easier to read and more useful during debugging

## [2.2.5] - 2026-04-04

This release continues the stable 2.x line with error UX polish, clearer
documentation boundaries, stronger examples and smoke coverage, and continued
typing cleanup across the runtime path.

### Added

- Added `CellErrorMap` and `RowIssueMap` as richer workbook-facing error access
  containers while preserving 2.x dict-like compatibility
- Added structured error records and API-friendly payload helpers through
  `records()` and `to_api_payload()` on both `CellErrorMap` and `RowIssueMap`
- Added `docs/getting-started.md` to give new users one clear entry point for
  installation, schema declaration, workflow setup, and backend configuration
- Added `docs/examples-showcase.md` and example-output assets so examples can
  be browsed as a lightweight showcase instead of only as source code
- Added more business-oriented examples, including employee import,
  create-or-update import, export workflow, selection-heavy forms, and
  date/range field workflows
- Added a minimal FastAPI reference project with separate route, service,
  storage, and schema modules so teams can start from a copyable backend
  layout instead of only single-file examples
- Added stronger smoke scripts and release checks for installed packages,
  repository examples, and generated example-output assets

### Changed

- Polished error UX so row and cell issues are easier to inspect through
  dedicated result-map helpers such as `at(...)`, `messages_at(...)`,
  `messages_for_row(...)`, and `flatten()`
- Unified exception boundaries around `ProgrammaticError`, `ConfigError`,
  `ExcelCellError`, and `ExcelRowError`, including structured `to_dict()`
  output and clearer equality semantics
- Normalized common validation messages into more natural, workbook-facing
  English such as `This field is required`
- Made common field-type validation messages more business-oriented by adding
  expected-format hints for date, date-range, number-range, email, phone,
  URL, and configured-selection fields
- Clarified `FieldMetaInfo` as a compatibility facade over layered metadata
  objects and moved more internal consumers and codecs onto `declared`,
  `runtime`, `presentation`, and `constraints`
- Continued shrinking typing gray areas outside `metadata.py` and
  `helper/pydantic.py` by removing or consolidating low-value `cast(...)`
  usage where concrete runtime behavior was already clear
- Strengthened documentation boundaries by cross-linking getting-started,
  public API, migrations, examples, showcase, and PyPI-facing README content
- Expanded `examples/README.md` into a recommended reading order with expected
  outputs and captured example artifacts
- Expanded the examples docs and showcase so the new FastAPI reference project
  is linked from GitHub README, PyPI README, and the examples showcase page

### Fixed

- Restored explicit `ProgrammaticError` handling for unsupported
  `Annotated[..., Field(...), ExcelMeta(...)]` declarations that use native
  Python types instead of `ExcelFieldCodec` subclasses
- Tightened codec resolution in the Pydantic adapter so unsupported
  declarations fail at the codec resolution boundary instead of being treated
  as valid runtime metadata
- Added regression coverage for the unsupported-annotation path and for error
  message quality in the Pydantic adapter

### Compatibility Notes

- No public import or export workflow API was removed in this release
- Valid `ExcelFieldCodec` and `CompositeExcelFieldCodec` declarations continue
  to work unchanged
- Unsupported native annotations with `ExcelMeta(...)` now fail early with the
  intended `ProgrammaticError`
- `storage=...` remains the recommended 2.x backend configuration path, while
  legacy built-in Minio fields continue to exist only as compatibility surface
- `FieldMeta(...)` and `ExcelMeta(...)` remain the stable public metadata entry
  points while internal metadata continues to consolidate behind them

### Release Summary

- import failures are easier to inspect and present through richer error maps
- validation messages are more consistent, more natural, and better suited for
  workbook feedback
- examples now read more like real integration guides and are protected by
  direct smoke coverage
- getting-started, public API, migrations, examples, and showcase docs now
  form a clearer documentation path
- runtime typing boundaries are a little tighter without sacrificing
  readability or 2.x compatibility

## [2.2.3] - Unpublished draft history

This release continues the stable 2.x line with a focused validation fix in
the Pydantic adapter layer.

### Fixed

- Restored explicit `ProgrammaticError` handling for unsupported
  `Annotated[..., Field(...), ExcelMeta(...)]` declarations that use native
  Python types instead of `ExcelFieldCodec` subclasses
- Tightened codec resolution in the Pydantic adapter so unsupported
  declarations fail at the codec resolution boundary instead of being treated
  as valid runtime metadata
- Added a regression test for unsupported annotated declarations to prevent
  native Python annotations from slipping through the workbook schema path

### Changed

- Clarified `FieldMetaInfo` as a compatibility facade over layered metadata
  objects instead of treating it as the primary internal metadata model
- Moved more core consumers and built-in codecs onto the layered metadata
  objects (`declared`, `runtime`, `presentation`, and `constraints`)
- Continued reducing the effective responsibility carried by the flat
  `FieldMetaInfo` compatibility surface in the 2.x implementation
- Concentrated necessary dynamic typing boundaries into explicit aliases in the
  codec and metadata layers instead of leaving ad hoc `Any` usage scattered
  across the codebase
- Replaced a number of remaining loose `Any` annotations in the runtime path
  with more explicit `object` or workbook-boundary aliases where the behavior
  was already concrete
- Added smoke coverage for the repository examples so the annotated schema and
  custom storage examples are exercised directly in tests

### Compatibility Notes

- No public import or export workflow API was removed in this release
- Valid `ExcelFieldCodec` and `CompositeExcelFieldCodec` declarations continue
  to work unchanged
- Unsupported native annotations with `ExcelMeta(...)` now fail early with the
  intended `ProgrammaticError`
- `FieldMeta(...)` and `ExcelMeta(...)` remain the stable public metadata entry
  points while internal metadata continues to consolidate behind them

### Release Summary

- unsupported annotated declarations now fail with the intended error again
- codec resolution is stricter and easier to reason about
- the validation fix is protected by an explicit integration regression test
- metadata internals continue to move toward layered objects rather than a flat
  central record
- runtime typing boundaries are more explicit without changing the public API
- repository examples now have direct smoke coverage in the test suite

## [2.2.2] - 2026-04-03

This release continues the stable 2.x line with stronger developer ergonomics,
clearer public API guidance, and better release-time smoke coverage.

### Added

- Added repository examples for:
  `Annotated` schema declarations, custom storage integration, and FastAPI
  upload flows
- Added `docs/public-api.md` to document stable public modules, compatibility
  modules, and internal modules
- Added `scripts/smoke_package.py` so release workflows can smoke-test template
  generation, import execution, and export generation from an installed package

### Changed

- Updated the release workflow to run package-level smoke tests after wheel and
  source-distribution installation
- Updated `README.md`, `README_cn.md`, and `MIGRATIONS.md` to point users
  toward examples, public API guidance, and the recommended config/storage
  patterns

### Compatibility Notes

- No public import or export workflow API was removed in this release
- The new examples and docs clarify recommended public paths without changing
  existing 2.x compatibility behavior

### Release Summary

- the repository now includes real integration examples instead of relying only
  on README snippets
- public API boundaries are documented explicitly
- release publishing now includes stronger smoke coverage for installed
  packages

## [2.2.1] - 2026-04-03

This release continues the stable 2.x line with deeper metadata layering,
stronger internal immutability, and tighter type boundaries around the
Pydantic adapter layer.

### Added

- Added regression tests that verify split metadata layers behave like
  immutable value objects
- Added regression tests that verify facade-level mutation replaces internal
  metadata layers rather than mutating them in place

### Changed

- Made `DeclaredFieldMeta`, `RuntimeFieldBinding`,
  `WorkbookPresentationMeta`, and `ImportConstraints` frozen internal
  structures
- Updated `FieldMetaInfo` mutation paths to replace internal layer objects via
  structural updates instead of mutating them in place
- Normalized workbook presentation internals so character sets and options are
  stored in immutable forms
- Tightened key type boundaries in the Pydantic adapter around annotations,
  codecs, and normalized input payloads

### Compatibility Notes

- No public import or export workflow API was removed in this release
- `FieldMeta(...)` and `ExcelMeta(...)` remain the stable public metadata entry
  points
- The metadata layering changes are internal and preserve the public 2.x
  surface

### Release Summary

- metadata internals are now more immutable and easier to reason about
- facade-level metadata updates preserve 2.x ergonomics while reducing hidden
  shared state
- the Pydantic adapter layer now has clearer type boundaries

## [2.2.0] - 2026-04-03

This release continues the stable 2.x line with runtime consolidation,
clearer configuration ergonomics, and a stronger protocol-first storage story.

### Added

- Added `ImportSessionPhase` and `ImportSessionSnapshot` so one-shot import runs
  expose a clearer lifecycle and final runtime summary
- Added recommended config constructors:
  `ImporterConfig.for_create(...)`, `ImporterConfig.for_update(...)`,
  `ImporterConfig.for_create_or_update(...)`, `ExporterConfig.for_model(...)`,
  and `ExporterConfig.for_storage(...)`
- Added targeted regression tests for config helper constructors, legacy
  storage deprecation behavior, and import session snapshots

### Changed

- Refined `ImportSession` so the import workflow now advances through explicit
  phases: workbook loading, header validation, row preparation, row execution,
  result rendering, and completion
- Added `ExcelAlchemy.last_import_snapshot` as the facade-level read-only view
  of the latest import session state
- Clarified the recommended storage configuration path around explicit
  `storage=...` backends
- Kept legacy `minio`, `bucket_name`, and `url_expires` support for 2.x, but
  now emit an explicit deprecation warning when that path is used
- Reduced warning noise by emitting the legacy storage deprecation warning once
  per compatibility scenario

### Compatibility Notes

- No public import or export workflow API was removed in this release
- The legacy Minio config path remains supported in 2.x for migration-friendly
  compatibility
- Existing direct `ImporterConfig(...)` and `ExporterConfig(...)` construction
  continue to work; helper constructors are the new recommended path

### Release Summary

- import sessions now expose a clearer lifecycle and final snapshot
- config construction is easier to read through dedicated helper constructors
- `storage=...` is now the clear recommended backend integration path for 2.x

## [2.1.0] - 2026-04-02

This release continues the stable 2.x line with internal architecture cleanup,
clearer naming, and a stronger separation between the long-lived facade and the
single-run import workflow runtime.

### Added

- Added `ImportSession` as the one-shot import workflow runtime that keeps
  worksheet state, header parsing state, issue tracking, and executor state out
  of the long-lived `ExcelAlchemy` facade
- Added normalized internal config layers:
  `ImporterSchemaOptions`, `ImportBehavior`, `ExporterSchemaOptions`,
  `ExportBehavior`, and `StorageOptions`
- Added internal metadata layers:
  `DeclaredFieldMeta`, `RuntimeFieldBinding`, `WorkbookPresentationMeta`, and
  `ImportConstraints`
- Added targeted regression tests for config normalization and split metadata
  layering

### Changed

- Refactored `ExcelAlchemy.import_data()` to delegate import execution to
  `ImportSession` while keeping the 2.x public API unchanged
- Reduced facade responsibility so `ExcelAlchemy` now primarily owns durable
  configuration and collaborator wiring rather than import-run state
- Normalized storage resolution so internal code now reads `storage_options`
  instead of scattering direct reads of `storage`, `minio`, `bucket_name`, and
  `url_expires`
- Updated import execution to consume normalized `schema_options` and
  `behavior` objects instead of treating config as an all-in-one bus
- Split `FieldMetaInfo` into internal declaration, runtime, presentation, and
  constraint layers while preserving the existing `FieldMeta(...)` and
  `ExcelMeta(...)` entry points
- Improved internal naming by moving the primary worksheet variable vocabulary
  from `df/header_df` to `worksheet_table/header_table`
- Renamed `excelalchemy.util.convertor` to
  `excelalchemy.util.converter`; the old path now remains as a deprecated
  compatibility shim
- Simplified generic type parameter names across the config, facade, storage,
  executor, and import-session layers to better reflect their roles

### Compatibility Notes

- `df` and `header_df` remain available as backward-compatible aliases on the
  facade and import session, but new internal code should prefer
  `worksheet_table` and `header_table`
- `excelalchemy.util.convertor` remains importable in 2.x and now emits the
  standard deprecation warning that points to `excelalchemy.util.converter`
- No public import/export workflow API was removed in this release

### Release Summary

- `ExcelAlchemy` is now a lighter facade, with single-run import state handled
  by `ImportSession`
- internal configuration now has clearer schema, behavior, and storage layers
- metadata internals are more structured without forcing users to rewrite
  existing `FieldMeta(...)` or `ExcelMeta(...)` declarations

## [2.0.0.post1] - 2026-03-28

This post-release updates the package presentation and release metadata for the
stable ExcelAlchemy 2.0 line without changing the core import/export behavior.

### Changed

- Added a dedicated PyPI-friendly long description via `README-pypi.md`
- Switched package metadata to use the PyPI-specific README
- Replaced relative README assets with PyPI-safe absolute image and document links
- Tuned Codecov status behavior for large release PRs and compatibility shim files

## [2.0.0] - 2026-03-28

This release promotes the validated 2.0 release candidate to the first stable public
release of ExcelAlchemy 2.0.

### Changed

- Promoted the 2.0 line from release candidate to stable
- Finalized release-facing documentation, badges, and portfolio screenshots
- Finalized the GitHub Actions coverage upload path for optional Codecov integration

## [2.0.0rc1] - 2026-03-27

This release candidate marks the first public preview of the ExcelAlchemy 2.0 line.
It consolidates the architectural work completed across the modernization roadmap and
is intended to validate the release pipeline before the final `2.0.0` release.

### Added

- Locale-aware workbook display text with `locale='zh-CN' | 'en'`
- A pluggable `ExcelStorage` protocol for custom storage backends
- An optional built-in Minio backend installable via `ExcelAlchemy[minio]`
- Internal `WorksheetTable` abstraction for workbook IO without pandas
- Architecture and design documentation in `README.md`, `ABOUT.md`, and `docs/architecture.md`
- A lightweight i18n message layer for runtime and workbook display messages

### Changed

- Migrated the codebase to a standard `src/` layout
- Migrated from Pydantic v1-style internals to a Pydantic v2-based adapter design
- Modernized the codebase for Python 3.12-3.14, with Python 3.14 as the primary target
- Switched local development, CI, and release workflows to `uv`
- Split the former monolithic orchestration layer into focused internal components
- Rewrote the main documentation as architecture-focused project pages
- Deprecated the legacy `excelalchemy.types.*` import paths in favor of `excelalchemy.metadata`, `excelalchemy.results`, `excelalchemy.config`, `excelalchemy.codecs`, and public types re-exported from the package root
- Promoted `excelalchemy.exceptions` as the stable exception module and converted `excelalchemy.exc`, `excelalchemy.identity`, and `excelalchemy.header_models` into explicit compatibility layers

### Removed

- Runtime dependency on `pandas`
- Hard architectural dependence on Minio
- Support for Python 3.10 and 3.11

### Breaking Changes

- The supported Python range is now `3.12-3.14`
- The project now requires Pydantic v2
- `pandas` is no longer installed or used at runtime
- Minio is no longer a core dependency; install `ExcelAlchemy[minio]` if you want the built-in backend
- Runtime exceptions and validation messages are now standardized in English

### Migration Notes

- If you previously depended on Minio support, install the extra:
  `pip install "ExcelAlchemy[minio]"`
- If you want a custom storage backend, provide `storage=...` on `ImporterConfig` or `ExporterConfig`
- If your users need English workbook-facing hints and import result labels, set `locale='en'`
- If you were relying on pandas being present indirectly, install it separately in your own application

## [1.1.0] - Previous stable line

- Legacy stable release before the 2.0 architecture and dependency modernization work.
