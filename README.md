> [中文](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/README_cn.md) | English
>


# ExcelAlchemy User Guide
# 📊 ExcelAlchemy [![codecov](https://codecov.io/gh/SundayWindy/ExcelAlchemy/branch/main/graph/badge.svg?token=F6QVKL37XH)](https://codecov.io/gh/SundayWindy/ExcelAlchemy)    [![](https://tokei.rs/b1/github.com/SundayWindy/ExcelAlchemy?category=lines)](https://github.com/SundayWindy/ExcelAlchemy)
ExcelAlchemy is a Python library for schema-driven Excel import and export with Pydantic models. It supports pluggable storage backends and currently ships with a built-in Minio-compatible implementation.

## Installation

Use pip to install:

```
pip install ExcelAlchemy
```

If you want the built-in Minio backend, install the optional extra:

```bash
pip install "ExcelAlchemy[minio]"
```

ExcelAlchemy currently supports Python 3.12 through 3.14.
Python 3.14 is the primary supported version, and new behavior or dependency updates may be optimized for it first.

## Storage backends

ExcelAlchemy accepts any storage backend that implements the `ExcelStorage` protocol.

- Use `storage=...` when you want a custom backend.
- The legacy `minio=..., bucket_name=..., url_expires=...` configuration still works and uses the built-in Minio implementation.
- If you use the built-in Minio backend, install `ExcelAlchemy[minio]`.

Example custom in-memory storage:

```python
from base64 import b64decode
from io import BytesIO
from typing import Any

from openpyxl import load_workbook
from pydantic import BaseModel

from excelalchemy import ExcelAlchemy, ExcelStorage, ExporterConfig, FieldMeta, ImporterConfig, Number, String
from excelalchemy.core.table import WorksheetTable
from excelalchemy.types.identity import UrlStr


class InMemoryExcelStorage(ExcelStorage):
    def __init__(self) -> None:
        self.fixtures: dict[str, bytes] = {}
        self.uploaded: dict[str, bytes] = {}

    def read_excel_table(self, input_excel_name: str, *, skiprows: int, sheet_name: str) -> WorksheetTable:
        workbook = load_workbook(BytesIO(self.fixtures[input_excel_name]), data_only=True)
        try:
            worksheet = workbook[sheet_name]
            rows = [
                [None if value is None else str(value) for value in row]
                for row in worksheet.iter_rows(
                    min_row=skiprows + 1,
                    max_row=worksheet.max_row,
                    max_col=worksheet.max_column,
                    values_only=True,
                )
            ]
        finally:
            workbook.close()

        while rows and all(value is None for value in rows[-1]):
            rows.pop()

        return WorksheetTable(rows=rows)

    def upload_excel(self, output_name: str, content_with_prefix: str) -> UrlStr:
        _, payload = content_with_prefix.split(',', 1)
        self.uploaded[output_name] = b64decode(payload)
        return UrlStr(f'memory://{output_name}')


class Importer(BaseModel):
    age: Number = FieldMeta(label='Age', order=1)
    name: String = FieldMeta(label='Name', order=2)


async def creator(data: dict[str, Any], context: None) -> Any:
    return data


storage = InMemoryExcelStorage()

# Template generation does not require a storage backend.
template_alchemy = ExcelAlchemy(ImporterConfig(Importer, creator=creator))
template_base64 = template_alchemy.download_template()
print(template_base64[:40])

# Uploading export output uses the custom storage backend.
export_alchemy = ExcelAlchemy(ExporterConfig(Importer, storage=storage))
url = export_alchemy.export_upload('people.xlsx', [{'age': 18, 'name': 'Alice'}])
print(url)  # memory://people.xlsx
print(storage.uploaded['people.xlsx'][:2])  # b'PK'
```

## Usage

### Choose template/result language

`locale` controls Excel-facing display text such as:

- the header hint in row 1
- column comments
- result workbook column titles
- row-level validation status text

The default is `zh-CN`. If you want an English template and result workbook, pass `locale='en'`.

```python
from excelalchemy import ExcelAlchemy, FieldMeta, ImporterConfig, Number, String
from pydantic import BaseModel


class Importer(BaseModel):
    age: Number = FieldMeta(label='Age', order=1)
    name: String = FieldMeta(label='Name', order=2)


alchemy_zh = ExcelAlchemy(ImporterConfig(Importer, locale='zh-CN'))
template_zh = alchemy_zh.download_template()

alchemy_en = ExcelAlchemy(ImporterConfig(Importer, locale='en'))
template_en = alchemy_en.download_template()
```

The same `locale` option also applies to import result workbooks:

```python
from excelalchemy import ExcelAlchemy, ImporterConfig


alchemy = ExcelAlchemy(
    ImporterConfig(
        Importer,
        creator=create_func,
        storage=storage,
        locale='en',
    )
)
result = await alchemy.import_data(input_excel_name='people.xlsx', output_excel_name='people-result.xlsx')
```

### Generate Excel template from Pydantic class

```python
from excelalchemy import ExcelAlchemy, FieldMeta, ImporterConfig, Number, String
from pydantic import BaseModel

class Importer(BaseModel):
    age: Number = FieldMeta(label='Age', order=1)
    name: String = FieldMeta(label='Name', order=2)
    phone: String | None = FieldMeta(label='Phone', order=3)
    address: String | None = FieldMeta(label='Address', order=4)

alchemy = ExcelAlchemy(ImporterConfig(Importer))
base64content = alchemy.download_template()
print(base64content)

```
* The above is a simple example of generating an Excel template from a Pydantic class. The Excel template will have a sheet named "Sheet1" with four columns: "Age", "Name", "Phone", and "Address". "Age" and "Name" are required fields, while "Phone" and "Address" are optional.
* The method returns a base64-encoded string that represents the Excel file. You can directly use the window.open method to open the Excel file in the front-end, or download it by typing the base64 content in the browser's address bar.
* When downloading a template, you can also specify some default values, for example:

