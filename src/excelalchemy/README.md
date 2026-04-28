# `src/excelalchemy/` Package Guide

This file explains the internal structure of the main package directory.
It is meant for developers and AI agents who need to change implementation details without confusing public API, compatibility layers, and internal collaborators.

## Related docs

- [../../README.md](../../README.md) for the public-facing overview.
- [../../AGENTS.md](../../AGENTS.md) for repository-local editing guidance.
- [../../docs/repo-map.md](../../docs/repo-map.md) for top-level repository navigation.
- [../../docs/domain-model.md](../../docs/domain-model.md) for the main concepts implemented here.
- [../../docs/agent/invariants.md](../../docs/agent/invariants.md) for important behavioral constraints.
- [../../tests/README.md](../../tests/README.md) for where this package's behavior is protected.

## Role of This Package

- `src/excelalchemy/` is the main library package.
- It contains:
  - the stable public surface used by application code
  - the internal orchestration that implements import, export, template generation, rendering, and storage integration
  - compatibility modules retained for the 2.x line
- The package is organized around a small public facade and a set of focused internal collaborators.
- In the v2.4 docs, those collaborators are also described through a higher-level
  import platform model:
  - template authoring
  - preflight gate
  - import runtime
  - result intelligence
  - artifact and delivery

## High-Level Package Structure

- `__init__.py`
  - Main public re-export surface.
  - If application-facing imports change, start here.
- `config.py`
  - Public workflow configuration types.
- `metadata.py`
  - Public metadata declarations plus the internal layered field-metadata model.
- `results.py`
  - Public result models and API-friendly error maps.
- `exceptions.py`
  - Public exception types.
- `artifacts.py`
  - Public workbook artifact wrapper.
- `codecs/`
  - Public field codecs and codec base classes.
- `core/`
  - Internal workflow orchestration and execution.
- `helper/`
  - Internal adapter layer, currently centered on Pydantic integration.
- `i18n/`
  - Internal message and locale handling.
- `_primitives/`
  - Internal low-level types, constants, payload aliases, diagnostics, and deprecation helpers.
- `types/`, `exc.py`, `identity.py`, `header_models.py`, `const.py`, `util/convertor.py`
  - Compatibility-oriented modules retained in the 2.x line.

## Public Surface vs Internal Implementation

### Public surface

These modules are the stable public entry points documented in `docs/public-api.md`:

- `src/excelalchemy/__init__.py`
- `src/excelalchemy/config.py`
- `src/excelalchemy/metadata.py`
- `src/excelalchemy/results.py`
- `src/excelalchemy/exceptions.py`
- `src/excelalchemy/codecs/`
- `src/excelalchemy/artifacts.py`

### Internal implementation

These modules implement behavior but are not the recommended import paths for application code:

- `src/excelalchemy/core/`
- `src/excelalchemy/helper/`
- `src/excelalchemy/i18n/`
- `src/excelalchemy/_primitives/`

### Compatibility-only surface

These exist to support the 2.x line and should not be treated as preferred implementation entry points for new work:

- `src/excelalchemy/types/`
- `src/excelalchemy/exc.py`
- `src/excelalchemy/identity.py`
- `src/excelalchemy/header_models.py`
- `src/excelalchemy/const.py`
- `src/excelalchemy/util/convertor.py`

## Major Modules and Responsibilities

### Public-facing root modules

- `src/excelalchemy/__init__.py`
  - Re-exports `ExcelAlchemy`, configs, codecs, result types, exception types, and common identity/value types.
  - Changes here affect top-level user imports directly.

- `src/excelalchemy/config.py`
  - Defines:
    - `ExcelMode`
    - `ImportMode`
    - `ImporterConfig`
    - `ExporterConfig`
    - normalized schema/behavior/storage option groupings
  - Also contains legacy Minio compatibility handling and deprecation warnings.

