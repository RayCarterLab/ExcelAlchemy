# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog and versioned according to PEP 440.

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