```python
from excelalchemy import ExcelAlchemy, FieldMeta, ImporterConfig, Number, String
from pydantic import BaseModel

class Importer(BaseModel):
    age: Number = FieldMeta(label='Age', order=1)
    name: String = FieldMeta(label='Name', order=2)
    phone: String | None = FieldMeta(label='Phone', order=3)
    address: String | None = FieldMeta(label='Address', order=4)

alchemy = ExcelAlchemy(ImporterConfig(Importer))

sample = [
    {'age': 18, 'name': 'Bob', 'phone': '12345678901', 'address': 'New York'},
    {'age': 19, 'name': 'Alice', 'address': 'Shanghai'},
    {'age': 20, 'name': 'John', 'phone': '12345678901'},
]
base64content = alchemy.download_template(sample)
print(base64content)
```
In the above example, we specify a sample, which is a list of dictionaries. Each dictionary represents a row in the Excel sheet, and the keys represent column names. The method returns an Excel template with default values filled in. If a field doesn't have a default value, it will be empty. For example:
* ![image](https://github.com/SundayWindy/ExcelAlchemy/raw/main/images/001_sample_template.png)

### Parse a Pydantic class from an Excel file and create data

The recommended way to use the built-in Minio backend is to pass an explicit storage strategy:

```python
import asyncio
from typing import Any

from excelalchemy import ExcelAlchemy, FieldMeta, ImporterConfig, Number, String
from excelalchemy.core.storage import MinioStorageGateway
from minio import Minio
from pydantic import BaseModel


class Importer(BaseModel):
    age: Number = FieldMeta(label='Age', order=1)
    name: String = FieldMeta(label='Name', order=2)
    phone: String | None = FieldMeta(label='Phone', order=3)
    address: String | None = FieldMeta(label='Address', order=4)


def data_converter(data: dict[str, Any]) -> dict[str, Any]:
    """Custom data converter, here you can modify the result of Importer.model_dump()"""
    data['age'] = data['age'] + 1
    data['name'] = {"phone": data['phone']}
    return data


async def create_func(data: dict[str, Any], context: None) -> Any:
    """Your defined creation function"""
    # do something to create data
    return True


async def main():
    storage = MinioStorageGateway(
        ImporterConfig(
            create_importer_model=Importer,
            creator=create_func,
            data_converter=data_converter,
            minio=Minio(endpoint=''),  # reachable minio address
            bucket_name='excel',
            url_expires=3600,
        )
    )
    alchemy = ExcelAlchemy(
        ImporterConfig(
            create_importer_model=Importer,
            creator=create_func,
            data_converter=data_converter,
            storage=storage,
        )
    )
    result = await alchemy.import_data(input_excel_name='test.xlsx', output_excel_name="test.xlsx")
    print(result)


asyncio.run(main())
```

* The example above uses the built-in Minio-compatible storage strategy, so you need to install Minio and create a bucket if you want to use that backend.
* If you already have your own object store, local filesystem layer, or test double, pass it as `storage=...` instead.
* The older `minio=..., bucket_name=..., url_expires=...` configuration is still supported for compatibility, but `storage=MinioStorageGateway(...)` is now the preferred form.
* You can also set `locale='en'` or `locale='zh-CN'` on `ImporterConfig(...)` to control the language used in generated templates and import result workbooks.

* The imported Excel file must be generated by the `download_template()` method, otherwise, it will produce a parsing error.
* In the above example, we define a `data_converter` function, which is used to modify the result of `Importer.model_dump().` The final result of `data_converter` function will be the parameter of the create_func function. This function is optional if you don't need to modify the data.
* The `create_func` function is used to create data, and the parameter is the result of the data_converter function, and context is None. You can create data, for example, by storing the data in a database.
* The `input_excel_name` parameter of the `import_data()` method is the storage key used by your backend, and the `output_excel_name` parameter is where the parsing result workbook will be uploaded. This file contains all the input data, and if any data fails the parsing, the first column of that data has an error message, and the error-producing cell is highlighted in red.
* The method returns an `ImportResult` type result. You can see the definition of this class in the code. This class contains all the information about the parsing result, such as the number of successfully imported data, the number of failed data, the failed data, etc.
* An example of the importing result is shown in the following image:
![image](https://github.com/SundayWindy/ExcelAlchemy/raw/main/images/002_import_result.png)


## Development

Install `uv`, then sync the development environment:

```bash
uv sync --extra development
uv run pre-commit install
```

The project uses the standard `src/` layout, so local development should go through the managed `uv` environment rather than relying on repository-root imports.

Common local commands:

```bash
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests
uv build
```

The CI workflow uses `uv` for dependency management and runs `ruff`, `pyright`, and the test matrix on Python 3.12, 3.13, and 3.14.

### Contributing

If you have questions, bug reports, or feature ideas, please open an issue in [GitHub Issues](https://github.com/RayCarterLab/ExcelAlchemy/issues).
Pull requests are welcome. Before opening one, please run the local validation commands above and update documentation when behavior changes.

### License
ExcelAlchemy is licensed under the MIT license. For more information, please see the [LICENSE](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/LICENSE) file.