- `src/excelalchemy/metadata.py`
  - Defines public declaration helpers:
    - `FieldMeta(...)`
    - `ExcelMeta(...)`
  - Also defines the internal metadata layers behind `FieldMetaInfo`:
    - `DeclaredFieldMeta`
    - `RuntimeFieldBinding`
    - `WorkbookPresentationMeta`
    - `ImportConstraints`
  - This file is central when changing field declaration behavior, workbook comments, formatting hints, or constraint overlay rules.

- `src/excelalchemy/results.py`
  - Defines public result objects:
    - `ImportResult`
    - `ValidateHeaderResult`
    - `ValidateResult`
    - `ValidateRowResult`
    - `CellErrorMap`
    - `RowIssueMap`
  - This is the main file for API payload shape and structured error access.

- `src/excelalchemy/exceptions.py`
  - Defines the public exception model:
    - `ExcelAlchemyError`
    - `ExcelCellError`
    - `ExcelRowError`
    - `ProgrammaticError`
    - `ConfigError`

- `src/excelalchemy/artifacts.py`
  - Defines `ExcelArtifact`, which wraps rendered workbook content as bytes, base64, or a data URL.

### `core/` internal orchestration

- `src/excelalchemy/core/alchemy.py`
  - Main facade implementation.
  - Builds layout and storage, exposes the top-level workflow methods, and surfaces inspection properties like `worksheet_table` and `cell_error_map`.
  - This is the first internal file to inspect when changing how the facade behaves.

- `src/excelalchemy/core/import_session.py`
  - Owns one import run’s runtime state.
  - Tracks:
    - workbook load state
    - header table
    - worksheet table
    - issue maps
    - execution counts
    - result rendering state
    - `ImportSessionSnapshot`
  - This is the main import lifecycle owner.

- `src/excelalchemy/core/schema.py`
  - Converts extracted field metadata into `ExcelSchemaLayout`.
  - Responsible for:
    - layout ordering
    - unique label/key indexing
    - composite field expansion
    - merged-header detection for selected output keys

- `src/excelalchemy/core/headers.py`
  - Header parsing and header validation.
  - Responsible for:
    - detecting simple vs merged headers
    - normalizing parsed headers into `ExcelHeader` objects
    - comparing workbook headers against schema layout

- `src/excelalchemy/core/rows.py`
  - Row reconstruction and issue tracking.
  - `RowAggregator` groups flattened worksheet data back into model-shaped payloads.
  - `ImportIssueTracker` maps row/cell failures back to workbook coordinates and prepends result columns.

- `src/excelalchemy/core/executor.py`
  - Dispatches the actual import execution path.
  - Responsible for:
    - choosing create/update/create-or-update behavior
    - validating reconstructed payloads
    - invoking configured callbacks
    - mapping failures into row/cell issues

- `src/excelalchemy/core/rendering.py`
  - High-level rendering entry points for templates, exports, and import result workbooks.

- `src/excelalchemy/core/writer.py`
  - Lower-level workbook writing details:
    - comments
    - fills/colors
    - workbook rows/cells
    - result/reason columns

- `src/excelalchemy/core/storage_protocol.py`
  - Defines the `ExcelStorage` protocol.
  - This is the main storage extension boundary.

- `src/excelalchemy/core/storage.py`
  - Resolves configured storage into a concrete gateway.
  - Also defines the missing-storage fallback path.

- `src/excelalchemy/core/storage_minio.py`
  - Built-in Minio-backed storage implementation.

- `src/excelalchemy/core/table.py`
  - Defines `WorksheetTable`, `WorksheetRow`, and related helpers.
  - This is the internal table abstraction used instead of pandas.

### `codecs/` field behavior

- `src/excelalchemy/codecs/base.py`
  - Defines:
    - `ExcelFieldCodec`
    - `CompositeExcelFieldCodec`
    - fallback logging helpers
  - Start here when changing the codec contract itself.

- `src/excelalchemy/codecs/*.py`
  - Built-in concrete field codecs such as:
    - `string.py`
    - `number.py`
    - `date.py`
    - `date_range.py`
    - `email.py`
    - `phone_number.py`
    - `money.py`
    - `radio.py`
    - `multi_checkbox.py`
    - `organization.py`
    - `staff.py`
    - `tree.py`
    - `url.py`

