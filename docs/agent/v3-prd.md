# ExcelAlchemy 3.0 PRD For Codex

## Status

`in_progress`

## Scope Authority

The current mainline is ExcelAlchemy 3.0. This document is the agent-facing
product and execution source of truth for current mainline work.

ExcelAlchemy 3.0 is allowed to break compatibility. Do not preserve 2.x
compatibility imports, aliases, deprecation warnings, or legacy configuration
paths unless a 3.0 task explicitly reintroduces them as current API.

Only follow 2.x compatibility rules when a task explicitly targets a 2.x
maintenance line.

## Product Goal

ExcelAlchemy 3.0 should become a typed, schema-driven Excel import/export
library whose public API is small, annotation-driven, and explicit enough for
both Python tooling and Codex agents to reason about without hidden rules.

The 3.0 design should follow public patterns used by strong Python libraries:

- Pydantic 2: type annotations define the Python data shape; metadata is
  attached through `Annotated` when static typing should stay visible.
  Reference: <https://docs.pydantic.dev/latest/concepts/fields/>
- FastAPI: ordinary Pydantic models define runtime contracts and generated
  external schemas instead of hand-written dictionaries.
  Reference: <https://fastapi.tiangolo.com/tutorial/body/>
- SQLAlchemy 2: declarative configuration is annotation-driven and provides
  explicit helper objects for runtime behavior.
  Reference: <https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html>

## Non-Goals

- Do not keep 2.x compatibility shims.
- Do not preserve deprecated import paths.
- Do not add broad catch-all package names such as `_internal`.
- Do not keep current docs merely because they existed in 2.x.
- Do not make large source rewrites before contract tests describe the 3.0 API.
- Do not create a separate documentation site workflow unless a future task
  explicitly asks for it.

## Target Public API

The 3.0 public surface should be intentionally small:

- `excelalchemy`
- `excelalchemy.config`
- `excelalchemy.columns`
- `excelalchemy.codecs`
- `excelalchemy.storage`
- `excelalchemy.results`
- `excelalchemy.errors`
- `excelalchemy.artifacts`

Preferred field declaration:

```python
from typing import Annotated

from pydantic import BaseModel, Field

from excelalchemy import ExcelAlchemy, ExcelColumn, ImportConfig
from excelalchemy.codecs import DateCodec, NumberCodec


class EmployeeImport(BaseModel):
    name: Annotated[str, ExcelColumn(label='Name', required=True, order=1)]
    joined_at: Annotated[int | None, ExcelColumn(label='Joined At', codec=DateCodec.day(), order=2)]
    salary: Annotated[
        float | None,
        Field(ge=0),
        ExcelColumn(label='Salary', codec=NumberCodec(fraction_digits=2), order=3),
    ]
```

Rules:

- Python type annotations remain the data contract.
- `ExcelColumn(...)` supplies Excel-specific metadata only.
- Pydantic `Field(...)` remains the place for Pydantic validation metadata.
- Codecs are explicit helper objects or immutable config objects, not fake
  Python scalar types.
- Requiredness comes from Pydantic unless `ExcelColumn(required=...)` explicitly
  overrides workbook-facing behavior.

## Codec Naming And Structure

3.0 codec names must describe Excel import/export semantics, not UI widgets or
legacy value-type shims.

Rules:

- User-facing codec helpers use `*Codec` names and return immutable
  `ExcelFieldCodecSpec` objects for `ExcelColumn(codec=...)`.
- Internal codec implementations use `*FieldCodec` names and implement
  `ExcelFieldCodec`.
- File names use data semantics. Do not use frontend-control names such as
  `radio` or `checkbox`.
- Text fields use `TextCodec`; Python `str` remains the type annotation and is
  not duplicated in the codec name.
- Choice fields use `SingleChoiceCodec` and `MultiChoiceCodec`. Entity-specific
  behavior such as organization, staff, or tree-node hints must be explicit
  helper parameters, not separate wrapper codec classes.
- Fixed-parameter wrappers such as a money codec are not separate public codecs.
  Use `NumberCodec(fraction_digits=2, unit=...)` or another explicit number
  helper parameter instead.
- Multi-choice separators must be explicit configuration shared by comments,
  parsing, and formatting. Do not let workbook comments and parser behavior
  diverge.
- Compatibility names such as `ValueType`, `StringCodec`, `ExcelCodecConfig`,
  `EXCEL_CHOICE_CODECS`, and `excel_choice_codec` are not valid public 3.0 API
  names.

