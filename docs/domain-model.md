# Domain Model

This document names the current ExcelAlchemy 3.0 concepts. Historical 2.x
compatibility surfaces are not current domain concepts.

## Core Concepts

| Concept | Primary files | Responsibility | Visibility |
| --- | --- | --- | --- |
| `ExcelAlchemy` facade | `src/excelalchemy/runtime/facade.py` | Coordinates template generation, preflight, import, export, rendering, and storage. | Public |
| Pydantic schema model | user code | Defines the Python data contract with ordinary type annotations. | Public |
| `ExcelColumn(...)` | `src/excelalchemy/columns.py` | Attaches workbook labels, ordering, hints, options, requiredness override, and explicit codec configuration through `Annotated`. | Public |
| Codec helpers | `src/excelalchemy/codecs/*.py` | Build immutable codec configuration objects such as `DateCodec.day()` and `EmailCodec()`. | Public |
| `FieldMetaInfo` | `src/excelalchemy/field_metadata/` | Resolved Excel-facing field metadata produced from `ExcelColumn(...)`; not a declaration API. | Internal runtime concept |
| `ImporterConfig` / `ExporterConfig` | `src/excelalchemy/config/` | Configure models, callbacks, locale, conversion, import mode, and explicit storage. | Public |
| `ExcelStorage` | `src/excelalchemy/storage/` | Protocol for reading workbook tables and uploading rendered workbook bytes. | Public extension surface |
| `ExcelSchemaLayout` | `src/excelalchemy/schema/layout.py` | Flattens model fields into ordered workbook columns and expands composite codecs. | Internal |
| Header parser and validator | `src/excelalchemy/worksheet/header_parser.py`, `src/excelalchemy/worksheet/header_validator.py` | Parse simple and merged headers and compare uploads with schema layout. | Internal |
| Row aggregator | `src/excelalchemy/runtime/rows.py` | Reconstructs flattened worksheet rows into model-shaped payloads and maps issues to coordinates. | Internal |
| Import executor | `src/excelalchemy/runtime/executor.py` | Validates row payloads and dispatches create, update, or create-or-update callbacks. | Internal |
| Import session | `src/excelalchemy/runtime/import_session.py` | Owns one import run, lifecycle events, counts, tables, and result rendering decisions. | Internal |
| Renderer and writer | `src/excelalchemy/rendering/` | Produce templates, exports, result workbooks, comments, colors, and result columns. | Internal |
| Result objects | `src/excelalchemy/results/` | Expose import outcomes, issue maps, preflight results, lifecycle events, and API payload helpers. | Public |

## Declaration Model

3.0 declarations use ordinary Python types:

```python
from typing import Annotated

from pydantic import BaseModel, Field

from excelalchemy import DateCodec, EmailCodec, ExcelColumn, NumberCodec


class EmployeeImport(BaseModel):
    name: Annotated[str, ExcelColumn(label='Name', order=1)]
    email: Annotated[str, ExcelColumn(label='Email', codec=EmailCodec(), order=2)]
    joined_at: Annotated[int | None, ExcelColumn(label='Joined At', codec=DateCodec.day(), order=3)]
    salary: Annotated[
        float | None,
        Field(ge=0),
        ExcelColumn(label='Salary', codec=NumberCodec(fraction_digits=2), order=4),
    ]
```

Rules:

- Python annotations define the data shape.
- `ExcelColumn(...)` defines workbook-facing metadata.
- Pydantic `Field(...)` defines Pydantic validation metadata.
- `ExcelColumn(codec=...)` selects non-default workbook parsing, formatting,
  and comment behavior.

## Execution Flow

1. `ImporterConfig` or `ExporterConfig` points `ExcelAlchemy` to one or more
   Pydantic models.
2. The Pydantic adapter resolves `Annotated[..., ExcelColumn(...)]` fields into
   `FieldMetaInfo` runtime metadata.
3. `ExcelSchemaLayout` orders fields and expands composite codecs into workbook
   columns.
4. Template/export paths render workbook output through `ExcelRenderer` and
   `ExcelWriter`.
5. Import paths parse headers, aggregate rows, validate model payloads, execute
   callbacks, collect issue maps, and render result workbooks when needed.
6. `ExcelStorage` is used only when an explicit storage backend is configured.

## Public Concepts

- `ExcelAlchemy`
- `ImporterConfig`, `ExporterConfig`, `ImportMode`
- `ExcelColumn(...)`
- codec helpers and `ExcelFieldCodec` / `CompositeExcelFieldCodec`
- `ExcelStorage`
- `ExcelArtifact`
- `ImportResult`, `ImportPreflightResult`, `ValidateHeaderResult`
- `CellErrorMap`, `RowIssueMap`
- lifecycle event models emitted by `ExcelAlchemy.import_data(..., on_event=...)`

## Removed 2.x Concepts

Do not restore these as current domain concepts:

- `FieldMeta(...)`
- `ExcelMeta(...)`
- `excelalchemy.types.*`
- `excelalchemy.exc`
- `excelalchemy.identity`
- `excelalchemy.header_models`
- `excelalchemy.const`
- `excelalchemy.util.convertor`
- `excelalchemy.core.*`
- `excelalchemy.helper.*`
- `excelalchemy.i18n.*`
- `excelalchemy._primitives.*`
- facade aliases `df`, `header_df`, `cell_errors`, `row_errors`
- legacy config fields `minio`, `bucket_name`, `url_expires`