### Adapter, i18n, and primitive helpers

- `src/excelalchemy/helper/pydantic.py`
  - Isolates the Pydantic boundary.
  - Responsible for:
    - extracting model metadata
    - resolving codec types
    - normalizing validation messages
    - mapping Pydantic validation output to `ExcelCellError` and `ExcelRowError`

- `src/excelalchemy/i18n/messages.py`
  - Central message lookup and locale handling.
  - Important when changing workbook-facing text, runtime error text, or locale policy.

- `src/excelalchemy/_primitives/constants.py`
  - Internal constants and enum-like definitions used across the package.

- `src/excelalchemy/_primitives/identity.py`
  - Internal typed wrappers for labels, keys, row indexes, column indexes, URLs, and related string-like identifiers.

- `src/excelalchemy/_primitives/payloads.py`
  - Shared payload type aliases for import/export/data-converter/callback paths.

- `src/excelalchemy/_primitives/diagnostics.py`
  - Developer-facing diagnostic logging helpers.

- `src/excelalchemy/_primitives/deprecation.py`
  - Deprecation warning helpers used by compatibility modules.

- `src/excelalchemy/_primitives/header_models.py`
  - Internal parsed-header model objects.

## Major Internal Flows

The package guide keeps the internal ownership view.
If you want the capability-oriented platform view above these flows, start with:

- [`../../docs/platform-architecture.md`](../../docs/platform-architecture.md)
- [`../../docs/runtime-model.md`](../../docs/runtime-model.md)
- [`../../docs/platform-code-mapping.md`](../../docs/platform-code-mapping.md)

### Import validation flow

The import path is implemented roughly in this order:

1. `src/excelalchemy/core/alchemy.py`
   - `ExcelAlchemy.import_data(...)` creates a new import session.
2. `src/excelalchemy/core/import_session.py`
   - loads workbook data through storage
   - builds header and worksheet state
3. `src/excelalchemy/core/headers.py`
   - parses headers
   - validates headers against the schema layout
4. `src/excelalchemy/core/rows.py`
   - reconstructs model-shaped row payloads
5. `src/excelalchemy/core/executor.py`
   - validates and dispatches create/update/upsert logic
6. `src/excelalchemy/helper/pydantic.py`
   - adapts Pydantic validation into ExcelAlchemy issues
7. `src/excelalchemy/core/rows.py`
   - records row/cell failures in workbook coordinates
8. `src/excelalchemy/core/rendering.py` and `src/excelalchemy/core/writer.py`
   - render the import result workbook when rows fail
9. `src/excelalchemy/results.py`
   - exposes the final result through `ImportResult`, `CellErrorMap`, and `RowIssueMap`

### Template generation flow

The template path is implemented roughly in this order:

1. `src/excelalchemy/core/alchemy.py`
   - selects output keys and header shape
2. `src/excelalchemy/core/schema.py`
   - provides ordered layout and merged-header decisions
3. `src/excelalchemy/codecs/`
   - provide comments, display formatting, and field-specific workbook semantics
4. `src/excelalchemy/core/rendering.py`
5. `src/excelalchemy/core/writer.py`
   - produce the workbook output
6. `src/excelalchemy/artifacts.py`
   - wraps the output when the artifact API is used

### Export flow

The export path is implemented roughly in this order:

1. `src/excelalchemy/core/alchemy.py`
   - accepts export rows and selected keys
2. `src/excelalchemy/core/schema.py`
   - resolves output layout and merged-header needs
3. `src/excelalchemy/codecs/`
   - format workbook-facing values
4. `src/excelalchemy/core/rendering.py`
5. `src/excelalchemy/core/writer.py`
6. `src/excelalchemy/core/storage_protocol.py` and `src/excelalchemy/core/storage.py`
   - are used only when the upload path is chosen

### Storage integration flow

Storage-related behavior is split into three concerns:

- contract:
  - `src/excelalchemy/core/storage_protocol.py`
- resolution:
  - `src/excelalchemy/core/storage.py`
