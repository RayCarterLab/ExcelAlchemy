# ExcelAlchemy

Schema-driven Python library for typed Excel import/export workflows with Pydantic and locale-aware workbooks.

ExcelAlchemy turns Pydantic models into typed workbook contracts:

- generate Excel templates from code
- validate uploaded workbooks
- map failures back to rows and cells
- render workbook-facing output in `zh-CN` or `en`
- keep storage pluggable through `ExcelStorage`

[GitHub Repository](https://github.com/RayCarterLab/ExcelAlchemy) · [Full README](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/README.md) · [Architecture](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/architecture.md) · [Migration Notes](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/MIGRATIONS.md)

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
