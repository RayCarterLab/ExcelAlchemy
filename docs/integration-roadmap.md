# Integration Roadmap

This page helps you choose a reading path through the ExcelAlchemy docs based on
what you are trying to build.

If you want the fastest general entry point, start with
[`docs/getting-started.md`](getting-started.md).
If you want the expectations-setting page for formulas, server-side execution,
large workbooks, and round-trip limits, see
[`docs/limitations.md`](limitations.md).
If you want screenshots and captured workflow output first, see
[`docs/examples-showcase.md`](examples-showcase.md).

## 1. If You Are Integrating ExcelAlchemy For The First Time

Recommended order:

1. [`docs/getting-started.md`](getting-started.md)
2. [`docs/limitations.md`](limitations.md)
3. [`docs/public-api.md`](public-api.md)
4. [`examples/README.md`](../examples/README.md)
5. [`docs/examples-showcase.md`](examples-showcase.md)

Focus on these concepts first:

- stable import paths
- schema declaration style
- `storage=...` as the recommended backend integration path
- the difference between import, create-or-update, and export workflows
- the practical limits of formula handling, performance, and workbook fidelity

## 2. If You Are Building A Backend API

Recommended order:

1. [`docs/result-objects.md`](result-objects.md)
2. [`docs/api-response-cookbook.md`](api-response-cookbook.md)
3. [`examples/fastapi_reference/README.md`](../examples/fastapi_reference/README.md)
4. [`docs/public-api.md`](public-api.md)

Focus on these objects:

- `ImportResult`
- `CellErrorMap`
- `RowIssueMap`

Use these payload helpers directly in your API layer:

- `ImportResult.to_api_payload()`
- `CellErrorMap.to_api_payload()`
- `RowIssueMap.to_api_payload()`
- `build_frontend_remediation_payload(...)` when the client wants compact retry guidance

## 3. If You Are Building Frontend Error Displays

Recommended order:

1. [`docs/result-objects.md`](result-objects.md)
2. [`docs/api-response-cookbook.md`](api-response-cookbook.md)
3. [`examples/fastapi_reference/README.md`](../examples/fastapi_reference/README.md)

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

If the frontend wants a compact retry-oriented payload instead of deriving its
own remediation summary, also inspect:

- `build_frontend_remediation_payload(...)`
- `remediation.suggested_action`
- `remediation.fix_hint`

## 4. If You Want Copyable Reference Code

Start here:

- [`examples/employee_import_workflow.py`](../examples/employee_import_workflow.py)
- [`examples/create_or_update_import.py`](../examples/create_or_update_import.py)
- [`examples/export_workflow.py`](../examples/export_workflow.py)
- [`examples/fastapi_reference/README.md`](../examples/fastapi_reference/README.md)

## 5. If You Need Migration And Compatibility Context

Read:

1. [`MIGRATIONS.md`](../MIGRATIONS.md)
2. [`docs/public-api.md`](public-api.md)

This is the best route when you need to answer:

- which imports are stable
- which imports are compatibility-only
- how the 2.x line treats legacy Minio configuration
