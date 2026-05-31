# Platform-to-Code Mapping

This page maps the current ExcelAlchemy 3.0 platform vocabulary to the source
tree. It is a human-readable ownership map; agent-facing rules live in
`docs/agent/architecture-boundaries.md`.

## Assessment Summary

| Platform area | Primary code owners | Status |
| --- | --- | --- |
| Template Authoring Layer | `field_metadata/`, `columns.py`, `schema/layout.py`, `rendering/`, `codecs/`, `runtime/facade.py` | current |
| Preflight Gate Layer | `runtime/preflight.py`, `worksheet/header_parser.py`, `worksheet/header_validator.py`, `runtime/facade.py`, `results/`, `storage/` | current |
| Import Runtime Layer | `runtime/facade.py`, `runtime/import_session.py`, `runtime/rows.py`, `runtime/executor.py`, `adapters/pydantic.py`, `schema/layout.py` | current |
| Lifecycle Events | `runtime/import_session.py`, public facade entry in `runtime/facade.py`, `results/` | current |
| Result Intelligence Layer | `results/`, `runtime/rows.py`, `runtime/import_session.py`, `runtime/executor.py` | current |
| Artifact / Delivery Layer | `artifacts.py`, `storage/`, `storage/gateway.py`, `storage/minio.py`, `rendering/`, `runtime/facade.py` | current |

## Layer Ownership

### Template Authoring Layer

Primary files:

- `src/excelalchemy/field_metadata/`
- `src/excelalchemy/columns.py`
- `src/excelalchemy/schema/layout.py`
- `src/excelalchemy/codecs/`
- `src/excelalchemy/rendering/renderer.py`
- `src/excelalchemy/rendering/writer.py`
- `src/excelalchemy/runtime/facade.py`

Public entry points:

- `excelalchemy.ExcelColumn`
- codec helpers such as `excelalchemy.EmailCodec` and `excelalchemy.DateCodec`
- `excelalchemy.ExcelAlchemy.download_template`
- `excelalchemy.ExcelAlchemy.download_template_artifact`

### Preflight Gate Layer

Primary files:

- `src/excelalchemy/runtime/preflight.py`
- `src/excelalchemy/worksheet/header_parser.py`
- `src/excelalchemy/worksheet/header_validator.py`
- `src/excelalchemy/runtime/facade.py`
- `src/excelalchemy/results/`
- `src/excelalchemy/storage/`

Public entry points:

- `excelalchemy.ExcelAlchemy.preflight_import`
- `excelalchemy.ImportPreflightResult`

### Import Runtime Layer

Primary files:

- `src/excelalchemy/runtime/facade.py`
- `src/excelalchemy/runtime/import_session.py`
- `src/excelalchemy/runtime/rows.py`
- `src/excelalchemy/runtime/executor.py`
- `src/excelalchemy/adapters/pydantic.py`
- `src/excelalchemy/schema/layout.py`

Public entry points:

- `excelalchemy.ExcelAlchemy.import_data`
- `excelalchemy.ImporterConfig`
- `excelalchemy.ImportMode`

### Lifecycle Events

Primary files:

- `src/excelalchemy/runtime/import_session.py`
- `src/excelalchemy/runtime/facade.py`
- `src/excelalchemy/results/`

Current event vocabulary:

- `started`
- `header_validated`
- `row_processed`
- `completed`
- `failed`

### Result Intelligence Layer

Primary files:

- `src/excelalchemy/results/`
- `src/excelalchemy/runtime/rows.py`
- `src/excelalchemy/runtime/import_session.py`
- `src/excelalchemy/runtime/executor.py`

Public entry points:

- `excelalchemy.ImportResult`
- `excelalchemy.CellErrorMap`
- `excelalchemy.RowIssueMap`
- `excelalchemy.results.build_frontend_remediation_payload`

### Artifact / Delivery Layer

Primary files:

- `src/excelalchemy/artifacts.py`
- `src/excelalchemy/storage/`
- `src/excelalchemy/storage/gateway.py`
- `src/excelalchemy/storage/minio.py`
- `src/excelalchemy/rendering/renderer.py`
- `src/excelalchemy/rendering/writer.py`
- `src/excelalchemy/runtime/facade.py`

Public entry points:

- `excelalchemy.ExcelStorage`
- `excelalchemy.ExcelArtifact`
- artifact-returning facade methods
- result workbook URL on `ImportResult`

## Boundary Notes

Template authoring is a composed capability, not a single subsystem. Public
users declare fields with `Annotated[..., ExcelColumn(...)]`; implementation
work then flows through metadata, schema layout, codecs, and rendering.

Header validation appears in both preflight and import runtime by design:
preflight is a cheap structural gate, while import runtime repeats validation
for execution-time certainty.

`ImportResult`, `CellErrorMap`, `RowIssueMap`, and remediation payload helpers
describe the same run at different levels:

- `ImportResult`: top-level outcome
- maps: stable detailed inspection surfaces
- remediation payload: frontend-oriented projection

Artifact delivery uses `ExcelStorage`, but storage is not Minio-only.
`MinioStorageGateway` is one concrete backend, and application code may provide
any object that satisfies the `ExcelStorage` protocol.

## Removed 2.x Paths

The current codebase no longer uses the old bridge packages:

- `excelalchemy.core.*`
- `excelalchemy.helper.*`
- `excelalchemy.i18n.*`
- `excelalchemy._primitives.*`

Do not reintroduce these paths as compatibility modules. Use the concrete 3.0
packages listed above.
