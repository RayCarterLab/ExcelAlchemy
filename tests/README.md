# Test Suite Guide

This directory holds the repository’s main automated test suite.
It is organized around stable public behavior first, then workflow integration, then focused unit coverage.

## Related docs

- [../README.md](../README.md) for the public-facing workflow overview.
- [../docs/repo-map.md](../docs/repo-map.md) for where the tested code lives.
- [../docs/agent/invariants.md](../docs/agent/invariants.md) for the behaviors this suite is meant to lock down.
- [../src/excelalchemy/README.md](../src/excelalchemy/README.md) for the implementation structure behind the tests.
- [../examples/README.md](../examples/README.md) for the example workflows that integration and smoke coverage protect.

## How the test suite is organized

### `tests/contracts/`

- Purpose:
  - protect the stable behavior that callers and downstream integrations rely on
  - protect key contracts between the public facade and core collaborators
- Main files:
  - `tests/contracts/test_template_contract.py`
    - template payload shape, workbook comments, merged headers, required-field styling, locale-sensitive template output
  - `tests/contracts/test_export_contract.py`
    - export payload shape, selected key behavior, merged-header export behavior, workbook-facing values
  - `tests/contracts/test_import_contract.py`
    - import result status, header-invalid vs data-invalid behavior, result workbook upload behavior, workbook failure rendering, locale-sensitive result output
  - `tests/contracts/test_storage_contract.py`
    - storage gateway selection, missing-storage behavior, custom storage behavior, upload payload expectations, `WorksheetTable` reader behavior
  - `tests/contracts/test_result_contract.py`
    - `ImportResult`, `ValidateHeaderResult`, status helpers, API payload shape
  - `tests/contracts/test_pydantic_contract.py`
    - metadata extraction, Pydantic validation mapping, custom codec extension surface, `Annotated[..., ExcelMeta(...)]` declarations
  - `tests/contracts/test_core_components_contract.py`
    - schema layout, header parsing/validation, row aggregation, issue tracking column offsets

### `tests/integration/`

- Purpose:
  - exercise broader end-to-end flows that cross multiple modules
  - verify runnable examples and real workflow combinations
- Main files:
  - `tests/integration/test_excelalchemy_workflows.py`
    - end-to-end workflow coverage across import/export paths and many built-in field types
  - `tests/integration/test_examples_smoke.py`
    - smoke-style tests for repository examples and the FastAPI reference app

### `tests/unit/`

- Purpose:
  - protect focused logic in individual modules or small subsystems
  - keep regressions close to the code that changed
- Main files:
  - `tests/unit/test_config_options.py`
    - config normalization, helper constructors, storage option behavior, legacy Minio warnings
  - `tests/unit/test_converters_and_schema_extraction.py`
    - converter utilities and schema extraction details
  - `tests/unit/test_deprecation_policy.py`
    - compatibility import warnings and replacement guidance
  - `tests/unit/test_diagnostics_logging.py`
    - named logger behavior and developer-facing diagnostics
  - `tests/unit/test_excel_exceptions.py`
    - exception model and payload behavior
  - `tests/unit/test_field_metadata.py`
    - metadata layering, comments, inherited behavior, constraint overlay details
  - `tests/unit/test_file_utils.py`
    - workbook/data-url utility helpers
  - `tests/unit/test_i18n_messages.py`
    - message lookup and locale-sensitive text behavior
  - `tests/unit/codecs/*.py`
    - per-codec behavior for parse/normalize/render/comment logic

### `tests/support/`

- Purpose:
  - shared fixtures and helpers used across contract, integration, and unit tests
- Important files:
  - `tests/support/base.py`
    - shared test base class
  - `tests/support/contract_models.py`
    - reusable Pydantic models and callbacks for tests
  - `tests/support/mock_minio.py`
    - local mock Minio behavior
  - `tests/support/storage.py`
    - in-memory storage test double
  - `tests/support/registry.py`
    - named workbook fixture registry
  - `tests/support/workbook.py`
    - workbook decoding, fill/color inspection, merge-range helpers, worksheet matrix helpers

### `tests/files/`

- Purpose:
  - workbook fixtures used by tests
- Current examples:
  - `tests/files/test_import_with_merge_header.xlsx`
  - `tests/files/test_date_range_input.xlsx`
  - `tests/files/test_date_range_missing_input_before.xlsx`
  - `tests/files/test_date_range_missing_input_after.xlsx`

## What kinds of behavior are protected by tests

- Public API shape and recommended usage:
  - facade methods
  - config helper constructors
  - result object payloads
  - public exception behavior
- Schema and metadata behavior:
  - `FieldMeta(...)`
  - `ExcelMeta(...)`
  - flattened layout ordering
  - composite field expansion
  - constraint overlay
- Import behavior:
  - header validation
  - row validation
  - create/update/create-or-update execution
  - result-workbook upload and rendering
- Export and template behavior:
  - data URL vs artifact behavior
  - workbook comments
  - merged headers
  - selected output keys
  - workbook-facing value formatting
- Storage behavior:
  - `ExcelStorage` contract behavior
  - storage gateway selection
  - `WorksheetTable` reader shape
  - missing-storage failure mode
  - Minio compatibility behavior
  - custom storage behavior
- Localization behavior:
  - template locale
  - result-workbook locale
  - message lookup and fallback behavior
- Compatibility behavior:
  - deprecated import paths
  - legacy naming aliases
  - deprecation warnings
- Developer-facing diagnostics:
  - named logger usage
  - warning/info message consistency

## Test types in this repository

### Contract tests

- Live under `tests/contracts/`.
- These are the highest-signal tests for public behavior.
- If a change would affect library consumers, examples, payload shape, or workbook output semantics, start here.