## Target Module Map

Do not introduce `_internal`. Name modules by concrete responsibility.

Suggested target layout:

```text
src/excelalchemy/
  __init__.py
  config/
  columns.py
  codecs/
  storage/
  results/
  errors.py
  field_metadata/
  schema/
  worksheet/
  runtime/
  rendering/
  adapters/
  policies.py
  messages.py
  diagnostics.py
```

Responsibilities:

- `columns.py`: `ExcelColumn` declarations for `Annotated`.
- `codecs/`: Excel parse, normalize, format, and header-comment behavior.
- `storage/`: `ExcelStorage` protocol and storage helpers.
- `results/`: result, issue-map, remediation, preflight, and event models.
- `errors.py`: public exceptions.
- `field_metadata/`: resolved Excel-facing field declaration, presentation,
  and runtime metadata.
- `schema/`: Pydantic model inspection and Excel schema layout.
- `worksheet/`: worksheet table abstraction, normalized header records, header
  parsing, and header validation.
- `runtime/`: import sessions, row aggregation, execution, lifecycle events.
- `rendering/`: workbook rendering and writer code.
- `adapters/`: explicit framework boundaries, starting with Pydantic.
- `policies.py`: deterministic policy constants and policy objects.
- `messages.py`: runtime and workbook-facing message lookup.
- `diagnostics.py`: logging names and structured diagnostics helpers.

## Required 3.0 Deletions

Remove these 2.x compatibility surfaces:

- `src/excelalchemy/types/`
- `src/excelalchemy/exc.py`
- `src/excelalchemy/identity.py`
- `src/excelalchemy/header_models.py`
- `src/excelalchemy/const.py` if it only exists as compatibility surface
- `src/excelalchemy/util/convertor.py`
- facade aliases `df`, `header_df`, `cell_errors`, `row_errors`
- legacy config fields `minio`, `bucket_name`, `url_expires`
- deprecation-warning tests that only protect 2.x compatibility

Replacement rule:

- Replace old names with current 3.0 names in tests, examples, docs, and smoke
  expectations in the same task that removes each compatibility surface.

## Hidden Rules To Make Explicit

Move these out of scattered implementation assumptions and into named models,
policies, or tests:

- workbook header hint row count
- simple header row count
- merged header row count
- result and reason column identity and ordering
- workbook unique-label separator
- payload path separator
- missing-value policy by import mode
- header-invalid imports do not upload a result workbook
- data-invalid imports upload a result workbook and return a URL
- codec parse fallback behavior
- codec render fallback behavior
- event callback failure behavior
- Pydantic validation-message normalization rules
- locale fallback behavior
- storage upload payload must be binary `.xlsx` bytes

## Documentation Policy For 3.0

Current docs must describe the 3.0 line unless they are clearly marked as
history, release notes, or migration material. A 3.0 task must not leave stale
2.x guidance in current docs.

Docs to rewrite or replace:

- `README.md`
- `README-pypi.md`
- `README_cn.md`
- `docs/about.md`
- `docs/getting-started.md`
- `docs/migrations.md`
- `docs/public-api.md`
- `docs/domain-model.md`
- `docs/runtime-model.md`
- `docs/platform-architecture.md`
- `docs/platform-code-mapping.md`
- `docs/result-objects.md`
- `docs/api-response-cookbook.md`
- `docs/integration-blueprints.md`
- `docs/integration-roadmap.md`
- `docs/locale.md`
- `docs/limitations.md`
- `docs/performance.md`
- `docs/repo-map.md`
- `src/excelalchemy/README.md`
- `tests/README.md`
- `examples/README.md`

Docs to delete when they become obsolete:

- 2.x-only maintenance notes under `docs/tech-debt/` after their code debt is
  removed
- generated example-output snapshots that describe removed 2.x APIs, after
  regenerating replacements

Docs to keep as history:

- `docs/history/`
- `docs/releases/`
- historical ADRs that explain why 2.x looked the way it did

Rule:

- Do not archive stale current docs just to avoid deleting them. Rewrite,
  merge, or delete them based on whether they are still useful for 3.0.

## Task Dependency Graph

Agents must treat the task graph as ordered. Do not start a task until every
listed dependency is complete and validated.

