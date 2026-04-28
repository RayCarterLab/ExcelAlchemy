# v2.3 Front-end Remediation Payload v1 Design Note

Status: `planned`

Related plan:

- [v2-3-front-end-remediation-payload-v1.md](./v2-3-front-end-remediation-payload-v1.md)

## Current Repository State

The current repository already has a stable public result surface and strong verification anchors:

- public result objects live in `src/excelalchemy/results.py`
- the recommended public import path already includes `excelalchemy.results`
- existing payload contracts are protected by:
  - `tests/contracts/test_result_contract.py`
  - `tests/unit/test_excel_exceptions.py`
  - `scripts/smoke_api_payload_snapshot.py`
  - `files/example-outputs/import-failure-api-payload.json`
- frontend/API guidance already centers on:
  - `docs/result-objects.md`
  - `docs/api-response-cookbook.md`
  - `examples/fastapi_reference/`

That means the safest design is to add a narrow, opt-in serializer in the existing public results layer and leave the default payload builders untouched.

## Recommended Approach

### Recommendation

Use a single new public helper function in `excelalchemy.results`:

```python
build_frontend_remediation_payload(
    *,
    result: ImportResult,
    cell_error_map: CellErrorMap,
    row_error_map: RowIssueMap,
) -> dict[str, object]
```

### Why this is the narrowest additive public entry point

This is the smallest stable API surface because it:

- adds one new public callable instead of changing multiple existing methods
- does not change `ImportResult`, `CellErrorMap`, or `RowIssueMap` method signatures
- does not require a new public module
- fits the current public API guidance, which already treats `excelalchemy.results` as the place for structured result helpers
- keeps package-root export optional rather than required

### Public entry point decision

The narrowest additive public entry point should be:

- a module-level helper in `excelalchemy.results`

It should not initially require a root export from `excelalchemy.__init__.py`.

Reason:

- `excelalchemy.results` is already a stable public module
- not exporting from the package root avoids widening the common import surface
- the feature is specialized enough that an explicit `from excelalchemy.results import ...` is appropriate

## Where Remediation Summary Should Live

### Recommended placement

The remediation summary should live as a serializer/preset layer inside `src/excelalchemy/results.py`.

### Why not attach it to existing result objects

Attaching remediation methods directly to existing classes would enlarge the stable method surface of:

- `ImportResult`
- `CellErrorMap`
- `RowIssueMap`

That creates more compatibility burden than necessary for a v1 experiment.

It also creates an awkward ownership question:

- `ImportResult` alone does not know enough about field- and row-level remediation
- `CellErrorMap` and `RowIssueMap` alone do not know enough about header-invalid outcomes

A serializer that accepts all three public objects matches the current repository design better.

### Why not create a separate helper module

Creating something like `excelalchemy.remediation` or `excelalchemy.frontend` would introduce a brand-new public module for a single narrowly scoped feature.

That would:

- increase public API surface more than necessary
- require extra public API documentation and boundary work
- be harder to justify while the feature is still explicitly a v1 experiment

## Source Of `suggested_action` / `fix_hint` In v1

### Recommended source hierarchy

Use a strict, additive derivation order:

1. `ImportResult` result state and header issue buckets for top-level remediation actions
2. `message_key` from underlying `ExcelCellError` / `ExcelRowError` when present
3. selected fallback `code` mappings where the code is already stable enough
4. no hint when the issue is not confidently recognized

### Concrete v1 policy

Top-level remediation guidance should come from:

- `result.result`
- `result.is_header_invalid`
- `result.is_data_invalid`
- `result.missing_required`
- `result.missing_primary`
- `result.unrecognized`
- `result.duplicated`
- `result.url`

Item-level and grouped remediation guidance should come from:

- `error.message_key` first
- `error.code` second

They should not come from:

- free-text parsing of `message`
- workbook-facing `display_message`
- schema metadata that does not already participate in result construction
- any new pipeline-generated remediation fields

### Why this is the safest v1 source

This approach is narrow and testable because:

- `message_key` is already explicit and structured
- `code` already appears in stable payloads
- header-invalid actions can be derived without new execution logic
- unknown errors can cleanly omit hints

### Important v1 limitation

The current repository still produces broad fallback codes such as `ExcelCellError` and `ExcelRowError` in some flows. That means v1 hint coverage should be intentionally sparse. High-confidence omissions are better than low-confidence generic advice.

## Best Verifier Anchors

### Primary anchors

These are the strongest existing verification anchors for this feature:

- `tests/contracts/test_result_contract.py`
  - best place to lock the new public helper entry point and its top-level payload contract
- `tests/unit/test_excel_exceptions.py`
  - best place to verify issue-record-derived remediation payload details, mapping behavior, and omission behavior
- `scripts/smoke_api_payload_snapshot.py`
  - best smoke check for end-to-end payload stability
- `files/example-outputs/import-failure-api-payload.json`
  - canonical snapshot for the invalid-import payload example

### Secondary anchors

Use these only if the reference example adopts the new payload:

