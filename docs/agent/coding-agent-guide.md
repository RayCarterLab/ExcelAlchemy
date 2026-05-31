# Coding Agent Guide

This page is the quick project brief for coding agents such as Codex, Claude
Code, and Cursor. It does not replace `AGENTS.md` or the rules in
`docs/agent/`; it summarizes the current 3.0 product shape and points agents to
the right files before editing.

## Project Summary

ExcelAlchemy is a schema-driven Python library for typed Excel import/export
workflows built around Pydantic models.

The public workflow is:

```text
Pydantic model + ExcelColumn -> template -> preflight -> import/export -> result workbook/API payload
```

The current mainline is ExcelAlchemy 3.0. Current docs, examples, tests, and
code should describe 3.0 unless a file is explicitly historical, release-note,
or migration material.

## 3.0 Public Contract

Use stable public imports in docs, tests, and examples:

```python
from typing import Annotated

from pydantic import BaseModel, Field

from excelalchemy import EmailCodec, ExcelAlchemy, ExcelColumn, ImporterConfig


class EmployeeImport(BaseModel):
    email: Annotated[
        str,
        Field(min_length=8),
        ExcelColumn(
            label='Email',
            codec=EmailCodec(),
            order=1,
            hint='Use your work email',
            example_value='alice@company.com',
        ),
    ]


alchemy = ExcelAlchemy(ImporterConfig(EmployeeImport, locale='en'))
```

Rules to preserve:

- Python annotations define the data shape.
- Pydantic `Field(...)` owns Pydantic validation metadata.
- `ExcelColumn(...)` owns workbook metadata.
- Codec helpers configure workbook parse, normalize, format, and comment
  behavior.
- Public result surfaces are `ImportResult`, `ImportPreflightResult`,
  `CellErrorMap`, `RowIssueMap`, and lifecycle events.
- Storage is configured with `storage=...` and implementations of
  `ExcelStorage`.

## Do Not Reintroduce

Do not restore removed 2.x compatibility surface in current 3.0 work:

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
- config fields `minio`, `bucket_name`, `url_expires`
- facade aliases `df`, `header_df`, `cell_errors`, `row_errors`
- field-factory wrappers or fake Python scalar/container types for codecs

If a task explicitly targets a 2.x maintenance line, stop and confirm the
branch/context before applying 3.0 removal rules.

## Where To Edit

- Public facade: `src/excelalchemy/runtime/facade.py`
- Config: `src/excelalchemy/config/`
- Column declarations: `src/excelalchemy/columns.py`
- Workbook field models: `src/excelalchemy/field_metadata/`
- Pydantic adaptation: `src/excelalchemy/adapters/pydantic.py`
- Schema layout: `src/excelalchemy/schema/layout.py`
- Header parsing and validation: `src/excelalchemy/worksheet/header_parser.py`
- Row aggregation: `src/excelalchemy/runtime/rows.py`
- Import execution: `src/excelalchemy/runtime/executor.py`
- Import session state and events: `src/excelalchemy/runtime/import_session.py`
- Rendering and workbook writing: `src/excelalchemy/rendering/renderer.py`,
  `src/excelalchemy/rendering/writer.py`
- Results and payload helpers: `src/excelalchemy/results/`
- Storage protocol and adapters: `src/excelalchemy/storage/`,
  `src/excelalchemy/storage/gateway.py`, `src/excelalchemy/storage/minio.py`
- Messages and locale text: `src/excelalchemy/messages.py`

For a broader file map, use `docs/repo-map.md`. For boundary details, use
`docs/agent/architecture-boundaries.md`.

## Docs And Examples Sync Matrix

When public usage changes, inspect the nearby docs in the same patch:

| Change | Docs/examples to inspect |
| --- | --- |
| Recommended onboarding or imports | `README.md`, `README-pypi.md`, `README_cn.md`, `docs/getting-started.md`, `docs/public-api.md` |
| Public module or removed-name boundary | `docs/public-api.md`, `docs/migrations.md`, `docs/repo-map.md`, `src/excelalchemy/README.md` |
| Import/export workflow behavior | `docs/runtime-model.md`, `docs/platform-architecture.md`, `docs/integration-blueprints.md`, `examples/README.md` |
| Result objects or API payloads | `docs/result-objects.md`, `docs/api-response-cookbook.md`, `examples/fastapi_reference/README.md` |
| Locale or message wording | `docs/locale.md`, `docs/result-objects.md`, generated example outputs if visible text changes |
| Example behavior or printed output | `examples/`, `docs/examples-showcase.md`, `docs/assets/example-outputs/`, smoke scripts |

Do not put agent-only instructions into user-facing README sections. Link to
this file or `AGENTS.md` instead.

## Validation Commands

Use focused validation for narrow changes. For docs-only changes, prefer:

```bash
uv run python scripts/smoke_docs_assets.py
```

If examples or generated output are touched:

```bash
uv run python scripts/smoke_examples.py
uv run python scripts/smoke_api_payload_snapshot.py
```

For code or public behavior changes, run the relevant focused tests and usually:

```bash
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest
```

Never hide failed or unrun validation in the final report.

## Common Task Routing

- User asks how to use the library: start with `README.md`,
  `docs/getting-started.md`, `docs/public-api.md`, and examples.
- User asks where to change behavior: start with `docs/repo-map.md`,
  `docs/agent/architecture-boundaries.md`, then the owning module and tests.
- User asks for a review: use `docs/agent/review.md` and lead with findings.
- User asks for 3.0 compatibility or removed APIs: use `docs/agent/v3-prd.md`,
  `docs/public-api.md`, and `docs/migrations.md`.
- User asks for harness work: inspect `harness/`, `harness/context_data/`, and
  the relevant harness tests before editing.
