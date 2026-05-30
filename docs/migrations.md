# Migration Notes

This page separates the current ExcelAlchemy 3.0 upgrade path from historical
2.x material. Current application code should follow the 3.0 guidance unless
you are explicitly maintaining an older release line.

## Upgrading To 3.0

ExcelAlchemy 3.0 is a breaking release. It removes the 2.x compatibility layer
and keeps only the current public API.

### Declaration style

Use ordinary Python types with explicit Excel metadata:

```python
from typing import Annotated

from pydantic import BaseModel, Field

from excelalchemy import EmailCodec, ExcelColumn, NumberCodec


class EmployeeImport(BaseModel):
    name: Annotated[str, ExcelColumn(label='Name', order=1)]
    age: Annotated[
        int,
        Field(ge=18),
        ExcelColumn(label='Age', codec=NumberCodec(), order=2),
    ]
    email: Annotated[
        str,
        Field(min_length=8),
        ExcelColumn(
            label='Email',
            codec=EmailCodec(),
            order=3,
            hint='Use your work email',
            example_value='alice@company.com',
        ),
    ]
```

Python annotations remain the data contract. `Field(...)` owns Pydantic
validation metadata. `ExcelColumn(...)` owns workbook labels, ordering, hints,
examples, and codec configuration.

### Recommended imports

Prefer imports from the package root and public modules:

```python
from excelalchemy import ExcelAlchemy, ExcelColumn, ImporterConfig, NumberCodec
from excelalchemy.config import ExporterConfig, ImportMode
from excelalchemy.storage import ExcelStorage
```

Do not import from removed 2.x compatibility paths:

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

### Storage

Use an explicit storage object:

```python
from excelalchemy import ExporterConfig
from excelalchemy.storage_minio import MinioStorageGateway

config = ExporterConfig.for_storage(
    ExporterModel,
    storage=MinioStorageGateway(minio_client, bucket_name='excel-files'),
)
```

The old `minio=...`, `bucket_name=...`, and `url_expires=...` config fields are
removed. Pass `storage=...` instead.

### Import inspection names

Use the explicit 3.0 names:

- `worksheet_table`
- `header_table`
- `cell_error_map`
- `row_error_map`

The old facade aliases `df`, `header_df`, `cell_errors`, and `row_errors` are
removed.

### Upgrade checklist

1. Replace field factories and old compatibility imports with
   `Annotated[..., ExcelColumn(...)]` and public 3.0 imports.
2. Replace legacy Minio config fields with `storage=...`.
3. Replace old facade inspection aliases with the explicit names above.
4. Review public API usage in `docs/public-api.md`.
5. Run your import, export, template, and storage flows in staging before
   upgrading production.

Current 3.0 examples:

- [`docs/getting-started.md`](getting-started.md)
- [`docs/public-api.md`](public-api.md)
- [`examples/README.md`](../examples/README.md)
- [`docs/examples-showcase.md`](examples-showcase.md)

## Upgrading To 2.0

This section is historical 2.x migration material. Keep it for users who are
reading old release paths, but do not treat it as current 3.0 guidance.

ExcelAlchemy 2.0 changed platform support, dependencies, and architecture while
keeping the broad public workflow recognizable from the 1.x line.

### Platform support

- Python 3.10 and 3.11 were no longer supported.
- Supported versions became Python 3.12, 3.13, and 3.14.
- Python 3.14 became the primary support target.

### Pydantic

- The project moved to Pydantic v2.
- Internal field extraction and validation integration moved behind adapter
  boundaries.

Applications pinned to Pydantic v1 needed to upgrade Pydantic before upgrading
ExcelAlchemy.

### Storage

2.x introduced the storage protocol direction that is current in 3.0:

```python
storage=...
```

The built-in Minio backend became optional:

```bash
pip install "ExcelAlchemy[minio]"
```

Recommended 2.x storage construction:

```python
from excelalchemy import ExporterConfig
from excelalchemy.storage_minio import MinioStorageGateway

config = ExporterConfig.for_storage(
    ExporterModel,
    storage=MinioStorageGateway(minio_client, bucket_name='excel-files'),
)
```

In the 2.x line, older `minio=..., bucket_name=..., url_expires=...`
configuration was compatibility-only. In 3.0, those fields are removed.

### Importer constructors

The 2.2 line added explicit constructors that remain useful in 3.0:

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

### pandas

- ExcelAlchemy stopped using or installing `pandas` at runtime.
- Workbook IO moved to `openpyxl` plus an internal `WorksheetTable`.

If an application depended on pandas as an indirect dependency, it needed to
install pandas directly.

### Runtime and workbook language

- Runtime exceptions were standardized in English.
- Workbook-facing display text became locale-aware.
- Supported display locales include `zh-CN` and `en`.

Example:

```python
config = ImporterConfig(ImporterModel, creator=create_func, locale='en')
```

### Historical 2.x checklist

1. Upgrade the Python runtime to 3.12+.
2. Upgrade the application to Pydantic v2.
3. Decide whether to install `ExcelAlchemy[minio]` or provide custom
   `storage=...`.
4. Set `locale='en'` for English-speaking workbook users.
5. Run import/export flows in staging before production rollout.
