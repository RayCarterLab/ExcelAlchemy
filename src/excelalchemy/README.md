# ExcelAlchemy Package Map

This package is being shaped for ExcelAlchemy 3.0. Use concrete responsibility
modules when editing code; do not add a generic `_internal` package and do not
restore 2.x compatibility shims.

## Public Entry Points

- `excelalchemy`: package root exports the common public API.
- `config/`: `ImporterConfig`, `ExporterConfig`, `ImportMode`, and normalized
  storage options.
- `columns.py`: `ExcelColumn(...)` and immutable column declarations for
  `typing.Annotated`.
- `codecs/`: built-in workbook codecs and codec extension base classes.
- `field_metadata/`: resolved Excel-facing field metadata used by the runtime.
- `results/`: import results, issue maps, preflight results, lifecycle events,
  and API payload helpers.
- `errors.py`: public exception exports.
- `storage/`: `ExcelStorage` protocol.
- `storage/gateway.py`: configured storage resolver and missing-storage
  fallback.
- `artifacts.py`: binary/data-URL workbook transport wrapper.

## Implementation Areas

- `adapters/`: framework boundaries, currently Pydantic model extraction and
  validation error normalization.
- `schema/`: Excel schema layout extraction and flattened column planning.
- `worksheet/`: worksheet tables, header records, header parsing, and header validation.
- `runtime/`: facade, import sessions, row aggregation, execution, and preflight.
- `rendering/`: workbook rendering and low-level writing.
- `messages.py`: runtime and workbook-facing message lookup.
- `policies.py`: named deterministic policies for layout, payload, result,
  event, and missing-value behavior.
- `diagnostics.py`: logger names and structured diagnostics helpers.

## Removed 2.x Surfaces

These paths and aliases are intentionally absent in 3.0:

- `excelalchemy.core.*`
- `excelalchemy.helper.*`
- `excelalchemy.i18n.*`
- `excelalchemy._primitives.*`
- `excelalchemy.const`
- `excelalchemy.exc`
- `excelalchemy.identity`
- `excelalchemy.header_models`
- `excelalchemy.metadata`
- `excelalchemy.types.*`
- `excelalchemy.util.convertor`
- facade aliases `df`, `header_df`, `cell_errors`, `row_errors`
- config fields `minio`, `bucket_name`, `url_expires`
- codec aliases `comment`, `serialize`, `deserialize`, `__validate__`,
  `model_items`
- metadata alias `value_type`

Use `storage=...` with an `ExcelStorage` implementation for any backend,
including `MinioStorageGateway`.
