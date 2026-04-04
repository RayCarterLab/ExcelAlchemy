# Examples Showcase

This page is the quickest way to understand how ExcelAlchemy looks in practice.

It complements the repository examples by surfacing the most representative
workflows, screenshots, and fixed outputs in one place. If you want the full
guided path through the examples directory, start with
[`examples/README.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/README.md).
If you want to see how import results and error maps are meant to be surfaced
through backend APIs, see
[`docs/result-objects.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/result-objects.md).
If you want copyable success and failure response shapes for backend endpoints,
see
[`docs/api-response-cookbook.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/api-response-cookbook.md).

## What ExcelAlchemy Looks Like

### Template

![Excel template screenshot](https://raw.githubusercontent.com/RayCarterLab/ExcelAlchemy/main/images/portfolio-template-en.png)

### Import Result

![Excel import result screenshot](https://raw.githubusercontent.com/RayCarterLab/ExcelAlchemy/main/images/portfolio-import-result-en.png)

## Representative Workflows

### 1. Import Workflow

Best entry point if you want to understand the core story:

- generate a workbook template
- accept a filled workbook
- validate the upload
- create domain rows
- write a result workbook back out

Source:

- [`examples/employee_import_workflow.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/employee_import_workflow.py)

Fixed output:

```text
Employee import workflow completed
Result: SUCCESS
Success rows: 1
Failed rows: 0
Result workbook URL: None
Created rows: 1
Uploaded artifacts: []
```

Full captured output:

- [`files/example-outputs/employee-import-workflow.txt`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/files/example-outputs/employee-import-workflow.txt)

### 2. Create-Or-Update Import

Best entry point if your backend mixes creates and updates in the same upload.

Source:

- [`examples/create_or_update_import.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/create_or_update_import.py)

Fixed output:

```text
Create-or-update import workflow completed
Result: SUCCESS
Success rows: 2
Failed rows: 0
Created rows: 1
Updated rows: 1
Result workbook URL: None
Uploaded artifacts: []
```

Full captured output:

- [`files/example-outputs/create-or-update-import.txt`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/files/example-outputs/create-or-update-import.txt)

### 3. Export Workflow

Best entry point if you want to see artifact generation and storage-backed
export delivery.

Source:

- [`examples/export_workflow.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/export_workflow.py)

Fixed output:

```text
Export workflow completed
Artifact filename: employees-export.xlsx
Artifact bytes: 6892
Upload URL: memory://employees-export-upload.xlsx
Uploaded objects: ['employees-export-upload.xlsx']
```

Full captured output:

- [`files/example-outputs/export-workflow.txt`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/files/example-outputs/export-workflow.txt)

### 4. Field Families

If you want to see how workbook-oriented field types read in real schemas:

- date and range fields:
  - [`examples/date_and_range_fields.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/date_and_range_fields.py)
  - [`files/example-outputs/date-and-range-fields.txt`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/files/example-outputs/date-and-range-fields.txt)
- selection-heavy forms:
  - [`examples/selection_fields.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/selection_fields.py)
  - [`files/example-outputs/selection-fields.txt`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/files/example-outputs/selection-fields.txt)

### 5. Integration Boundaries

If you want to see how ExcelAlchemy fits into backend systems:

- custom storage protocol:
  - [`examples/custom_storage.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/custom_storage.py)
  - [`files/example-outputs/custom-storage.txt`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/files/example-outputs/custom-storage.txt)
- built-in Minio path for the current 2.x line:
  - [`examples/minio_storage.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/minio_storage.py)
- FastAPI integration:
  - [`examples/fastapi_upload.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/fastapi_upload.py)
  - [`examples/fastapi_reference/README.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/fastapi_reference/README.md)
  - [`files/example-outputs/fastapi-reference.txt`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/files/example-outputs/fastapi-reference.txt)

## Recommended Reading Order

If you want to work through the examples intentionally rather than browse this
showcase:

1. [`examples/annotated_schema.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/annotated_schema.py)
2. [`examples/employee_import_workflow.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/employee_import_workflow.py)
3. [`examples/create_or_update_import.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/create_or_update_import.py)
4. [`examples/export_workflow.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/export_workflow.py)
5. [`examples/custom_storage.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/custom_storage.py)
6. [`examples/date_and_range_fields.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/date_and_range_fields.py)
7. [`examples/selection_fields.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/selection_fields.py)
8. [`examples/minio_storage.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/minio_storage.py)
9. [`examples/fastapi_upload.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/fastapi_upload.py)
10. [`examples/fastapi_reference/README.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/fastapi_reference/README.md)

Or start with the dedicated guide:

- [`examples/README.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/README.md)
