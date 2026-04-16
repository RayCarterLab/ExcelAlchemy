# v2.3 Front-end Remediation Payload v1

Status: `planned`

## Problem Statement

ExcelAlchemy already exposes stable import result payloads through:

- `ImportResult.to_api_payload()`
- `CellErrorMap.to_api_payload()`
- `RowIssueMap.to_api_payload()`

Those payloads are useful and already frontend-capable, but they are still optimized around raw result inspection rather than remediation flow. Frontend consumers currently need to derive their own:

- remediation-oriented aggregate summary
- suggested next action
- optional fix hints for known issue types
- compact payload shape tuned for “what should the user do next?”

For `v2.3`, the experiment should stay narrow: add an additive frontend remediation payload layer on top of the existing result objects without changing the import pipeline, storage behavior, or current default payload contracts.

## Goals

- Add a frontend-oriented remediation payload capability on top of existing import result objects.
- Keep the feature additive and backward-compatible.
- Preserve the existing `to_api_payload()` default shapes.
- Provide an aggregated remediation summary derived from existing result data.
- Add optional `fix_hint` / `suggested_action` fields for known issue patterns.
- Provide one explicit serializer entry point for this payload so downstream API code can opt in intentionally.
- Update the minimal docs, example integration, and smoke assets needed to make the feature visible and verifiable.

## Non-Goals

- Automatic fixing or workbook mutation.
- Async jobs, background processing, or progress reporting.
- Import execution pipeline redesign.
- Storage redesign or storage-specific behavior.
- Global public API renaming.
- Broad refactors of result objects unrelated to remediation payloads.
- Expanding compatibility shims or deprecation behavior.

## Proposed User-Visible Behavior

### Existing payloads remain unchanged

These existing serializers must keep their current behavior and documented shapes:

- `ImportResult.to_api_payload()`
- `CellErrorMap.to_api_payload()`
- `RowIssueMap.to_api_payload()`

### New additive remediation serializer

Add one new public, frontend-focused serializer under `excelalchemy.results`.

Preferred direction:

- introduce a standalone helper such as `build_frontend_remediation_payload(...)`

Why this direction:

- it avoids branching the stable default `to_api_payload()` behavior
- it keeps the remediation feature explicitly opt-in
- it avoids coupling the new payload too tightly to any one result object
- it keeps the implementation in the public results layer instead of the import pipeline

The helper should accept the existing public result surfaces:

- `ImportResult`
- `CellErrorMap`
- `RowIssueMap`

### Remediation payload v1 contents

The first version should be intentionally small and deterministic. The payload should include:

- stable import status summary
- remediation aggregate summary
- top-level suggested next action
- optional item-level and summary-level `fix_hint` / `suggested_action`
- compact grouped data oriented around remediation, not full raw inspection

The expected shape should be centered on sections like:

- `result`
  - stable overall status, likely derived from `ImportResult`
- `remediation`
  - aggregate counts such as affected rows, affected fields, affected codes, and whether a result workbook is available
  - top-level `suggested_action`
  - top-level `fix_hint` when the issue is globally actionable, such as header mismatch
- `by_field`
  - field-oriented remediation summaries derived from `CellErrorMap.summary_by_field()`
- `by_code`
  - code-oriented remediation summaries derived from existing summary helpers
- `items`
  - compact issue records with optional `fix_hint` / `suggested_action`

Version 1 should not attempt to replace the existing rich payloads. It should be a thinner, frontend-task-oriented view built from them.

### Hint behavior

Hints should be optional and best-effort:

- use known `message_key` values first when present
- fall back to known `code` mappings where safe
- if no mapping is known, leave `fix_hint` / `suggested_action` unset in a consistent way

Version 1 should not invent speculative hints for unknown errors.

## Likely Code Areas Affected

### Public result surfaces

- `src/excelalchemy/results.py`
  - primary implementation location for the remediation serializer and any small helper data structures
- `src/excelalchemy/__init__.py`
  - only if the new serializer is exported from the package root

### Public docs

- `docs/result-objects.md`
  - document the new remediation serializer alongside the existing result helpers
- `docs/api-response-cookbook.md`
  - add a frontend-remediation-oriented response example
- `docs/public-api.md`
  - update only if a new public helper is added to the stable public surface
- `docs/integration-roadmap.md`
  - update only if the recommended frontend-reading path should explicitly mention the new helper

### Example integration surface

- `examples/fastapi_reference/responses.py`
  - opt into the new remediation payload in the reference response builder
- `examples/fastapi_reference/schemas.py`
  - extend the example response schema with a remediation field if the example adopts it
- `examples/fastapi_reference/README.md`
  - document the new response section and example JSON

### Tests

- `tests/contracts/test_result_contract.py`
  - contract coverage for the new public serializer
- `tests/unit/test_excel_exceptions.py`
  - focused payload-shape and helper coverage for `CellErrorMap` / `RowIssueMap` driven remediation output
- `tests/integration/test_examples_smoke.py`
  - only if the FastAPI reference example response shape changes

### Smoke and generated assets

- `scripts/smoke_api_payload_snapshot.py`
  - extend or add a remediation snapshot assertion path
- `scripts/generate_example_output_assets.py`
  - regenerate captured output if example payload output changes
- `scripts/smoke_docs_assets.py`
  - update required fragments only if docs gain a stable remediation section reference
- `files/example-outputs/import-failure-api-payload.json`
  - update only if the canonical failure payload asset intentionally includes remediation output

## Test Strategy

### Contract tests

Add contract tests that verify:

