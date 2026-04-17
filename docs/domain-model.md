# Domain Model

This document names the core concepts used by `ExcelAlchemy` and shows how they relate to each other.
It is based on the repository as it exists today.

For directory-level navigation, see [`docs/repo-map.md`](repo-map.md).
For component structure, see [`docs/architecture.md`](architecture.md).

## Related docs

- [repo-map.md](repo-map.md) for where these concepts live in the repository.
- [invariants.md](invariants.md) for the constraints that govern these concepts.
- [../src/excelalchemy/README.md](../src/excelalchemy/README.md) for the package-level implementation view.
- [../tests/README.md](../tests/README.md) for where the model is protected by tests.

## 1. Core concepts and entities

| Concept | Primary files | Responsibility | Visibility |
| --- | --- | --- | --- |
| `ExcelAlchemy` facade | `src/excelalchemy/__init__.py`, `src/excelalchemy/core/alchemy.py` | Main workflow entry point for template generation, import, export, and upload. | Public |
| Schema/model contract | User Pydantic models referenced by `ImporterConfig` and `ExporterConfig` | Defines the workbook-facing data shape. Fields carry Excel-specific codec types and metadata. | Public concept |
| `ImporterConfig` | `src/excelalchemy/config.py` | Configures import models, callbacks, import mode, locale, and storage. | Public |
| `ExporterConfig` | `src/excelalchemy/config.py` | Configures export model, locale, storage, and export conversion behavior. | Public |
| `ImportMode` | `src/excelalchemy/config.py` | Selects `CREATE`, `UPDATE`, or `CREATE_OR_UPDATE` import behavior. | Public |
| `FieldMeta(...)` / `ExcelMeta(...)` | `src/excelalchemy/metadata.py` | Declare workbook labels, ordering, hints, options, required-ness, formatting hints, and import constraints. | Public |
| `FieldMetaInfo` and layered metadata | `src/excelalchemy/metadata.py` | Hold resolved field metadata during execution. `FieldMetaInfo` is the compatibility facade over the layered metadata objects. | Internal runtime concept with compatibility role |
| Field codec | `src/excelalchemy/codecs/base.py`, `src/excelalchemy/codecs/*.py` | Owns Excel-facing parsing, display formatting, normalization, and header-comment behavior for a field type. | Public extension surface |
| Composite field codec | `src/excelalchemy/codecs/base.py`, `src/excelalchemy/codecs/date_range.py`, `src/excelalchemy/codecs/number_range.py`, `src/excelalchemy/codecs/organization.py`, `src/excelalchemy/codecs/staff.py`, `src/excelalchemy/codecs/tree.py` | Expands one logical field into multiple worksheet columns. | Public extension surface |
| Schema layout | `src/excelalchemy/core/schema.py` | Flattens model fields into an Excel-facing ordered layout with unique labels and keys. | Internal |
| Header model | `src/excelalchemy/_primitives/header_models.py` | Represents one parsed workbook header, including parent/child label relationships for merged headers. | Internal |
| Header parser | `src/excelalchemy/core/headers.py` | Detects simple vs merged headers and turns header rows into normalized header objects. | Internal |
| Header validator | `src/excelalchemy/core/headers.py` | Compares workbook headers to schema layout and produces `ValidateHeaderResult`. | Internal |
| Worksheet table | `src/excelalchemy/core/table.py` | Lightweight internal 2D table abstraction used for workbook import/export flow instead of pandas. | Internal, but important to understand |
| Import session | `src/excelalchemy/core/import_session.py` | Owns one import run’s lifecycle, state, counts, header table, worksheet table, and result rendering decisions. | Internal |
| Import session snapshot | `src/excelalchemy/core/import_session.py` | Immutable summary of the current import session phase and counts. | Internal |
| Row aggregator | `src/excelalchemy/core/rows.py` | Reconstructs flattened worksheet rows back into model-shaped payloads. | Internal |
| Import issue tracker | `src/excelalchemy/core/rows.py` | Maps cell and row issues back into workbook coordinates and result columns. | Internal |
| Import executor | `src/excelalchemy/core/executor.py` | Validates row payloads and dispatches configured create/update/upsert callbacks. | Internal |
| Pydantic adapter | `src/excelalchemy/helper/pydantic.py` | Extracts metadata from Pydantic models and converts Pydantic validation output into ExcelAlchemy row/cell issues. | Internal boundary |
| Renderer | `src/excelalchemy/core/rendering.py` | Converts worksheet tables and metadata into workbook outputs for templates, exports, and import results. | Internal |
| Writer | `src/excelalchemy/core/writer.py` | Applies workbook-level formatting, comments, colors, and result columns. | Internal |
| `ExcelStorage` | `src/excelalchemy/core/storage_protocol.py` | Defines the storage protocol for reading workbook tables and uploading rendered workbooks. | Public extension surface |
| Storage gateway resolution | `src/excelalchemy/core/storage.py` | Chooses the storage implementation for a config, including missing-storage fallback. | Internal |
| `MinioStorageGateway` | `src/excelalchemy/core/storage_minio.py` | Built-in `ExcelStorage` implementation for Minio-compatible object storage. | Concrete implementation |
| `ExcelArtifact` | `src/excelalchemy/artifacts.py` | Wraps a rendered workbook as bytes, base64, or data URL. | Public |
| `ValidateHeaderResult` | `src/excelalchemy/results.py` | Represents header-only validation outcome. | Public result type |
| `ImportResult` | `src/excelalchemy/results.py` | Represents the top-level outcome of an import run. | Public result type |
| `CellErrorMap` | `src/excelalchemy/results.py` | Structured cell-level issue map with workbook coordinates and API helpers. | Public result type |
| `RowIssueMap` | `src/excelalchemy/results.py` | Structured row-level issue map with summaries and API helpers. | Public result type |

