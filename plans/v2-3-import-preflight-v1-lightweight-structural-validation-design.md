# v2.3 Import Preflight v1: Lightweight Structural Validation

Status: `planned`

## Problem

`ExcelAlchemy` currently has one import-oriented runtime path:

- `ExcelAlchemy.import_data(...)`
- `ImportSession.run(...)`

That path assumes:

- storage-backed workbook loading
- async execution
- row-level validation and create/update callbacks
- optional result-workbook rendering and upload

Users who only want to answer "is this workbook structurally importable?" must
still enter the full import shape or build ad hoc checks around internal
components. That is too heavy for API upload guards and pre-submit validation.

The gap is especially clear for these checks:

- does the configured sheet exist
- do the workbook headers match the schema
- is the workbook structurally usable for import
- roughly how many data rows would the import process

## Goals

- Add a lightweight preflight workflow that validates an import workbook before
  full import execution.
- Keep the workflow additive and clearly separate from `import_data(...)`.
- Reuse existing header parsing and header validation behavior.
- Reuse the existing storage-backed workbook input seam so callers do not need
  to materialize raw workbook bytes themselves.
- Support:
  - sheet existence checks
  - header validation
  - basic workbook structure checks
  - row count estimation
- Return a lightweight public result object suitable for API and service-layer
  decisions.
- Avoid new storage surface area, result-workbook rendering, row execution, and
  callback invocation.

## Non-goals

- No full import execution.
- No row-level validation or callback dispatch.
- No async API for v1.
- No job system, lifecycle events, or progress streaming.
- No new storage abstraction, storage-specific public API, or upload behavior.
- No template changes.
- No remediation payload integration.
- No attempt to infer deep workbook quality beyond structural importability.

## API Options

### Option A: Add `preflight_only=` to `import_data(...)`

Example:

```python
result = await alchemy.import_data(
    input_excel_name,
    output_excel_name,
    preflight_only=True,
)
```

Reject this option.

Reasons:

- it mixes a lightweight structural check into the full import API
- it still implies storage-backed input names and output names
- it keeps preflight async for no real benefit
- it invites branching inside `ImportSession.run(...)` and increases coupling

### Option B: Reuse `ValidateHeaderResult` as the public result

Example:

```python
header_result = alchemy.preflight_import(input_excel_name)
```

Reject this option.

Reasons:

- `ValidateHeaderResult` only models header issues
- it cannot represent sheet-missing or structure-invalid outcomes cleanly
- it has no place for row count estimation
- stretching it would blur the difference between header validation and
  workbook preflight

### Option C: Add a new synchronous preflight method and result type

Example:

```python
result = alchemy.preflight_import(input_excel_name)
```

Recommend this option.

Reasons:

- additive public surface
- aligns with the existing facade input seam
- no async requirement
- clear separation from full import semantics
- enough room for sheet, structure, header, and row-count fields without
  overloading `ImportResult` or `ValidateHeaderResult`

## Recommended Design

### Public API

Add one new synchronous facade method:

```python
def preflight_import(self, input_excel_name: str) -> ImportPreflightResult:
    ...
```

Keep the first version intentionally narrow:

- input is an existing workbook name resolved through configured `ExcelStorage`
- the configured schema sheet name remains the lookup target
- no output workbook name
- no async variant in v1

### Public Result Shape

Add a lightweight public result model and status enum in
`src/excelalchemy/results.py`.

Recommended names:

- `ImportPreflightStatus`
- `ImportPreflightResult`

Recommended status values:

- `VALID`
- `HEADER_INVALID`
- `SHEET_MISSING`
- `STRUCTURE_INVALID`

Recommended result responsibilities:

- report whether preflight passed
- expose the configured sheet name and whether it was found
- expose header issues using the same field groups already used by
  `ValidateHeaderResult` / `ImportResult`
- expose `has_merged_header` when header rows were readable
- expose `estimated_row_count`
- expose a small, stable list of structural issue codes for non-header failures

The result should stay lightweight:

- no `url`
- no `success_count` / `fail_count`
- no row-error maps
- no cell-error maps
- no remediation hints

### Internal Design

Do not route preflight through `ImportSession.run(...)`.

Instead, add a small dedicated internal path that reuses existing logic where it
already exists:

- reuse `ExcelSchemaLayout`
- reuse `ExcelHeaderParser`
- reuse `ExcelHeaderValidator`
- reuse `WorksheetTable`
- reuse configured `ExcelStorage` for workbook reads only

Recommended shape:

- add a new internal helper or session-like object dedicated to preflight
- use the existing storage gateway read path to obtain `WorksheetTable`
- keep row-count estimation in the preflight path, not in `ImportSession`

Clarification for the original "no storage" constraint:

- preflight should not introduce a new storage API
- preflight should not upload or write artifacts
- preflight may still read the input workbook through configured `ExcelStorage`,
  because that is already the repository's import input boundary

### Structure Checks In Scope For v1

Keep "basic structure checks" small and explicit:

- configured sheet exists
- storage can read the configured workbook into `WorksheetTable`
- enough rows exist to inspect the header block
- the header block is readable for simple or merged-header detection

