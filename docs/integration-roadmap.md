# Integration Roadmap

This page helps you choose a reading path through the ExcelAlchemy docs based on
what you are trying to build.

If you want the fastest general entry point, start with
[`docs/getting-started.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/getting-started.md).
If you want the expectations-setting page for formulas, server-side execution,
large workbooks, and round-trip limits, see
[`docs/limitations.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/limitations.md).
If you want screenshots and captured workflow output first, see
[`docs/examples-showcase.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/examples-showcase.md).

## 1. If You Are Integrating ExcelAlchemy For The First Time

Recommended order:

1. [`docs/getting-started.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/getting-started.md)
2. [`docs/limitations.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/limitations.md)
3. [`docs/public-api.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/public-api.md)
4. [`examples/README.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/README.md)
5. [`docs/examples-showcase.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/examples-showcase.md)

Focus on these concepts first:

- stable import paths
- schema declaration style
- `storage=...` as the recommended backend integration path
- the difference between import, create-or-update, and export workflows
- the practical limits of formula handling, performance, and workbook fidelity

## 2. If You Are Building A Backend API

Recommended order:

1. [`docs/result-objects.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/result-objects.md)
2. [`docs/api-response-cookbook.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/api-response-cookbook.md)
3. [`examples/fastapi_reference/README.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/fastapi_reference/README.md)
4. [`docs/public-api.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/public-api.md)

Focus on these objects:

- `ImportResult`
- `CellErrorMap`
- `RowIssueMap`

Use these payload helpers directly in your API layer:

- `ImportResult.to_api_payload()`
- `CellErrorMap.to_api_payload()`
- `RowIssueMap.to_api_payload()`

## 3. If You Are Building Frontend Error Displays

Recommended order:

1. [`docs/result-objects.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/result-objects.md)
2. [`docs/api-response-cookbook.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/api-response-cookbook.md)
3. [`examples/fastapi_reference/README.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/fastapi_reference/README.md)

Focus on these payload fields:

- `code`
- `message_key`
- `message`
- `display_message`

And these grouped or summary helpers:

- `summary.by_field`
- `summary.by_row`
- `summary.by_code`
- `facets.field_labels`
- `facets.codes`
- `facets.row_numbers_for_humans`
- `grouped.messages_by_field`
- `grouped.messages_by_row`
- `grouped.messages_by_code`

## 4. If You Want Copyable Reference Code

Start here:

- [`examples/employee_import_workflow.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/employee_import_workflow.py)
- [`examples/create_or_update_import.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/create_or_update_import.py)
- [`examples/export_workflow.py`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/export_workflow.py)
- [`examples/fastapi_reference/README.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/fastapi_reference/README.md)

## 5. If You Need Migration And Compatibility Context

Read:

1. [`MIGRATIONS.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/MIGRATIONS.md)
2. [`docs/public-api.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/public-api.md)

This is the best route when you need to answer:

- which imports are stable
- which imports are compatibility-only
- how the 2.x line treats legacy Minio configuration
