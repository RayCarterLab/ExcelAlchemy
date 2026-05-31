# Public API Guide

This page summarizes the current ExcelAlchemy 3.0 public surface for
application code. Historical 2.x migration paths are not current API. Coding
agents should pair this with `docs/agent/coding-agent-guide.md` before editing
public contracts.

## Public Modules

- `excelalchemy`: package root for the common facade, config, codecs, results,
  storage protocol, artifacts, and identity wrappers.
- `excelalchemy.config`: `ImporterConfig`, `ExporterConfig`, `ImportMode`, and
  normalized config objects.
- `excelalchemy.columns`: `ExcelColumn(...)` and immutable `ExcelColumnSpec`
  declarations for `typing.Annotated`.
- `excelalchemy.codecs`: built-in workbook codecs and codec extension base
  classes.
- `excelalchemy.results`: import results, issue maps, preflight results,
  lifecycle events, and API payload helpers.
- `excelalchemy.errors`: public exceptions.
- `excelalchemy.storage`: `ExcelStorage` protocol for workbook IO.
- `excelalchemy.artifacts`: `ExcelArtifact` transport wrapper.

## Declaration Style

Prefer ordinary Python annotations plus Excel metadata in `Annotated`:

```python
from typing import Annotated

from pydantic import BaseModel, Field

from excelalchemy import ExcelColumn, NumberCodec


class EmployeeImport(BaseModel):
    name: Annotated[str, ExcelColumn(label='Name', required=True, order=1)]
    salary: Annotated[
        float | None,
        Field(ge=0),
        ExcelColumn(label='Salary', codec=NumberCodec(fraction_digits=2), order=2),
    ]
```

The Python type remains visible to Pydantic. Excel-specific behavior belongs in
`ExcelColumn(...)` and codec configuration helpers.

## Workflow Surface

- `ExcelAlchemy.download_template(...)`
- `ExcelAlchemy.download_template_artifact(...)`
- `ExcelAlchemy.preflight_import(...)`
- `ExcelAlchemy.import_data(..., on_event=...)`
- `ExcelAlchemy.export(...)`
- `ExcelAlchemy.export_artifact(...)`
- `ExcelAlchemy.export_upload(...)`

Inspection properties use explicit names:

- `worksheet_table`
- `header_table`
- `cell_error_map`
- `row_error_map`
- `last_import_snapshot`

## Storage

Config objects accept a single backend path:

```python
from excelalchemy import ImporterConfig
from excelalchemy.storage.minio import MinioStorageGateway

config = ImporterConfig.for_create(
    EmployeeImport,
    creator=create_employee,
    storage=MinioStorageGateway(minio_client, bucket_name='excel-files'),
)
```

Custom backends implement `ExcelStorage`.

## Removed 2.x Surface

These paths and names are intentionally not part of 3.0:

- `excelalchemy.const`
- `excelalchemy.exc`
- `excelalchemy.identity`
- `excelalchemy.header_models`
- `excelalchemy.types.*`
- `excelalchemy.metadata`
- `excelalchemy.util.convertor`
- `excelalchemy.core.*`
- `excelalchemy.helper.*`
- `excelalchemy.i18n.*`
- `excelalchemy._primitives.*`
- config fields `minio`, `bucket_name`, `url_expires`
- facade aliases `df`, `header_df`, `cell_errors`, `row_errors`
- codec aliases `comment`, `serialize`, `deserialize`, `__validate__`,
  `model_items`
- metadata alias `value_type`

Do not add compatibility shims for these names to make old tests or examples
pass.
