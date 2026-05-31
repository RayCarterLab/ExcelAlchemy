# ExcelAlchemy

Schema-driven Python library for typed Excel import/export workflows with
Pydantic and locale-aware workbooks.

ExcelAlchemy turns Pydantic models into workbook contracts:

- generate Excel templates from code
- validate uploaded workbooks
- map failures back to rows and cells
- return result workbooks and API-friendly error payloads
- keep workbook IO pluggable through `ExcelStorage`

The current mainline is ExcelAlchemy 3.0. It uses ordinary Python annotations
plus explicit `ExcelColumn(...)` metadata. Old 2.x field factories,
compatibility imports, legacy config fields, and facade aliases are not current
API.

[GitHub Repository](https://github.com/RayCarterLab/ExcelAlchemy) · [Full README](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/README.md) · [Getting Started](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/getting-started.md) · [Examples](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/README.md) · [Public API](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/public-api.md) · [Migration Notes](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/migrations.md)

## Screenshots

### Template

![Excel template screenshot](https://raw.githubusercontent.com/RayCarterLab/ExcelAlchemy/main/docs/assets/images/portfolio-template-en.png)

### Import Result

![Excel import result screenshot](https://raw.githubusercontent.com/RayCarterLab/ExcelAlchemy/main/docs/assets/images/portfolio-import-result-en.png)

## Install

```bash
pip install ExcelAlchemy
```

Optional Minio-compatible storage support:

```bash
pip install "ExcelAlchemy[minio]"
```

## Quick Example

```python
from typing import Annotated

from pydantic import BaseModel, Field

from excelalchemy import EmailCodec, ExcelAlchemy, ExcelColumn, ImporterConfig


class EmployeeImport(BaseModel):
    name: Annotated[str, ExcelColumn(label='Name', order=1)]
    email: Annotated[
        str,
        Field(min_length=8),
        ExcelColumn(
            label='Email',
            codec=EmailCodec(),
            order=2,
            hint='Use your work email',
            example_value='alice@company.com',
        ),
    ]


alchemy = ExcelAlchemy(ImporterConfig(EmployeeImport, locale='en'))
template = alchemy.download_template_artifact(filename='employees-template.xlsx')

excel_bytes = template.as_bytes()
```

## Import Workflow

The shortest import path is:

```text
template -> preflight -> import -> remediation -> delivery
```

Minimal backend sketch:

```python
from excelalchemy.results import ImportLifecycleEvent, build_frontend_remediation_payload


events: list[ImportLifecycleEvent] = []

preflight = alchemy.preflight_import('employees.xlsx')
if preflight.is_valid:
    result = await alchemy.import_data(
        'employees.xlsx',
        'employees-result.xlsx',
        on_event=events.append,
    )
    payload = {
        'result': result.to_api_payload(),
        'cell_errors': alchemy.cell_error_map.to_api_payload(),
        'row_errors': alchemy.row_error_map.to_api_payload(),
        'remediation': build_frontend_remediation_payload(
            result=result,
            cell_error_map=alchemy.cell_error_map,
            row_error_map=alchemy.row_error_map,
        ),
    }
```

## Why ExcelAlchemy

- Pydantic v2-based schema extraction and validation
- `Annotated[..., ExcelColumn(...)]` declaration style
- workbook comments and result workbooks in `zh-CN`, `en`, or `ja`
- pluggable storage instead of a hard-coded backend
- `openpyxl`-based runtime path without pandas
- contract tests, Ruff, and Pyright in the development workflow

## Learn More

- [Full project README](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/README.md)
- [Getting started](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/getting-started.md)
- [Examples showcase](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/examples-showcase.md)
- [Result objects](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/result-objects.md)
- [API response cookbook](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/api-response-cookbook.md)
- [Platform architecture](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/platform-architecture.md)
- [Migration notes](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/migrations.md)