- `examples/fastapi_reference/responses.py`
- `examples/fastapi_reference/schemas.py`
- `examples/fastapi_reference/README.md`
- `tests/integration/test_examples_smoke.py`
- `scripts/generate_example_output_assets.py`

### Why these are the right anchors

They align with the feature shape:

- public API contract
- focused result serialization logic
- one canonical invalid-import payload snapshot
- one copyable backend integration example

They avoid drifting into pipeline, storage, or compatibility verification that this feature does not need.

## Docs That Must Change If Implemented Correctly

### Must change

- `docs/result-objects.md`
  - add the new remediation helper and explain where it fits relative to existing payload helpers
- `docs/api-response-cookbook.md`
  - add one frontend-remediation-oriented response shape using the new helper
- `examples/fastapi_reference/README.md`
  - show the new response section if the FastAPI reference adopts it

### Conditional changes

- `docs/public-api.md`
  - only if the new helper is meant to be part of the documented stable helper set
- `docs/integration-roadmap.md`
  - only if the frontend path should explicitly point readers to the remediation helper

### Should not need changes

- `README.md`
- `README-pypi.md`
- `MIGRATIONS.md`
- storage docs
- compatibility docs

## Rejected Alternative

### Rejected option

Add a `preset=` or `mode=` parameter to existing serializers such as:

- `ImportResult.to_api_payload(preset='frontend_remediation')`
- `CellErrorMap.to_api_payload(preset='frontend_remediation')`
- `RowIssueMap.to_api_payload(preset='frontend_remediation')`

### Why reject it

This looks compact, but it is the wrong tradeoff for this repository:

- it changes stable public method signatures on first-class public objects
- it introduces branching behavior into serializers whose current contracts are already documented and smoke-tested
- it makes ownership unclear because remediation needs combined data from `ImportResult`, `CellErrorMap`, and `RowIssueMap`
- it increases the chance of future preset sprawl in already-core methods
- it is harder to explain and test than one standalone helper with one fixed output shape

In short:

- one new helper is easier to document, easier to snapshot, and easier to keep additive than adding “serializer modes” to three existing public objects

## Precise Implementation Boundaries

### In scope

- one new public helper in `src/excelalchemy/results.py`
- small private mapping helpers in `src/excelalchemy/results.py` if needed
- contract tests for the new helper
- focused unit tests for hint derivation and omission behavior
- docs updates for result objects and API cookbook
- optional adoption in `examples/fastapi_reference/`
- snapshot smoke update if the canonical payload asset intentionally includes remediation output

### Out of scope

- changes to `src/excelalchemy/core/*`
- changes to the import execution pipeline
- new storage behavior
- compatibility cleanup
- broad package-root re-export expansion
- new public modules
- new async/job abstractions
- automatic remediation or workbook rewriting

## Checklist Of Files Likely To Change

### Core implementation

- [ ] `src/excelalchemy/results.py`
- [ ] `src/excelalchemy/__init__.py` only if root export is intentionally added

### Tests

- [ ] `tests/contracts/test_result_contract.py`
- [ ] `tests/unit/test_excel_exceptions.py`
- [ ] `tests/integration/test_examples_smoke.py` only if the FastAPI reference example response changes

### Docs and examples

- [ ] `docs/result-objects.md`
- [ ] `docs/api-response-cookbook.md`
- [ ] `examples/fastapi_reference/responses.py` if the example adopts the helper
- [ ] `examples/fastapi_reference/schemas.py` if the example adopts the helper
- [ ] `examples/fastapi_reference/README.md` if the example adopts the helper
- [ ] `docs/public-api.md` only if the helper is added to the documented stable helper list
- [ ] `docs/integration-roadmap.md` only if the frontend reading path is updated

### Smoke assets

- [ ] `scripts/smoke_api_payload_snapshot.py`
- [ ] `files/example-outputs/import-failure-api-payload.json`
- [ ] `scripts/generate_example_output_assets.py` only if example output generation is extended
- [ ] `scripts/smoke_docs_assets.py` only if new stable doc fragments need smoke coverage

## Checklist Of Verifiers That Must Pass

- [ ] `uv run ruff format --check .`
- [ ] `uv run ruff check .`
- [ ] `uv run pyright`
- [ ] `uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests`
- [ ] `uv run python scripts/smoke_package.py`
- [ ] `uv run python scripts/smoke_examples.py`
- [ ] `uv run python scripts/smoke_docs_assets.py`
- [ ] `uv run python scripts/smoke_api_payload_snapshot.py`

## Final Design Decision

For `Front-end remediation payload v1`, the preferred design is:

- one opt-in helper function in `excelalchemy.results`
- implemented as a serializer/preset layer in `src/excelalchemy/results.py`
- driven by existing `ImportResult`, `CellErrorMap`, and `RowIssueMap`
- deriving hints from header issue buckets, `message_key`, and selected stable `code` mappings only
- verified primarily by result contract tests, payload-focused unit tests, and the existing invalid-import snapshot smoke path

This is the smallest additive API surface with the strongest testability in the current repository.