## 2. Responsibilities

### Declaration responsibilities

- Pydantic models define the logical data contract for import and export.
- `FieldMeta(...)` and `ExcelMeta(...)` define the workbook-facing contract:
  - label
  - order
  - comments and hints
  - options
  - formatting hints
  - import-side constraints
- Field codecs define how a field behaves in a workbook:
  - how it is described in header comments
  - how workbook input is parsed
  - how values are normalized for validation
  - how values are rendered back for display

### Execution responsibilities

- `ExcelAlchemy` turns a config and schema into a usable workflow object.
- `ExcelSchemaLayout` turns schema declarations into a flattened Excel layout.
- `ExcelHeaderParser` and `ExcelHeaderValidator` decide whether an uploaded workbook matches that layout.
- `RowAggregator` reconstructs model-shaped data from worksheet rows.
- `ImportExecutor` validates and dispatches row payloads through configured callbacks.
- `ImportIssueTracker` preserves workbook-coordinate visibility for failures.

### Output responsibilities

- `ExcelRenderer` and `writer.py` produce:
  - templates
  - exports
  - import result workbooks
- `ImportResult`, `CellErrorMap`, and `RowIssueMap` expose structured programmatic results.
- `ExcelArtifact` exposes workbook output in transport-friendly forms.

### Integration responsibilities

- `ExcelStorage` is the boundary for reading and uploading workbooks.
- `MinioStorageGateway` is the built-in concrete backend.
- `helper/pydantic.py` is the boundary between Pydantic and ExcelAlchemy-specific metadata/error handling.

## 3. Relationships between concepts

- `ImporterConfig` or `ExporterConfig` is passed into `ExcelAlchemy`.
- The config points to one or more schema models.
- Schema model fields are declared with Excel-specific codec types and metadata.
- `helper/pydantic.py` extracts those declarations into runtime field metadata.
- `ExcelSchemaLayout` organizes that metadata into an ordered Excel-facing layout.
- The layout drives:
  - template generation
  - header validation
  - row aggregation
  - error ordering
  - export column selection
- `ExcelStorage` provides workbook input as `WorksheetTable` and accepts rendered workbook output for upload.
- During import:
  - `ImportSession` coordinates the lifecycle
  - `ExcelHeaderParser` parses header rows
  - `ExcelHeaderValidator` validates them against `ExcelSchemaLayout`
  - `RowAggregator` reconstructs row payloads
  - `ImportExecutor` validates and dispatches rows
  - `ImportIssueTracker` accumulates row and cell issues
  - `ExcelRenderer` writes a result workbook when needed
- `ImportIssueTracker` feeds the public `CellErrorMap` and `RowIssueMap`.
- `ImportResult` summarizes the overall import status and any result workbook URL.
- For template and export paths, `ExcelRenderer` produces workbook output that can be returned directly as a data URL, wrapped as `ExcelArtifact`, or uploaded through storage.

## 4. Public-facing vs internal concepts

### Public-facing concepts

