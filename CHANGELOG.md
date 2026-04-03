# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog and versioned according to PEP 440.

## [2.2.3] - Unreleased

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

### Compatibility Notes

- No public import or export workflow API was removed in this release
- Valid `ExcelFieldCodec` and `CompositeExcelFieldCodec` declarations continue
  to work unchanged
- Unsupported native annotations with `ExcelMeta(...)` now fail early with the
  intended `ProgrammaticError`

### Release Summary

- unsupported annotated declarations now fail with the intended error again
- codec resolution is stricter and easier to reason about
- the validation fix is protected by an explicit integration regression test

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

## [2.2.1] - Unreleased

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
