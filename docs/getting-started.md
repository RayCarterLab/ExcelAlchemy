# Getting Started

This page is the fastest way to get productive with ExcelAlchemy.

If you want screenshots and fixed workflow outputs first, see
[`docs/examples-showcase.md`](examples-showcase.md).
If you want the full public surface and compatibility boundaries, see
[`docs/public-api.md`](public-api.md).
If you want to understand the result objects and how to surface them through an
API, see
[`docs/result-objects.md`](result-objects.md).
If you want practical expectations around formulas, cached values, server-side
processing, and workbook fidelity, see
[`docs/limitations.md`](limitations.md).
If you need operational guidance for larger uploads, memory-sensitive services,
or background-job planning, see
[`docs/performance.md`](performance.md).
If you want a role-based reading path, see
[`docs/integration-roadmap.md`](integration-roadmap.md).

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

If you want generated templates to give users a more concrete example before
upload, you can add template UX metadata such as `hint` and `example_value`:

```python
class EmployeeImporter(BaseModel):
    work_email: Annotated[
        String,
        Field(min_length=8),
        ExcelMeta(
            label='Work email',
            order=3,
            hint='Use your company email address',
            example_value='alice@company.com',
        ),
    ]
```

This is additive. It does not change import behavior or worksheet layout. It
only adds a more helpful header comment in the generated template, for example:

- `Hint: Use your company email address`
- `Example: alice@company.com`

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
  [`examples/custom_storage.py`](../examples/custom_storage.py)
- export workflow:
  [`examples/export_workflow.py`](../examples/export_workflow.py)
- import workflow:
  [`examples/employee_import_workflow.py`](../examples/employee_import_workflow.py)

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

1. [`examples/annotated_schema.py`](../examples/annotated_schema.py)
2. [`examples/employee_import_workflow.py`](../examples/employee_import_workflow.py)
3. [`examples/create_or_update_import.py`](../examples/create_or_update_import.py)
4. [`examples/export_workflow.py`](../examples/export_workflow.py)
5. [`examples/README.md`](../examples/README.md)

If you want the shorter visual summary, see
[`docs/examples-showcase.md`](examples-showcase.md).

## 7. Know The Stable Boundaries

Before you wire ExcelAlchemy into a larger project, review:

- [`docs/public-api.md`](public-api.md)
- [`MIGRATIONS.md`](../MIGRATIONS.md)

These two documents explain:

- which modules are stable public entry points
- which import paths are compatibility-only in 2.x
- how storage and Minio should be configured going forward

## 8. Surface Results In Your Own API

If you are integrating ExcelAlchemy into a web backend, the recommended public
result surface is:

- `ImportResult`
- `alchemy.cell_error_map`
- `alchemy.row_error_map`

These objects let you return:

- a high-level import summary
- row-level error summaries
- cell-level coordinates for UI highlighting

See:

- [`docs/result-objects.md`](result-objects.md)
- [`docs/api-response-cookbook.md`](api-response-cookbook.md)
- [`examples/fastapi_reference/README.md`](../examples/fastapi_reference/README.md)
