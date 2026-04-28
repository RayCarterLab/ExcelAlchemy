# Agent Testing Guide

This file defines validation expectations for AI agents.

## Full Validation

Use full validation when changes affect shared workflow behavior, public API,
storage, result payloads, docs smoke expectations, or examples.

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

## Focused Validation

Choose focused checks for narrow changes:

- Codec behavior: relevant `tests/unit/codecs/` tests.
- Public contracts: relevant `tests/contracts/` tests.
- Examples: `tests/integration/test_examples_smoke.py` and
  `scripts/smoke_examples.py`.
- Result payloads: `tests/contracts/test_result_contract.py`,
  `scripts/smoke_api_payload_snapshot.py`.
- Storage behavior: `tests/contracts/test_storage_contract.py`.
- Compatibility and deprecations: `tests/unit/test_deprecation_policy.py`.
- Locale behavior: `docs/locale.md` plus relevant contract tests.

## Failure Handling

When validation fails:

1. Capture the exact failing command.
2. Read the error output.
3. Identify whether the failure is caused by the patch, environment, dependency
   state, flaky external service, or pre-existing repository state.
4. Inspect the relevant source and tests.
5. Update the plan with a specific hypothesis.
6. Apply a targeted fix.
7. Re-run the narrow failing check.
8. Run broader checks if the fix affects shared behavior.

Do not retry blindly. Do not weaken tests only to pass validation. Do not report
success when checks failed or were not run.

## If Validation Cannot Run

Report:

- Command attempted.
- Reason it could not run.
- Scope of unvalidated behavior.
- Recommended next validation step.

## Generated Outputs

Regenerate `files/example-outputs/` with
`scripts/generate_example_output_assets.py` when captured example output changes
intentionally.

Keep these smoke checks passing after docs or payload changes:

- `scripts/smoke_docs_assets.py`
- `scripts/smoke_api_payload_snapshot.py`
