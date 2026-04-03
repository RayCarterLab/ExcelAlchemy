# Public API Guide

This page summarizes which ExcelAlchemy modules are intended to be stable public
entry points, which ones remain compatibility shims for the 2.x line, and which
ones should be treated as internal implementation details.

## Stable Public Modules

These modules are the recommended import paths for application code:

- `excelalchemy`
  The package root re-exports the most common public types, codecs, config
  objects, and result models.
- `excelalchemy.config`
  Public workflow configuration objects such as `ImporterConfig`,
  `ExporterConfig`, and `ImportMode`.
- `excelalchemy.metadata`
  Public metadata entry points such as `FieldMeta(...)`, `ExcelMeta(...)`, and
  `PatchFieldMeta`.
- `excelalchemy.results`
  Structured import result models such as `ImportResult`,
  `ValidateResult`, and `ValidateHeaderResult`.
- `excelalchemy.exceptions`
  Stable exception module for `ConfigError`, `ExcelCellError`,
  `ExcelRowError`, and `ProgrammaticError`.
- `excelalchemy.codecs`
  Public codec namespace for built-in Excel field codecs.

## Stable Public Protocols And Concepts

- `ExcelStorage`
  The recommended backend integration contract for workbook IO.
- `storage=...`
  The recommended backend configuration pattern in the 2.x line.
- `ExcelArtifact`
  The recommended return shape when you need bytes, base64, or data URLs.

## Compatibility Modules In 2.x

These imports still work in the 2.x line, but should be treated as migration
paths rather than long-term public module choices:

- `excelalchemy.exc`
  Deprecated compatibility layer. Prefer `excelalchemy.exceptions`.
- `excelalchemy.identity`
  Deprecated compatibility layer. Prefer imports from the package root.
- `excelalchemy.header_models`
  Compatibility layer; application code should not depend on it.
- `excelalchemy.types.*`
  Deprecated compatibility namespace retained for 2.x migrations.
- `excelalchemy.util.convertor`
  Deprecated compatibility import. Prefer `excelalchemy.util.converter`.

## Internal Modules

These modules may change without notice and should not be imported directly in
application code:

- `excelalchemy.core.*`
- `excelalchemy.helper.*`
- `excelalchemy.i18n.*`
- `excelalchemy._primitives.*`

The internals are intentionally allowed to evolve as the 2.x architecture
continues to consolidate.

## Recommended Import Style

Prefer imports like:

```python
from excelalchemy import ExcelAlchemy, ExcelMeta, FieldMeta, ImporterConfig, ValidateResult
from excelalchemy.config import ExporterConfig, ImportMode
from excelalchemy.exceptions import ConfigError
```

Avoid depending on implementation details such as:

```python
from excelalchemy.core.alchemy import ExcelAlchemy
from excelalchemy.core.headers import ExcelHeaderParser
from excelalchemy._primitives.identity import UniqueLabel
```

## Deprecation Direction

The 2.x line keeps compatibility shims to support migration, but the long-term
direction is:

- public API from `excelalchemy`, `excelalchemy.config`,
  `excelalchemy.metadata`, `excelalchemy.results`, `excelalchemy.exceptions`,
  and `excelalchemy.codecs`
- backend integration through `ExcelStorage`
- internal orchestration and helper modules treated as implementation details