- built-in Minio backend:
  - `src/excelalchemy/core/storage_minio.py`

The recommended 2.x design is:

- config holds `storage=...`
- `build_storage_gateway(...)` resolves it
- import reads workbook data as `WorksheetTable`
- export/import-result uploads return a URL through the storage implementation
- custom storage readers currently use `src/excelalchemy/core/table.py` for that `WorksheetTable` contract

## Where To Look When Changing Specific Behavior

### Changing public API behavior

Start here:

- `src/excelalchemy/__init__.py`
- `src/excelalchemy/config.py`
- `src/excelalchemy/metadata.py`
- `src/excelalchemy/results.py`
- `src/excelalchemy/exceptions.py`
- `docs/public-api.md`
- `MIGRATIONS.md`
- `tests/contracts/`

Use extra caution when changing:

- exported names
- config constructor behavior
- result payload shape
- exception wording or exception type mapping
- compatibility aliases

### Changing import validation behavior

Start here:

- `src/excelalchemy/core/import_session.py`
- `src/excelalchemy/core/headers.py`
- `src/excelalchemy/core/rows.py`
- `src/excelalchemy/core/executor.py`
- `src/excelalchemy/helper/pydantic.py`
- `src/excelalchemy/results.py`
- `tests/contracts/test_import_contract.py`
- `tests/contracts/test_core_components_contract.py`
- `tests/contracts/test_pydantic_contract.py`

Typical examples:

- header validation rules
- row reconstruction
- Pydantic error mapping
- create/update/upsert behavior
- result-workbook error placement

### Changing export or template generation behavior

Start here:

- `src/excelalchemy/core/alchemy.py`
- `src/excelalchemy/core/schema.py`
- `src/excelalchemy/core/rendering.py`
- `src/excelalchemy/core/writer.py`
- `src/excelalchemy/codecs/`
- `tests/contracts/test_template_contract.py`
- `tests/contracts/test_export_contract.py`

Typical examples:

- workbook comments
- merged headers
- selected output keys
- workbook-facing display formatting
- artifact generation

### Changing storage integration behavior

Start here:

- `src/excelalchemy/core/storage_protocol.py`
- `src/excelalchemy/core/storage.py`
- `src/excelalchemy/core/storage_minio.py`
- `src/excelalchemy/config.py`
- `examples/custom_storage.py`
- `tests/contracts/test_storage_contract.py`
- `tests/unit/test_config_options.py`

Typical examples:

- storage contract shape
- default gateway selection
- missing-storage behavior
- Minio compatibility behavior
- upload payload expectations

### Changing locale-aware output behavior

Start here:

- `src/excelalchemy/i18n/messages.py`
- `src/excelalchemy/metadata.py`
- `src/excelalchemy/core/alchemy.py`
- `src/excelalchemy/core/writer.py`
- `docs/locale.md`
- `tests/contracts/test_template_contract.py`
- `tests/contracts/test_import_contract.py`

Typical examples:

- workbook instruction text
- header comments
- result/reason column labels
- row status text
- fallback locale behavior

## Implementation Cautions

- Do not treat compatibility modules under `src/excelalchemy/types/` and the root compatibility shims as preferred edit points for new behavior.
- Do not reintroduce pandas-style assumptions into the runtime path; this package now uses `WorksheetTable`.
- Do not hard-wire Minio into core workflow logic; storage is intentionally abstracted behind `ExcelStorage`.
- Treat `src/excelalchemy/core/table.py` as a narrow extension seam for current 2.x storage integrations, not as a general application import surface.
- If you change result payload shape, inspect:
  - `src/excelalchemy/results.py`
  - `docs/result-objects.md`
  - `docs/api-response-cookbook.md`
  - `scripts/smoke_api_payload_snapshot.py`
  - `files/example-outputs/import-failure-api-payload.json`
- If you change docs-visible example behavior, inspect:
  - `examples/`
  - `files/example-outputs/`
  - `scripts/generate_example_output_assets.py`
  - `scripts/smoke_examples.py`
  - `scripts/smoke_docs_assets.py`