| ID | Task | Depends On | Required Output |
| --- | --- | --- | --- |
| T0 | Establish 3.0 agent rules | none | Agent docs state that 3.0 has no compatibility obligation |
| T1 | Write 3.0 public API contract tests | T0 | Failing or skipped contract tests for the intended API |
| T2 | Replace field declaration model | T1 | `ExcelColumn` plus extraction through `Annotated` |
| T3 | Redesign codecs as explicit helpers | T2 | Codecs no longer masquerade as Python scalar/container types |
| T4 | Extract policies and typed events | T1 | Policy objects/constants and event models replace implicit dicts |
| T5 | Reshape package modules | T2, T3, T4 | Concrete-responsibility modules replace compatibility/internal names |
| T6 | Remove compatibility surfaces | T5 | Old imports, aliases, config paths, and deprecation tests removed |
| T7 | Update runtime/import/export behavior | T3, T4, T6 | Import/export flows pass 3.0 contracts |
| T8 | Update storage API | T6, T7 | `storage=...` only; upload/read contracts typed and tested |
| T9 | Rewrite result and remediation payloads | T4, T7 | Public payloads modeled, typed, and covered by contract tests |
| T10 | Rewrite examples and generated outputs | T7, T8, T9 | Examples use only 3.0 API; snapshots regenerated |
| T11 | Rewrite, merge, or delete stale docs | T10 | Current docs describe only 3.0; obsolete 2.x docs removed |
| T12 | Full validation and release readiness | T11 | Full validation stack passes; residual risks listed |

## Task Specifications

### T0: Establish 3.0 Agent Rules

Scope:

- `AGENTS.md`
- `docs/agent/*`

Actions:

- Add explicit 3.0 override language for compatibility rules.
- Make it clear that 3.0 compatibility removal is intentional, not casual.

Validation:

- `uv run ruff format --check .`
- `uv run ruff check .`

### T1: Write 3.0 Public API Contract Tests

Scope:

- `tests/contracts/`
- `tests/support/`

Actions:

- Write tests for `ExcelColumn` declaration through `Annotated`.
- Write tests for explicit codec helpers.
- Write tests for public imports only from the target public surface.
- Write tests proving old compatibility imports are gone.
- Mark tests with clear expected-failure strategy only if the repository uses
  that pattern; otherwise commit them with implementation in the same PR.

Validation:

- Targeted contract tests.
- `uv run pyright` after enough implementation exists.

### T2: Replace Field Declaration Model

Scope:

- `src/excelalchemy/columns.py`
- `src/excelalchemy/field_metadata/` or its 3.0 replacement
- `src/excelalchemy/adapters/pydantic.py`
- tests near schema extraction

Actions:

- Introduce immutable column metadata.
- Make `Annotated[T, ExcelColumn(...)]` the only recommended declaration path.
- Remove `FieldMeta(...)` as a Pydantic `Field(...)` compatibility wrapper.
- Keep Pydantic `Field(...)` metadata in Pydantic's domain.

Validation:

- Metadata and Pydantic contract tests.
- `uv run pyright`.

### T3: Redesign Codecs As Explicit Helpers

Scope:

- `src/excelalchemy/codecs/`
- `tests/unit/codecs/`
- schema extraction tests

Actions:

- Replace scalar inheritance such as `Number(Decimal, ExcelFieldCodec)` with
  codec helper classes or frozen config objects.
- Keep codec responsibilities: comment, parse, normalize, format.
- Make codec fallback behavior explicit and tested.
- Keep composite-codec column expansion deterministic.

Validation:

- All codec unit tests.
- Relevant contract tests for composite fields.

### T4: Extract Policies And Typed Events

Scope:

- `src/excelalchemy/policies.py`
- `src/excelalchemy/results/`
- `src/excelalchemy/runtime/`
- import event tests

Actions:

- Create named policy constants for header rows, separators, result columns,
  locale defaults, and missing-value behavior.
- Replace event callback payload dictionaries with typed event models.
- Keep callback execution synchronous and best-effort unless a task explicitly
  changes the runtime model.

Validation:

- Import event contract tests.
- Result payload tests.

### T5: Reshape Package Modules

Scope:

- `src/excelalchemy/`
- package README
- repo map docs when docs are updated

Actions:

- Move code into concrete-responsibility modules.
- Do not create `_internal`.
- Remove vague package names when a domain name is available.
- Keep public re-exports narrow and intentional in `src/excelalchemy/__init__.py`.

