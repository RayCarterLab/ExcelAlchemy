# ExcelAlchemy

[![CI](https://github.com/RayCarterLab/ExcelAlchemy/actions/workflows/ci.yml/badge.svg)](https://github.com/RayCarterLab/ExcelAlchemy/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/RayCarterLab/ExcelAlchemy/graph/badge.svg)](https://app.codecov.io/gh/RayCarterLab/ExcelAlchemy)
![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-3776AB)
![Lint](https://img.shields.io/badge/lint-ruff-D7FF64)
![Typing](https://img.shields.io/badge/typing-pyright-2C6BED)

[中文 README](README_cn.md) · [About](ABOUT.md) · [Getting Started](docs/getting-started.md) · [Integration Roadmap](docs/integration-roadmap.md) · [Platform Architecture](docs/platform-architecture.md) · [Runtime Model](docs/runtime-model.md) · [Integration Blueprints](docs/integration-blueprints.md) · [Result Objects](docs/result-objects.md) · [API Response Cookbook](docs/api-response-cookbook.md) · [Code Mapping](docs/platform-code-mapping.md) · [Examples Showcase](docs/examples-showcase.md) · [Public API](docs/public-api.md) · [Locale Policy](docs/locale.md) · [Limitations](docs/limitations.md) · [Performance](docs/performance.md) · [Changelog](CHANGELOG.md) · [Migration Notes](MIGRATIONS.md)

Repository guides: [AGENTS.md](AGENTS.md) · [Repository Map](docs/repo-map.md) · [Domain Model](docs/domain-model.md) · [Agent Invariants](docs/agent/invariants.md) · [Package Guide](src/excelalchemy/README.md) · [Test Guide](tests/README.md) · [Examples Guide](examples/README.md)

Engineering records: [Plans](plans/README.md) · [Technical Debt](docs/tech-debt/README.md) · [Historical ADRs](docs/history/adr/README.md)

ExcelAlchemy is a schema-driven Python library for Excel import and export workflows.
It turns Pydantic models into typed workbook contracts: generate templates, validate uploads, map failures back to rows
and cells, and produce locale-aware result workbooks.

This repository is also a design artifact.
It documents a series of deliberate engineering choices: `src/` layout, Pydantic v2 migration, pandas removal,
pluggable storage, `uv`-based workflows, and locale-aware workbook output.

The current stable release is `2.4.0`, which continues the ExcelAlchemy 2.x
line with a more complete import workflow: clearer template guidance before
upload, lightweight structural preflight before execution, synchronous
lifecycle visibility during import, and remediation-oriented payloads after
failures.

For the platform-layer architecture of that workflow, see:

- [`docs/platform-architecture.md`](docs/platform-architecture.md)
- [`docs/runtime-model.md`](docs/runtime-model.md)
- [`docs/integration-blueprints.md`](docs/integration-blueprints.md)

## At a Glance

- Build Excel templates directly from typed Pydantic schemas
- Guide users with workbook-facing input hints and examples
- Run lightweight structural preflight checks before full import
- Validate uploaded workbooks and write failures back to rows and cells
- Observe import lifecycle progress through additive callbacks
- Build remediation-oriented payloads for retry workflows
- Keep storage pluggable through `ExcelStorage`
- Render workbook-facing text in `zh-CN` or `en`
- Stay lightweight at runtime with `openpyxl` instead of pandas
- Protect behavior with contract tests, `ruff`, and `pyright`

## Screenshots

| Template | Import Result |
| --- | --- |
| ![Excel template screenshot](images/portfolio-template-en.png) | ![Excel import result screenshot](images/portfolio-import-result-en.png) |

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
template_data_url = template.as_data_url()  # compatibility path for older browser integrations
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
        ExcelMeta(
            label='Email',
            order=1,
            hint='Use your work email',
            example_value='alice@company.com',
        ),
    ]


alchemy = ExcelAlchemy(ImporterConfig(Importer, locale='en'))
template = alchemy.download_template_artifact(filename='people-template.xlsx')
```

This template metadata is additive: it keeps the worksheet layout unchanged and
adds clearer header comments for spreadsheet users, such as a free-form hint
and a concrete example value.

For browser downloads, prefer `template.as_bytes()` with a `Blob`, or return the bytes from your backend with
`Content-Disposition: attachment`. A top-level navigation to a long `data:` URL is less reliable in modern browsers.

## Import Workflow Overview

The shortest path through the import platform is:

```text
template -> preflight -> import -> remediation -> delivery
```

In practical backend terms:

- generate a template with workbook-facing guidance
- run `preflight_import(...)` to reject structurally invalid workbooks early
- run `import_data(..., on_event=...)` for the real import runtime
- build a remediation payload when the client needs retry-oriented guidance
- return or upload the result workbook artifact when the flow needs delivery

Minimal example:

```python
from excelalchemy.results import build_frontend_remediation_payload


events: list[dict[str, object]] = []

preflight = alchemy.preflight_import('employees.xlsx')
if preflight.is_valid:
    result = await alchemy.import_data(
        'employees.xlsx',
        'employees-result.xlsx',
        on_event=events.append,
    )
    payload = build_frontend_remediation_payload(
        result=result,
        cell_error_map=alchemy.cell_error_map,
        row_error_map=alchemy.row_error_map,
    )
```

If you want the full platform view behind this flow, see:

- [`docs/platform-architecture.md`](docs/platform-architecture.md)
- [`docs/runtime-model.md`](docs/runtime-model.md)
- [`docs/integration-blueprints.md`](docs/integration-blueprints.md)

## Import Workflow

ExcelAlchemy is designed to work as a product-ready import layer rather than
only a row-validation helper.

The top-level import workflow in the 2.x line is:

- template authoring
- preflight gate
- import runtime
- result intelligence
- artifact and delivery

In practical terms, that usually means:

- generate a template with workbook-facing guidance
- run `preflight_import(...)` as a lightweight structural gate
- run `import_data(..., on_event=...)` for full validation and execution
- inspect `ImportResult`, `CellErrorMap`, and `RowIssueMap`
- build remediation-oriented payloads if the import fails
- deliver template or result workbook artifacts through the configured storage seam

For the platform view and runtime sequence behind this workflow, see:

- [`docs/platform-architecture.md`](docs/platform-architecture.md)
- [`docs/runtime-model.md`](docs/runtime-model.md)
- [`docs/integration-blueprints.md`](docs/integration-blueprints.md)

Use `preflight_import(...)` when you want a fast answer to:

- does the configured sheet exist
- do the workbook headers match the schema
- is the workbook structurally importable

Use `import_data(...)` when you want the full workflow:

- row validation
- create / update callback execution
- result workbook rendering
- structured row and cell failure output

Short example:

```python
from pydantic import BaseModel

from excelalchemy import ExcelAlchemy, Email, FieldMeta, ImporterConfig, Number, String
from excelalchemy.results import build_frontend_remediation_payload


class EmployeeImporter(BaseModel):
    full_name: String = FieldMeta(label='Full name', order=1, hint='Use the legal name')
    age: Number = FieldMeta(label='Age', order=2)
    work_email: Email = FieldMeta(label='Work email', order=3, example_value='alice@company.com')


async def create_employee(row: dict[str, object], context: dict[str, object] | None) -> dict[str, object]:
    return row


alchemy = ExcelAlchemy(
    ImporterConfig.for_create(
        EmployeeImporter,
        creator=create_employee,
        storage=storage,
        locale='en',
    )
)

template = alchemy.download_template_artifact(filename='employee-template.xlsx')

preflight = alchemy.preflight_import('employees.xlsx')
if not preflight.is_valid:
    response = {'preflight': preflight.to_api_payload()}
else:
    events: list[dict[str, object]] = []
    result = await alchemy.import_data(
        'employees.xlsx',
        'employees-result.xlsx',
        on_event=events.append,
    )

    response = {
        'result': result.to_api_payload(),
        'events': events,
        'remediation': build_frontend_remediation_payload(
            result=result,
            cell_error_map=alchemy.cell_error_map,
            row_error_map=alchemy.row_error_map,
        ),
    }
```

This keeps one clear separation:

- template authoring and preflight help before execution
- import runtime handles real validation and persistence
- result intelligence helps API and frontend retry flows after failure
- artifact and delivery expose files and URLs after the run

## When To Use / When Not To Use / Limitations & Gotchas

### When To Use

- You want schema-driven Excel templates and imports in a Python backend.
- You want row-level and cell-level validation feedback tied to workbook coordinates.
- You want server-side workbook generation and processing without requiring Microsoft Excel on the host.
- You want a typed integration path built around Pydantic models and explicit storage boundaries.

### When Not To Use

- You need desktop Excel automation, live recalculation, or macro execution.
- You need a general spreadsheet analysis tool or a pandas-first data processing workflow.
- You need byte-for-byte preservation of an existing workbook as it moves through your system.
- You need UI-grade responsiveness for very large operational workbooks instead of batch-style backend processing.

### Limitations & Gotchas

- Formula cells are read through `openpyxl` using stored workbook values. ExcelAlchemy does not run Excel and does not recalculate formulas on the server.
- This is a server-side file-processing library, not a wrapper around a locally installed Excel application.
- Large workbook performance depends on workbook size, formula density, and validation workload. Treat large imports as backend jobs, not instant spreadsheet interactions.
- Exported or result workbooks should not be described as full-fidelity round trips of the original file. The library reads and renders the workbook data it needs for its own workflow.

| Scenario | Is ExcelAlchemy a good fit? |
| --- | --- |
| Backend upload validation and result workbook generation | Yes |
| Typed template generation from Pydantic models | Yes |
| Server-side processing in containers or Linux services | Yes |
| Desktop Excel automation or local Office integration | No |
| Exact workbook round-trip preservation for complex existing files | Usually no |

For concrete details and FAQ-style guidance, see
[`docs/limitations.md`](docs/limitations.md).
If you are evaluating large uploads, memory-sensitive services, or background
job thresholds, also see
[`docs/performance.md`](docs/performance.md).

## Choosing ExcelAlchemy

ExcelAlchemy is easiest to justify when you need typed schema modeling,
template generation, workbook-facing validation feedback, and clean backend/API
integration in the same workflow.

- Compare it to plain `openpyxl` when you are deciding between a reusable
  workflow library and one-off workbook scripting.
- Compare it to Excel automation tools when you need to separate server-side
  processing from desktop Excel behavior.
- Compare it to dataframe/schema-validation stacks when the question is
  “workbook contract and user feedback” versus “tabular ETL and validation.”

For the balanced decision guide and summary table, see
[`docs/tool-comparison.md`](docs/tool-comparison.md).

## Repository Scope

- A library for building Excel workflows from typed schemas.
- A reference implementation of “facade outside, focused components inside”.
- A portfolio project that emphasizes architecture, migration strategy, and maintainability.

## Non-Goals

- Not a general spreadsheet analysis library.
- Not a pandas-first data wrangling tool.
- Not a GUI spreadsheet editor.
- Not a fully generic forms framework.

## Why This Exists

Many internal systems still receive business data through Excel.
The painful part is rarely “reading a file”; it is keeping templates, validation rules, row-level error reporting, and backend integration consistent across projects.

ExcelAlchemy treats Excel as a typed contract:

- the model defines the shape
- field metadata defines the workbook experience
- import execution is separated from parsing
- storage is an interchangeable strategy, not a hard-coded implementation

## Architecture

ExcelAlchemy exposes a small public surface and delegates the real work to internal components.

```mermaid
flowchart TD
    A[ExcelAlchemy Facade]
    A --> B[ExcelSchemaLayout]
    A --> C[ExcelHeaderParser / Validator]
    A --> D[RowAggregator]
    A --> E[ImportExecutor]
    A --> F[ExcelRenderer / writer.py]
    A --> G[ExcelStorage Protocol]

    G --> H[MinioStorageGateway]
    G --> I[Custom Storage]

    B --> J[FieldMeta / FieldMetaInfo]
    E --> K[Pydantic Adapter]
    F --> L[i18n Display Messages]
    E --> M[Runtime Error Messages]
```

See the full breakdown in [docs/platform-code-mapping.md](docs/platform-code-mapping.md).
For the integration-oriented platform view layered above those components, see
[docs/platform-architecture.md](docs/platform-architecture.md),
[docs/runtime-model.md](docs/runtime-model.md), and
[docs/integration-blueprints.md](docs/integration-blueprints.md).

## Workflow

```mermaid
flowchart LR
    A[Pydantic model + FieldMeta] --> B[ExcelAlchemy facade]
    B --> C[Template rendering]
    B --> D[Worksheet parsing]
    D --> E[Header validation]
    D --> F[Row aggregation]
    F --> G[Import executor]
    G --> H[Import result workbook]
    C --> I[Workbook for users]
    H --> I
```

## Design Principles

This repository is guided by explicit design principles rather than accidental convenience.
The full mapping is in [ABOUT.md](ABOUT.md); the short version is:

1. Schema first.
2. Explicit metadata over implicit conventions.
3. Composition over monoliths.
4. Adapters at integration boundaries.
5. Protocols over concrete backends.
6. Progressive modernization over one-shot rewrites.
7. Runtime simplicity over hidden magic.
8. User-facing clarity over clever internals.
9. Tests should protect behavior, not implementation accidents.
10. Migration-friendly seams are part of the design.

## Quick Start

### Install

```bash
pip install ExcelAlchemy
```

If you want the built-in Minio backend:

```bash
pip install "ExcelAlchemy[minio]"
```

## Examples

Practical examples live in the repository:

- [`examples/annotated_schema.py`](examples/annotated_schema.py)
- [`examples/employee_import_workflow.py`](examples/employee_import_workflow.py)
- [`examples/create_or_update_import.py`](examples/create_or_update_import.py)
- [`examples/date_and_range_fields.py`](examples/date_and_range_fields.py)
- [`examples/selection_fields.py`](examples/selection_fields.py)
- [`examples/custom_storage.py`](examples/custom_storage.py)
- [`examples/export_workflow.py`](examples/export_workflow.py)
- [`examples/minio_storage.py`](examples/minio_storage.py)
- [`examples/fastapi_upload.py`](examples/fastapi_upload.py)
- [`examples/fastapi_reference/README.md`](examples/fastapi_reference/README.md)
- [`examples/README.md`](examples/README.md)

If you want the recommended reading order, start with
[`examples/README.md`](examples/README.md).

If you want a single page that combines screenshots, representative workflows,
and captured outputs, see
[`docs/examples-showcase.md`](docs/examples-showcase.md).

Selected fixed outputs from the examples are generated by
[`scripts/generate_example_output_assets.py`](scripts/generate_example_output_assets.py).

### Example Outputs

Import workflow output:

```text
Employee import workflow completed
Preflight: VALID
Result: SUCCESS
Success rows: 1
Failed rows: 0
Result workbook URL: None
Created rows: 1
Uploaded artifacts: []
```

Export workflow output:

```text
Export workflow completed
Artifact filename: employees-export.xlsx
Artifact bytes: 6893
Upload URL: memory://employees-export-upload.xlsx
Uploaded objects: ['employees-export-upload.xlsx']
```

Full captured outputs:

- [`files/example-outputs/employee-import-workflow.txt`](files/example-outputs/employee-import-workflow.txt)
- [`files/example-outputs/create-or-update-import.txt`](files/example-outputs/create-or-update-import.txt)
- [`files/example-outputs/export-workflow.txt`](files/example-outputs/export-workflow.txt)
- [`files/example-outputs/date-and-range-fields.txt`](files/example-outputs/date-and-range-fields.txt)
- [`files/example-outputs/selection-fields.txt`](files/example-outputs/selection-fields.txt)
- [`files/example-outputs/custom-storage.txt`](files/example-outputs/custom-storage.txt)
- [`files/example-outputs/annotated-schema.txt`](files/example-outputs/annotated-schema.txt)
- [`files/example-outputs/fastapi-reference.txt`](files/example-outputs/fastapi-reference.txt)

## Public API Boundaries

If you want to know which modules are stable public entry points versus
compatibility shims or internal modules, see
[`docs/public-api.md`](docs/public-api.md).

## Import Inspection Names

When you inspect import-run state from the facade, prefer the clearer 2.2 names:

- `alchemy.worksheet_table`
- `alchemy.header_table`
- `alchemy.cell_error_map`
- `alchemy.row_error_map`

The older aliases:

- `alchemy.df`
- `alchemy.header_df`
- `alchemy.cell_errors`
- `alchemy.row_errors`

still work in the 2.x line as compatibility paths, but new application code
should use the clearer names above.

## Structured Error Access

Import failures are now easier to inspect programmatically.

- `alchemy.cell_error_map`
- `alchemy.row_error_map`

Both containers remain dict-like for 2.x compatibility, but they also expose
clearer helper methods for application code and API handlers:

- `at(...)`
- `messages_at(...)`
- `messages_for_row(...)`
- `numbered_messages_for_row(...)`
- `flatten()`
- `to_dict()`
- `to_api_payload()`

This makes it easier to:

- build frontend-friendly validation responses
- render row-level and cell-level failure summaries
- keep workbook feedback and API feedback aligned

Common field types also provide more business-oriented validation wording. For
example:

- date fields now mention the expected date format
- date range and number range fields now mention the expected combined input
- email, phone number, and URL fields now include example formats
- selection, organization, and staff fields now mention that values must come
  from the configured options

## Locale-Aware Workbook Output

`locale` affects workbook-facing display text such as:

- header hint text
- column comments
- result workbook column titles
- row validation status labels

The public locale policy is documented in [docs/locale.md](docs/locale.md).
In short:

- runtime exceptions are standardized in English
- workbook display locales currently support `zh-CN` and `en`
- workbook display defaults to `zh-CN` for the 2.x line

```python
from excelalchemy import ExcelAlchemy, FieldMeta, ImporterConfig, Number, String
from pydantic import BaseModel


class Importer(BaseModel):
    age: Number = FieldMeta(label='Age', order=1)
    name: String = FieldMeta(label='Name', order=2)


zh_template = ExcelAlchemy(ImporterConfig(Importer, locale='zh-CN')).download_template_artifact()
en_template = ExcelAlchemy(ImporterConfig(Importer, locale='en')).download_template_artifact()
```

The same `locale` also controls import result workbooks:

```python
alchemy = ExcelAlchemy(
    ImporterConfig(
        Importer,
        creator=create_func,
        storage=storage,
        locale='en',
    )
)
result = await alchemy.import_data("people.xlsx", "people-result.xlsx")
```

## Storage Protocol

Storage is modeled as a protocol, not a product decision.

```python
from excelalchemy import ExcelAlchemy, ExcelStorage, ExporterConfig, UrlStr
from excelalchemy.core.table import WorksheetTable


class InMemoryExcelStorage(ExcelStorage):
    def read_excel_table(self, input_excel_name: str, *, skiprows: int, sheet_name: str) -> WorksheetTable:
        ...

    def upload_excel(self, output_name: str, content_with_prefix: str) -> UrlStr:
        ...


alchemy = ExcelAlchemy(ExporterConfig(Importer, storage=InMemoryExcelStorage()))
```

Use the built-in Minio implementation when you want it, but the library no longer requires Minio to define its architecture.

## Why These Design Choices

### Why no pandas?

ExcelAlchemy uses `openpyxl` plus an internal `WorksheetTable` abstraction.
`WorksheetTable` is intentionally narrow and only models the operations the core
workflow needs; it is not a pandas-compatible public table layer.
The project was not using pandas for analysis, joins, or vectorized computation; it was mostly using it as a transport layer.
Removing pandas:

- simplified installation
- removed the `numpy` dependency chain
- made behavior more explicit
- better aligned the code with the actual problem domain

### Why a Pydantic adapter layer?

The project used to lean on Pydantic internals more directly.
That becomes fragile during major-version upgrades.
Now the design is:

- `FieldMeta` owns Excel metadata
- the Pydantic adapter reads model structure
- the adapter does not own the domain semantics

This is what made the Pydantic v2 migration practical without rewriting the public API.

### Why a facade?

The public object should stay small.
The internal object graph can evolve.
`ExcelAlchemy` is the facade; parsing, rendering, execution, storage, and schema layout are delegated to separate collaborators.

### Why a storage protocol?

Excel workflows should not be locked to Minio, S3, or any one persistence strategy.
`ExcelStorage` keeps the boundary stable while allowing object storage, local filesystem adapters, in-memory test doubles,
and custom infrastructure integrations to share the same import/export contract.

## Evolution

This repository intentionally records its evolution:

- `src/` layout migration
- CI and release modernization
- Pydantic metadata decoupling
- Pydantic v2 migration
- Python 3.12-3.14 modernization
- internal architecture split
- pandas removal
- storage abstraction
- i18n foundation and locale-aware workbook text

These are not incidental refactors; they are the story of the codebase.
See [ABOUT.md](ABOUT.md) for the migration rationale behind each step.

## Pydantic v1 vs v2

The short version:

| Topic | v1-style risk | Current v2 design |
| --- | --- | --- |
| Field access | Tight coupling to `__fields__` / `ModelField` | Adapter over `model_fields` |
| Metadata ownership | Excel metadata mixed with validation internals | `FieldMetaInfo` is a compatibility facade over layered Excel metadata |
| Validation integration | Deep reliance on internals | Adapter + explicit runtime validation |
| Upgrade path | Brittle | Layered |

More detail is documented in [ABOUT.md](ABOUT.md).

## Docs Map

- [README.md](README.md): product + design overview
- [README_cn.md](README_cn.md): Chinese usage-oriented guide
- [ABOUT.md](ABOUT.md): engineering rationale and evolution notes
- [docs/platform-architecture.md](docs/platform-architecture.md): import platform capability model
- [docs/runtime-model.md](docs/runtime-model.md): runtime sequence across the import workflow
- [docs/integration-blueprints.md](docs/integration-blueprints.md): backend/frontend integration patterns
- [docs/platform-code-mapping.md](docs/platform-code-mapping.md): component map and boundaries
- [docs/limitations.md](docs/limitations.md): practical fit, limitations, and gotchas
- [docs/performance.md](docs/performance.md): operational guidance for large files, memory, and backend guardrails
- [docs/tool-comparison.md](docs/tool-comparison.md): when ExcelAlchemy fits better than scripting, automation, or dataframe-first approaches

## Development

The project uses `uv` for local development and CI.

```bash
uv sync --extra development
uv run pre-commit install
uv run ruff check .
uv run pyright
uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests
uv build
```

## License

MIT. See [LICENSE](LICENSE).
