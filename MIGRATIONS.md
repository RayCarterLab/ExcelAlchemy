# Migration Notes

## Upgrading To 2.0

ExcelAlchemy 2.0 keeps the public workflow recognizable, but the project has changed
meaningfully in platform support, dependencies, and architecture.

This guide focuses on what users are most likely to notice when upgrading from the
`1.x` line to `2.0.0`.

## Platform Support

- Python 3.10 and 3.11 are no longer supported
- Supported versions are now Python 3.12, 3.13, and 3.14
- Python 3.14 is the primary support target

## Pydantic

- ExcelAlchemy now targets Pydantic v2
- Internal field extraction and validation integration were redesigned around adapter boundaries

If your application is still pinned to Pydantic v1, upgrade that dependency before upgrading ExcelAlchemy.

## Storage

### What changed

- Minio is no longer a mandatory dependency
- Storage is now modeled as the `ExcelStorage` protocol
- The built-in Minio backend is still available, but as an optional extra

### The 2.x recommendation in one sentence

For all new 2.x application code, prefer:

```python
storage=...
```

Treat the older built-in Minio fields as compatibility-only API surface.

### New install patterns

Base install:

```bash
pip install ExcelAlchemy
```

Install with built-in Minio support:

```bash
pip install "ExcelAlchemy[minio]"
```

### Recommended configuration pattern

Prefer explicit storage objects:

```python
from excelalchemy import ExporterConfig
from excelalchemy.core.storage_minio import MinioStorageGateway

config = ExporterConfig.for_storage(
    ExporterModel,
    storage=MinioStorageGateway(minio_client, bucket_name='excel-files'),
)
```

### Legacy compatibility

The older `minio=..., bucket_name=..., url_expires=...` configuration style is
still accepted for compatibility, but:

- it is not the recommended 2.x path
- it emits a deprecation warning
- it should be treated as a migration bridge rather than a long-term API choice

If you are writing new code in the 2.x line, use `storage=...` instead.

### Recommended importer constructors

The 2.2 line also adds more explicit constructors for common importer modes:

```python
config = ImporterConfig.for_create(ImporterModel, creator=create_func, storage=storage)
```

```python
config = ImporterConfig.for_update(ImporterModel, updater=update_func, storage=storage)
```

```python
config = ImporterConfig.for_create_or_update(
    create_importer_model=CreateModel,
    update_importer_model=UpdateModel,
    is_data_exist=is_data_exist,
    creator=create_func,
    updater=update_func,
    storage=storage,
)
```

### Examples and docs

If you want concrete examples of the recommended 2.x API shape, see:

- [`docs/getting-started.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/getting-started.md)
- [`docs/public-api.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/public-api.md)
- [`examples/README.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/README.md)
- [`docs/examples-showcase.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/examples-showcase.md)

## pandas

- ExcelAlchemy no longer uses or installs `pandas` at runtime
- Workbook IO is now based on `openpyxl` and an internal `WorksheetTable`

If your application depended on pandas being installed as an indirect dependency, install it explicitly in your own project.

## Runtime And Workbook Language

- Runtime exceptions are standardized in English
- Workbook-facing display text is locale-aware
- Supported display locales currently include `zh-CN` and `en`

Example:

```python
config = ImporterConfig(ImporterModel, creator=create_func, locale='en')
```

## Module Paths

- `excelalchemy.types.*` and `excelalchemy.types.value.*` are deprecated compatibility imports in the 2.x line
- those imports now emit `ExcelAlchemyDeprecationWarning`
- the compatibility layer will be removed in ExcelAlchemy 3.0

Prefer the new module layout:

- `excelalchemy.metadata`
- `excelalchemy.results`
- `excelalchemy.config`
- `excelalchemy.codecs`
- the `excelalchemy` package root for common public types such as `Label`, `Key`, and `UrlStr`

Additional top-level module guidance:

- `excelalchemy.exceptions` is the stable replacement for `excelalchemy.exc`
- `excelalchemy.identity` is now a compatibility import; prefer `from excelalchemy import Label, Key, UrlStr, ...`
- `excelalchemy.header_models` is internal and should not be imported in application code
- `docs/public-api.md` summarizes stable public modules, compatibility modules, and internal modules

## Import Inspection Names

The 2.2 line also clarifies the recommended names for inspecting import-run
state from the facade:

- prefer `worksheet_table` over `df`
- prefer `header_table` over `header_df`
- prefer `cell_error_map` over `cell_errors`
- prefer `row_error_map` over `row_errors`

The old names still work as compatibility aliases in the 2.x line, but new
code should use the clearer names above.

## Recommended Upgrade Checklist

1. Upgrade your Python runtime to 3.12+.
2. Upgrade your project to Pydantic v2.
3. Decide whether you need `ExcelAlchemy[minio]` or a custom `storage=...` implementation.
4. If you expose templates or import result workbooks to English-speaking users, set `locale='en'`.
5. Run your import/export flows against `2.0.0` in a staging environment before promoting it in production.