Validation:

- Import contract tests.
- `uv run pyright`.
- `uv run ruff check .`.

### T6: Remove Compatibility Surfaces

Scope:

- compatibility modules and tests
- public API docs
- examples

Actions:

- Delete compatibility packages and modules listed in "Required 3.0 Deletions".
- Remove deprecation warning helpers if no longer used by current 3.0 APIs.
- Update or delete tests that only protect compatibility.
- Replace old names everywhere in current docs and examples.

Validation:

- `uv run ruff check .`
- `uv run pyright`
- targeted import/deletion tests.

### T7: Update Runtime Import And Export Behavior

Scope:

- `src/excelalchemy/runtime/`
- `src/excelalchemy/schema/`
- `src/excelalchemy/worksheet/`
- integration and contract tests

Actions:

- Make import sessions consume the 3.0 schema layout.
- Remove pandas-style vocabulary from runtime APIs.
- Preserve intentional behavior for header-invalid, data-invalid, and success
  outcomes unless a 3.0 contract changes it.
- Replace `assert` runtime checks with explicit exceptions.

Validation:

- Import and export contract tests.
- Integration workflow tests.

### T8: Update Storage API

Scope:

- `src/excelalchemy/storage/`
- storage examples
- storage contract tests

Actions:

- Keep `ExcelStorage` as the only storage extension boundary.
- Remove legacy Minio config fields.
- Keep Minio support only as an explicit storage implementation if retained.
- Ensure upload payloads are binary workbook bytes, not data URLs.

Validation:

- Storage contract tests.
- Package smoke if public imports changed.

### T9: Rewrite Result And Remediation Payloads

Scope:

- `src/excelalchemy/results/`
- `docs/result-objects.md`
- `docs/api-response-cookbook.md`
- result contract tests

Actions:

- Use typed models for public result, issue, event, and remediation payloads.
- Keep `model_dump()` as the serialization boundary.
- Remove hand-written untyped payload conventions where practical.

Validation:

- Result contract tests.
- API payload snapshot smoke after generated snapshots are updated.

### T10: Rewrite Examples And Generated Outputs

Scope:

- `examples/`
- `docs/assets/example-outputs/`
- `scripts/generate_example_output_assets.py`
- `scripts/smoke_examples.py`

Actions:

- Rewrite examples to use 3.0 imports and declarations only.
- Delete examples that exist only to explain 2.x compatibility.
- Regenerate captured example outputs.

Validation:

- `uv run python scripts/generate_example_output_assets.py`
- `uv run python scripts/smoke_examples.py`
- `uv run pytest tests/integration/test_examples_smoke.py`

### T11: Rewrite, Merge, Or Delete Stale Docs

Scope:

- all current docs listed in "Documentation Policy For 3.0"
- generated docs assets

Actions:

- Replace 2.x API guidance with 3.0 guidance.
- Delete docs that are no longer true and not worth rewriting.
- Merge overlapping platform docs into fewer current docs when possible.
- Keep current docs short enough for Codex to use; move historical context only
  when it belongs in existing history areas.

Validation:

- `uv run python scripts/smoke_docs_assets.py`
- `uv run python scripts/smoke_api_payload_snapshot.py`

### T12: Full Validation And Release Readiness

Scope:

- entire repository

Actions:

- Run full validation.
- Review public imports, package metadata, examples, docs, and generated assets.
- Record any remaining 3.0 release blockers in a current plan or tech-debt doc.

Validation:

```bash
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests
uv run python scripts/smoke_package.py
uv run python scripts/smoke_examples.py
uv run python scripts/smoke_docs_assets.py
uv run python scripts/smoke_api_payload_snapshot.py
```

## Codex Execution Rules

- Start every 3.0 implementation turn by reading this PRD and the affected
  current source/tests.
- If an older doc conflicts with this PRD, follow this PRD for 3.0 tasks.
- Prefer contract tests before large implementation changes.
- Keep each PR task-bounded; do not attempt the entire 3.0 migration in one
  patch.
- Do not leave current docs describing removed APIs.
- Do not introduce a compatibility shim to make old tests pass.
- Do not preserve old import paths by re-exporting from new modules.
- Do not use `_internal`; choose concrete package names from the target module
  map or add a more precise name.
- Do not change historical docs except to fix links broken by an intentional
  file move or deletion.
- When deleting docs, verify that no current docs or README files link to the
  deleted path.