- `ExcelAlchemy`
- `ImporterConfig`
- `ExporterConfig`
- `ImportMode`
- schema models declared with Pydantic
- `FieldMeta(...)`
- `ExcelMeta(...)`
- built-in codecs under `src/excelalchemy/codecs/`
- codec extension base classes:
  - `ExcelFieldCodec`
  - `CompositeExcelFieldCodec`
- `ExcelStorage`
- `ExcelArtifact`
- `ValidateHeaderResult`
- `ImportResult`
- `CellErrorMap`
- `RowIssueMap`

### Internal concepts

- `ExcelSchemaLayout`
- `ExcelHeader`
- `ExcelHeaderParser`
- `ExcelHeaderValidator`
- `WorksheetTable`
- `WorksheetRow`
- `ImportSession`
- `ImportSessionSnapshot`
- `ImportSessionPhase`
- `RowAggregator`
- `ImportIssueTracker`
- `ImportExecutor`
- `ExcelRenderer`
- `writer.py`
- storage gateway resolution in `src/excelalchemy/core/storage.py`
- Pydantic adaptation in `src/excelalchemy/helper/pydantic.py`
- primitives under `src/excelalchemy/_primitives/`

### Bridge or compatibility concepts

- `FieldMetaInfo`
  - Important runtime object in the implementation.
  - Not the main declaration entry point for new code.
- Compatibility modules kept for the 2.x line:
  - `src/excelalchemy/types/`
  - `src/excelalchemy/exc.py`
  - `src/excelalchemy/identity.py`
  - `src/excelalchemy/header_models.py`
  - `src/excelalchemy/util/convertor.py`

## 5. Important lifecycle and flow concepts

### Import flow

The import flow is the richest lifecycle in the repository.

- Start point:
  - `ExcelAlchemy.import_data(...)`
  - implemented in `src/excelalchemy/core/alchemy.py`
- Runtime owner:
  - `ImportSession`
  - `src/excelalchemy/core/import_session.py`
- Main lifecycle phases:
  - `INITIALIZED`
  - `WORKBOOK_LOADED`
  - `HEADERS_VALIDATED`
  - `ROWS_PREPARED`
  - `ROWS_EXECUTED`
  - `RESULT_RENDERED`
  - `COMPLETED`
- Decision points:
  - header valid or not via `ValidateHeaderResult`
  - row valid or not through `ImportExecutor`
  - overall result via `ValidateResult`:
    - `HEADER_INVALID`
    - `DATA_INVALID`
    - `SUCCESS`
- Workbook-facing row result concept:
  - `ValidateRowResult`
  - values:
    - `SUCCESS`
    - `FAIL`

### Template generation flow

- Start points:
  - `ExcelAlchemy.download_template(...)`
  - `ExcelAlchemy.download_template_artifact(...)`
- Core idea:
  - schema contract -> field metadata -> schema layout -> worksheet table -> renderer -> workbook output
- Main components:
  - `src/excelalchemy/core/alchemy.py`
  - `src/excelalchemy/core/schema.py`
  - `src/excelalchemy/core/rendering.py`
  - `src/excelalchemy/core/writer.py`

### Export flow

- Start points:
  - `ExcelAlchemy.export(...)`
  - `ExcelAlchemy.export_artifact(...)`
  - `ExcelAlchemy.export_upload(...)`
- Core idea:
  - export model + export rows -> selected output keys -> worksheet table -> renderer -> artifact or uploaded workbook
- Main components:
  - `src/excelalchemy/core/alchemy.py`
  - `src/excelalchemy/core/schema.py`
  - `src/excelalchemy/core/rendering.py`
  - `src/excelalchemy/core/writer.py`
  - `src/excelalchemy/core/storage_protocol.py`
  - `src/excelalchemy/core/storage.py`

### Storage integration flow

- Start point:
  - `storage=...` on `ImporterConfig` or `ExporterConfig`
- Core idea:
  - input workbooks are read as `WorksheetTable`
  - rendered workbooks are uploaded and returned as URLs
  - custom storage readers currently use `src/excelalchemy/core/table.py` for that table shape
- Main components:
  - `src/excelalchemy/core/storage_protocol.py`
  - `src/excelalchemy/core/storage.py`
  - `src/excelalchemy/core/storage_minio.py`
  - `src/excelalchemy/core/table.py`
  - `examples/custom_storage.py`

## Mental model in one sentence

- `ExcelAlchemy` treats an Excel workbook as a typed contract derived from Pydantic models, then routes that contract through layout, parsing, validation, execution, rendering, and storage boundaries.