- the new remediation serializer is available from the intended public module
- existing `to_api_payload()` outputs are unchanged
- remediation payloads for `SUCCESS`, `HEADER_INVALID`, and `DATA_INVALID` are deterministic
- aggregate counts are derived correctly from existing result objects
- item ordering is deterministic enough for snapshot-style assertions

### Unit tests

Add focused tests that verify:

- known `message_key` mappings produce `fix_hint` / `suggested_action`
- known `code` mappings work when `message_key` is absent
- unknown issues omit remediation hints consistently
- field-level and row-level summaries do not over-count duplicated records
- header-invalid remediation summaries do not require row or cell errors

### Integration tests

If the FastAPI reference app adopts the remediation payload:

- extend the example smoke coverage to assert the new response section exists
- keep the reference app compile/runtime smoke path small and additive

### Smoke validation

Keep smoke verification narrow:

- extend the API payload snapshot path rather than introducing a new smoke workflow
- update doc smoke only for stable, durable fragments
- avoid expanding smoke to unrelated examples

## Docs, Examples, And Smoke Updates Required

Required if the feature is implemented:

- document the remediation helper in `docs/result-objects.md`
- add one cookbook example in `docs/api-response-cookbook.md`
- update `examples/fastapi_reference/README.md` to show the new response section
- update `examples/fastapi_reference/responses.py` and `schemas.py` if the reference app uses the new serializer
- update `scripts/smoke_api_payload_snapshot.py`
- update `files/example-outputs/import-failure-api-payload.json` if the canonical snapshot is expanded

Likely not required unless scope grows:

- `README.md`
- `README-pypi.md`
- compatibility docs such as `MIGRATIONS.md`
- storage docs

## Risks And Open Questions

### 1. Hint quality is constrained by current error metadata

Many current payloads still expose broad fallback codes such as `ExcelCellError`. Useful remediation hints cannot assume a rich code taxonomy already exists.

Planned constraint:

- v1 hints should be sparse and high-confidence
- unknown issues should not receive guessed remediation text

### 2. Message locale needs explicit policy

Runtime/API text in 2.x is English-first, while workbook-facing text is locale-aware.

Open question:

- should remediation hint text follow the existing English-first API policy in v1, or should it attempt locale-aware text when the error originated from a `message_key`?

Recommended v1 answer:

- keep remediation hint text aligned with the current API/runtime policy unless there is a very low-cost locale-aware path

### 3. Payload scope can sprawl quickly

There is a real risk of turning a narrow serializer into a second full response model.

Planned constraint:

- v1 should add only summary, action, and compact remediation groupings
- it should not duplicate every section from the existing raw payloads

### 4. Public API surface choice must stay conservative

Adding a preset argument to the existing `to_api_payload()` methods is technically possible, but it increases branching in already-stable serializers.

Planned decision:

- prefer a new standalone remediation serializer helper over changing the existing serializer signatures

### 5. Compatibility aliases should remain out of scope

If package-root export changes or facade examples touch old aliases indirectly, treat that as a documentation and testing consideration, not as a reason to modify compatibility shims.

## Phased Implementation Steps

### Phase 1. Lock the v1 payload contract

- define the remediation payload shape in `docs/result-objects.md` and/or the plan-local notes during implementation
- choose the exact public entry point name in `src/excelalchemy/results.py`
- define the initial hint mapping policy:
  - `message_key` first
  - selected fallback `code` mappings second
  - unknown issues omitted
- define deterministic ordering for grouped sections

### Phase 2. Implement the public serializer narrowly

- add the remediation serializer in `src/excelalchemy/results.py`
- keep all existing serializers unchanged
- export from `src/excelalchemy/__init__.py` only if the helper is intended to be package-root public

### Phase 3. Add contract and unit coverage

- add contract tests for public availability and stable payload output
- add unit tests for mapping, omission, and aggregation behavior
- add regression coverage for success, header-invalid, and data-invalid cases

### Phase 4. Update reference integration and docs

- adopt the remediation payload in `examples/fastapi_reference/`
- document the new helper in result-object and API-cookbook docs
- keep example changes minimal and aligned with the preferred public import path

### Phase 5. Refresh smoke assets

- update the API payload snapshot path
- regenerate any affected example output asset
- keep `scripts/smoke_docs_assets.py` aligned if new durable doc fragments are introduced

## Explicit Acceptance Criteria

- A new additive remediation serializer exists in the public results layer.
- Existing `ImportResult.to_api_payload()`, `CellErrorMap.to_api_payload()`, and `RowIssueMap.to_api_payload()` contract outputs remain unchanged.
- The remediation serializer supports `SUCCESS`, `HEADER_INVALID`, and `DATA_INVALID` outcomes.
- The remediation payload includes an aggregated remediation summary.
- The remediation payload includes optional `fix_hint` and/or `suggested_action` fields for known issue patterns.
- Unknown issue patterns do not receive guessed remediation hints.
- The implementation does not modify the import execution pipeline.
- The implementation does not introduce async/job concepts.
- The implementation does not require storage changes.
- Contract tests cover the new public behavior.
- Relevant docs and the FastAPI reference example are updated if they opt into the new payload.
- Snapshot/smoke verification is updated and passes for the intended canonical example payload.

## Verification

When implementation starts, the verification set for this plan should include:

- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pyright`
- `uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests`
- `uv run python scripts/smoke_package.py`
- `uv run python scripts/smoke_examples.py`
- `uv run python scripts/smoke_docs_assets.py`
- `uv run python scripts/smoke_api_payload_snapshot.py`