### Integration tests

- Live under `tests/integration/`.
- These cover multi-module flows and runnable repository examples.
- Use these when a change crosses facade, schema, codecs, storage, rendering, or example code.

### Unit tests

- Live under `tests/unit/`.
- These cover focused logic in one module or subsystem.
- Use these for metadata details, config normalization, exception behavior, i18n logic, utility helpers, and individual codecs.

### Regression tests

- There is no separate `tests/regression/` directory.
- Regression coverage is added next to the affected area:
  - contract regressions go in `tests/contracts/`
  - workflow regressions go in `tests/integration/`
  - focused logic regressions go in `tests/unit/`

### Smoke-style tests

- Smoke-style tests inside `tests/` live mainly in:
  - `tests/integration/test_examples_smoke.py`
- Additional smoke coverage exists outside `tests/` in:
  - `scripts/smoke_examples.py`
  - `scripts/smoke_package.py`
  - `scripts/smoke_docs_assets.py`
  - `scripts/smoke_api_payload_snapshot.py`

## Where to add tests for specific changes

### Public API changes

- Add or update tests in:
  - `tests/contracts/test_result_contract.py`
  - `tests/contracts/test_storage_contract.py`
  - `tests/contracts/test_template_contract.py`
  - `tests/contracts/test_export_contract.py`
  - `tests/contracts/test_import_contract.py`
  - `tests/unit/test_config_options.py`
  - `tests/unit/test_deprecation_policy.py`
- Use this area for:
  - facade method behavior
  - result payload shape
  - config constructor behavior
  - public naming changes
  - compatibility-path changes

### Schema and layout behavior

- Add or update tests in:
  - `tests/contracts/test_core_components_contract.py`
  - `tests/contracts/test_pydantic_contract.py`
  - `tests/unit/test_converters_and_schema_extraction.py`
  - `tests/unit/test_field_metadata.py`
- Use this area for:
  - field metadata extraction
  - layout ordering
  - merged-header shape
  - composite field expansion
  - schema converter behavior

### Import validation behavior

- Add or update tests in:
  - `tests/contracts/test_import_contract.py`
  - `tests/contracts/test_pydantic_contract.py`
  - `tests/contracts/test_core_components_contract.py`
  - `tests/integration/test_excelalchemy_workflows.py`
- Use this area for:
  - header validation
  - row validation
  - Pydantic error mapping
  - create/update/upsert flow behavior
  - import session lifecycle behavior

### Workbook rendering behavior

- Add or update tests in:
  - `tests/contracts/test_template_contract.py`
  - `tests/contracts/test_export_contract.py`
  - `tests/contracts/test_import_contract.py`
  - `tests/support/workbook.py` helpers if you need new workbook assertions
- Use this area for:
  - comments
  - fills/colors
  - result/reason columns
  - merged-cell output
  - workbook-facing display values

### Localization behavior

- Add or update tests in:
  - `tests/contracts/test_template_contract.py`
  - `tests/contracts/test_import_contract.py`
  - `tests/unit/test_i18n_messages.py`
- Use this area for:
  - workbook display locale
  - runtime message lookup
  - header comments and workbook instruction text
  - result-workbook labels and row status text

### Storage behavior

- Add or update tests in:
  - `tests/contracts/test_storage_contract.py`
  - `tests/unit/test_config_options.py`
  - `tests/integration/test_excelalchemy_workflows.py` if the change affects broader workflows
  - `tests/support/storage.py` if a new storage test double is needed
- Use this area for:
  - storage gateway selection
  - reader return shape (`WorksheetTable`)
  - `ExcelStorage` contract behavior
  - upload payload expectations
  - missing-storage errors
  - legacy Minio compatibility

## Useful shared helpers

- Use `tests/support/contract_models.py` for reusable importer/exporter models and callbacks.
- Use `tests/support/storage.py` for in-memory storage-backed tests.
- Use `tests/support/workbook.py` for workbook assertions instead of reimplementing workbook parsing in each test.
- Use `tests/support/registry.py` and `tests/files/` for named workbook fixtures.

## Running tests

- Full test suite:
  - `uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests`
- Common smoke checks related to tests:
  - `uv run python scripts/smoke_package.py`
  - `uv run python scripts/smoke_examples.py`
  - `uv run python scripts/smoke_docs_assets.py`
  - `uv run python scripts/smoke_api_payload_snapshot.py`

## What an agent should check before opening a PR

- The changed behavior is covered at the right level:
  - `tests/contracts/` for public behavior
  - `tests/integration/` for end-to-end/example behavior
  - `tests/unit/` for focused logic
- Existing tests for the touched area still pass.
- New behavior has a regression test near the affected subsystem.
- If examples changed, check:
  - `tests/integration/test_examples_smoke.py`
  - `scripts/smoke_examples.py`
- If result payloads changed, check:
  - `tests/contracts/test_result_contract.py`
  - `docs/result-objects.md`
  - `docs/api-response-cookbook.md`
  - `scripts/smoke_api_payload_snapshot.py`
- If locale-visible workbook text changed, check:
  - `tests/contracts/test_template_contract.py`
  - `tests/contracts/test_import_contract.py`
  - `tests/unit/test_i18n_messages.py`
  - `docs/locale.md`
- If storage behavior changed, check:
  - `tests/contracts/test_storage_contract.py`
  - `tests/unit/test_config_options.py`
  - `examples/custom_storage.py`
- If compatibility behavior changed, check:
  - `tests/unit/test_deprecation_policy.py`
  - `MIGRATIONS.md`
  - `docs/public-api.md`
