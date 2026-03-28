# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog and versioned according to PEP 440.

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
