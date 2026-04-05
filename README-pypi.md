# ExcelAlchemy

Schema-driven Python library for typed Excel import/export workflows with Pydantic and locale-aware workbooks.

ExcelAlchemy turns Pydantic models into typed workbook contracts:

- generate Excel templates from code
- validate uploaded workbooks
- map failures back to rows and cells
- render workbook-facing output in `zh-CN` or `en`
- keep storage pluggable through `ExcelStorage`

The current stable release is `2.2.8`, which continues the 2.x line with a clearer integration roadmap, stronger import-failure payload smoke verification, and more direct install-time validation of the FastAPI reference app.

[GitHub Repository](https://github.com/RayCarterLab/ExcelAlchemy) · [Full README](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/README.md) · [Getting Started](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/getting-started.md) · [Integration Roadmap](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/integration-roadmap.md) · [Result Objects](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/result-objects.md) · [API Response Cookbook](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/api-response-cookbook.md) · [Examples Showcase](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/examples-showcase.md) · [Architecture](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/architecture.md) · [Migration Notes](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/MIGRATIONS.md)

## Screenshots

### Template

![Excel template screenshot](https://raw.githubusercontent.com/RayCarterLab/ExcelAlchemy/main/images/portfolio-template-en.png)

### Import Result

![Excel import result screenshot](https://raw.githubusercontent.com/RayCarterLab/ExcelAlchemy/main/images/portfolio-import-result-en.png)

## Install

```bash
pip install ExcelAlchemy
```

Optional Minio support:

```bash
pip install "ExcelAlchemy[minio]"
```

## Minimal Example

```python
from pydantic import BaseModel

from excelalchemy import ExcelAlchemy, FieldMeta, ImporterConfig, Number, String


class Importer(BaseModel):
    age: Number = FieldMeta(label='Age', order=1)
    name: String = FieldMeta(label='Name', order=2)


alchemy = ExcelAlchemy(ImporterConfig(Importer, locale='en'))
template = alchemy.download_template_artifact(filename='people-template.xlsx')

excel_bytes = template.as_bytes()
```

## Modern Annotated Example

```python
from typing import Annotated

from pydantic import BaseModel, Field

from excelalchemy import Email, ExcelAlchemy, ExcelMeta, ImporterConfig


class Importer(BaseModel):
    email: Annotated[
        Email,
        Field(min_length=10),
        ExcelMeta(label='Email', order=1, hint='Use your work email'),
    ]


alchemy = ExcelAlchemy(ImporterConfig(Importer, locale='en'))
template = alchemy.download_template_artifact(filename='people-template.xlsx')
```

## Example Outputs

These fixed outputs are generated from the repository examples by
[`scripts/generate_example_output_assets.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/scripts/generate_example_output_assets.py).

Import workflow:

```text
Employee import workflow completed
Result: SUCCESS
Success rows: 1
Failed rows: 0
Result workbook URL: None
Created rows: 1
Uploaded artifacts: []
```

Export workflow:

```text
Export workflow completed
Artifact filename: employees-export.xlsx
Artifact bytes: 6893
Upload URL: memory://employees-export-upload.xlsx
Uploaded objects: ['employees-export-upload.xlsx']
```

Full captured outputs:

- [employee-import-workflow.txt](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/files/example-outputs/employee-import-workflow.txt)
- [create-or-update-import.txt](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/files/example-outputs/create-or-update-import.txt)
- [export-workflow.txt](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/files/example-outputs/export-workflow.txt)
- [date-and-range-fields.txt](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/files/example-outputs/date-and-range-fields.txt)
- [selection-fields.txt](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/files/example-outputs/selection-fields.txt)
- [fastapi-reference.txt](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/files/example-outputs/fastapi-reference.txt)

For a single GitHub page that combines screenshots, representative workflows,
and captured outputs, see the
[Examples Showcase](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/examples-showcase.md).

If you want a copyable FastAPI-oriented reference layout rather than a single
example script, see the
[FastAPI reference project](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/fastapi_reference/README.md).

## Error Feedback

ExcelAlchemy keeps workbook-facing validation feedback readable while also
supporting API-friendly inspection in application code.

The stable 2.x result surface includes:

- `alchemy.cell_error_map`
- `alchemy.row_error_map`

These objects remain dict-like for compatibility, but also expose helpers such
as:

- `messages_at(...)`
- `messages_for_row(...)`
- `flatten()`
- `to_api_payload()`

Common field types now also produce more business-oriented error wording, such
as expected date formats, sample email/phone/URL formats, and clearer messages
for configured selection fields.

## Why ExcelAlchemy

- Pydantic v2-based schema extraction and validation
- locale-aware workbook comments and result workbooks
- pluggable storage instead of a hard-coded backend
- `openpyxl`-based runtime path without pandas
- contract tests, Ruff, and Pyright in the development workflow

## Learn More

- [Full project README](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/README.md)
- [Architecture notes](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/architecture.md)
- [Locale policy](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/locale.md)
- [Migration notes](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/MIGRATIONS.md)