Do not add deeper checks such as:

- per-row value validation
- field codec parsing across data rows
- business-rule execution
- workbook repair suggestions

### Row Count Estimation

The estimate should align with current import semantics instead of inventing a
new counting rule.

Recommended rule:

- read the worksheet through the configured storage gateway into
  `WorksheetTable`
- detect merged vs simple headers with `ExcelHeaderParser`
- estimate data rows from the same header-offset logic the import session uses

Target invariant:

- for a workbook that later runs through `import_data(...)`, preflight
  `estimated_row_count` should match `last_import_snapshot.data_row_count`
  unless later implementation intentionally documents an edge-case difference

### Duplication And Reuse Direction

Prefer reusing the existing storage read seam and current header components
rather than introducing a raw-bytes API or a generic shared import engine.

Do not duplicate header parsing or validation logic in the facade.

Do not over-abstract the shared logic either.

Recommended boundary:

- storage gateway is responsible for reading `WorksheetTable`
- preflight path is responsible for structural decisions
- `ExcelHeaderParser` and `ExcelHeaderValidator` stay responsible for header
  semantics
- `ImportSession` remains responsible for full import execution only

## Affected Modules

Likely source changes:

- `src/excelalchemy/core/alchemy.py`
- `src/excelalchemy/results.py`
- `src/excelalchemy/__init__.py`
- one new internal module for preflight orchestration under
  `src/excelalchemy/core/`, if that keeps `alchemy.py` and `import_session.py`
  clean
- possibly `src/excelalchemy/core/headers.py` for small reuse-oriented helpers

Likely documentation changes:

- `docs/public-api.md`
- `docs/result-objects.md`
- `docs/domain-model.md`
- `docs/architecture.md`
- `README.md` if the preflight workflow becomes part of the main onboarding
  story

Likely examples:

- `examples/employee_import_workflow.py` or a new focused example
- `examples/fastapi_reference/` if the feature is presented as an upload guard

Likely test updates:

- `tests/contracts/test_import_contract.py`
- `tests/contracts/test_result_contract.py`
- one new unit-focused test module for preflight internals if needed
- example smoke tests if examples are updated

## Test Strategy

Contract tests should define the public behavior:

- valid workbook returns `VALID`
- missing target sheet returns `SHEET_MISSING`
- unreadable or structurally unusable workbook returns `STRUCTURE_INVALID`
- invalid headers return `HEADER_INVALID`
- header issue lists preserve current ordering semantics
- `estimated_row_count` matches current import counting rules for simple and
  merged headers
- no row-level execution side effects occur

Unit tests should focus on isolated mechanics:

- simple vs merged header detection under preflight
- structural issue classification
- row count estimation against existing import semantics

Integration and smoke coverage should stay light:

- add or update one example only if the public story is changed
- avoid broad smoke churn unless docs/examples are intentionally expanded

## Risks

### Duplicate structural logic

Risk:

- preflight could accidentally duplicate header handling or row-count rules from
  `ImportSession`

Mitigation:

- reuse `ExcelHeaderParser` and `ExcelHeaderValidator` directly
- reuse the existing storage read seam instead of introducing a second input
  mechanism
- extract only small focused helpers if duplication appears in count logic or
  result mapping

### Coupling preflight to the full import session

Risk:

- branching inside `ImportSession.run(...)` would mix sync preflight with async
  import execution and increase maintenance burden

Mitigation:

- keep preflight as a dedicated path with targeted reuse of header and layout
  helpers

### Result-type overlap

Risk:

- `ImportResult`, `ValidateHeaderResult`, and a new preflight result can become
  confusing if their responsibilities overlap

Mitigation:

- document the distinction clearly:
  - `ValidateHeaderResult` = header-only internal/public helper result
  - `ImportResult` = full import outcome
  - `ImportPreflightResult` = lightweight structural importability result

### Count drift

Risk:

- preflight row-count estimation could silently diverge from import-session row
  counting, especially for merged headers

Mitigation:

- define tests that compare both paths on the same fixtures
- derive the estimate from the same header-offset rules already used in import

## Phased Steps

1. Define the public API and result-model contract.
2. Implement a dedicated read-only preflight path that uses the configured
   storage gateway and reuses header parser and header
   validator logic.
3. Add contract tests for statuses, header issue mapping, and row-count
   estimation.
4. Update docs for the new public entry point and result object.
5. Add or update one example only if it improves the public workflow story.

## Acceptance Criteria

- The library exposes a new additive synchronous preflight entry point.
- Preflight accepts `input_excel_name` and reads through configured
  `ExcelStorage`.
- Preflight does not execute create/update callbacks.
- Preflight does not produce result workbooks or upload anything.
- Preflight reports:
  - sheet existence
  - header validity
  - basic structural validity
  - estimated row count
- Header issue lists remain consistent with existing header validation behavior.
- The result type is documented as a stable public surface.
- Existing full-import APIs and result payloads remain unchanged.

## Verification

When implementation starts, run:

- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pyright`
- `uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests`
- `uv run python scripts/smoke_package.py`
- `uv run python scripts/smoke_examples.py`
