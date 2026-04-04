# Getting Started

This page is the fastest way to get productive with ExcelAlchemy.

If you want screenshots and fixed workflow outputs first, see
[`docs/examples-showcase.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/examples-showcase.md).
If you want the full public surface and compatibility boundaries, see
[`docs/public-api.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/public-api.md).

## 1. Install

Base install:

```bash
pip install ExcelAlchemy
```

Optional built-in Minio support:

```bash
pip install "ExcelAlchemy[minio]"
```

## 2. Start With The Recommended Imports

Prefer the stable public entry points:

```python
from excelalchemy import ExcelAlchemy, FieldMeta, ImporterConfig, Number, String
from excelalchemy.config import ExporterConfig, ImportMode
from excelalchemy.exceptions import ConfigError, ExcelCellError, ExcelRowError
```

Avoid importing from internal modules such as `excelalchemy.core.*`,
`excelalchemy.helper.*`, or `excelalchemy._primitives.*` in application code.

## 3. Define A Schema

Classic style:

```python
from pydantic import BaseModel

from excelalchemy import FieldMeta, Number, String


class EmployeeImporter(BaseModel):
    full_name: String = FieldMeta(label='Full name', order=1)
    age: Number = FieldMeta(label='Age', order=2)
```

Modern annotated style:

```python
from typing import Annotated

from pydantic import BaseModel, Field

from excelalchemy import ExcelMeta, Number, String


class EmployeeImporter(BaseModel):
    full_name: Annotated[String, ExcelMeta(label='Full name', order=1)]
    age: Annotated[Number, Field(ge=18), ExcelMeta(label='Age', order=2)]
```

## 4. Pick The Workflow You Need

Import-only create flow:

```python
config = ImporterConfig.for_create(EmployeeImporter, creator=create_employee, storage=storage, locale='en')
alchemy = ExcelAlchemy(config)
```

Create-or-update flow:

```python
config = ImporterConfig.for_create_or_update(
    create_importer_model=CreateEmployeeImporter,
    update_importer_model=UpdateEmployeeImporter,
    is_data_exist=is_data_exist,
    creator=create_employee,
    updater=update_employee,
    storage=storage,
    locale='en',
)
alchemy = ExcelAlchemy(config)
```

Export flow:

```python
config = ExporterConfig.for_storage(EmployeeExporter, storage=storage, locale='en')
alchemy = ExcelAlchemy(config)
```

## 5. Prefer `storage=...`

In the 2.x line, the recommended backend integration path is always:

```python
storage=...
```

That storage object should implement the public `ExcelStorage` protocol.

Examples:

- custom storage:
  [`examples/custom_storage.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/custom_storage.py)
- export workflow:
  [`examples/export_workflow.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/export_workflow.py)
- import workflow:
  [`examples/employee_import_workflow.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/employee_import_workflow.py)

### Legacy Minio Fields

The older:

- `minio=...`
- `bucket_name=...`
- `url_expires=...`

fields are still accepted in 2.x, but they are compatibility paths only. They
emit deprecation warnings and should not be used in new application code.

If you need Minio in 2.x, prefer constructing a storage object explicitly and
passing it via `storage=...`.

## 6. Learn By Example

Recommended reading order:

1. [`examples/annotated_schema.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/annotated_schema.py)
2. [`examples/employee_import_workflow.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/employee_import_workflow.py)
3. [`examples/create_or_update_import.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/create_or_update_import.py)
4. [`examples/export_workflow.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/export_workflow.py)
5. [`examples/README.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/README.md)

If you want the shorter visual summary, see
[`docs/examples-showcase.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/examples-showcase.md).

## 7. Know The Stable Boundaries

Before you wire ExcelAlchemy into a larger project, review:

- [`docs/public-api.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/public-api.md)
- [`MIGRATIONS.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/MIGRATIONS.md)

These two documents explain:

- which modules are stable public entry points
- which import paths are compatibility-only in 2.x
- how storage and Minio should be configured going forward
