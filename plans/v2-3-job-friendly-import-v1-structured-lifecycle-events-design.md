# v2.3 Job-friendly Import v1: Structured Import Lifecycle Events

Status: `planned`

## Chosen API Design

Use the existing import entry point and add one optional keyword-only callback:

```python
await alchemy.import_data(
    input_excel_name,
    output_excel_name,
    on_event=handle_event,
)
```

Recommended signature:

```python
async def import_data(
    self,
    input_excel_name: str,
    output_excel_name: str,
    *,
    on_event: Callable[[dict[str, object]], None] | None = None,
) -> ImportResult
```

This is the smallest additive API that satisfies the feature goal:

- no new public method
- no config-level event registration
- no observer class
- no generator-based import mode
- no new persistence or background execution model

The callback is per-run rather than attached to the `ExcelAlchemy` instance or
`ImporterConfig`, which keeps the surface narrow and avoids sticky runtime
state.

## Why This Is The Simplest Viable Shape

The repository already has one stable import control flow:

- `ExcelAlchemy.import_data(...)`
- `ImportSession.run(...)`

The design should layer observability onto that path, not create a second one.

This callback shape is the narrowest fit because it:

- keeps `import_data(...)` as the only import workflow entry point
- avoids widening `ImporterConfig` for a runtime-only concern
- avoids introducing a second public abstraction just to carry events
- is trivial to test with a local `events.append`
- does not require consumers to learn a different import API

## Rejected Alternative

Reject a generator-based API such as:

```python
async for event in alchemy.stream_import_data(...):
    ...
```

Reasoning:

- it creates a second public import workflow beside `import_data(...)`
- it complicates the final-result path for callers that still need
  `ImportResult`
- it likely requires expanding `src/excelalchemy/core/abstract.py`
- it is more surface area than this v1 needs

Also reject a config-level callback on `ImporterConfig` for v1.

Reasoning:

- it broadens config surface for a per-run runtime concern
- it creates callback lifetime questions on long-lived `ExcelAlchemy` instances
- it is less explicit than passing the handler directly to the import call that
  uses it

## Event Structure

Use plain event dictionaries for v1.

Do not introduce a public event class hierarchy yet.

Required common field:

- `event`

All other fields should be event-specific and only included when needed for
progress or outcome.

### Event Kinds

- `started`
- `header_validated`
- `row_processed`
- `completed`
- `failed`

### Recommended Event Payloads

`started`

```python
{'event': 'started'}
```

`header_validated`

```python
{'event': 'header_validated', 'is_valid': True}
```

```python
{
    'event': 'header_validated',
    'is_valid': False,
    'missing_required': [...],
    'missing_primary': [...],
    'unrecognized': [...],
    'duplicated': [...],
}
```

`row_processed`

```python
{
    'event': 'row_processed',
    'processed_row_count': 3,
    'total_row_count': 10,
    'success_count': 2,
    'fail_count': 1,
}
```

`completed`

```python
{
    'event': 'completed',
    'result': 'SUCCESS' | 'DATA_INVALID' | 'HEADER_INVALID',
    'success_count': 9,
    'fail_count': 1,
    'url': 'memory://result.xlsx' | None,
}
```

`failed`

```python
{
    'event': 'failed',
    'error_type': 'ValueError',
    'error_message': '...',
}
```

## Deliberate Non-Fields For v1

Do not add these unless implementation proves they are required:

- no sequence number
- no timestamp
- no `import_mode`
- no `has_merged_header`
- no raw row payload
- no `CellErrorMap` / `RowIssueMap` payload copies
- no event object metadata beyond `event`

This keeps the event contract small and lowers compatibility burden.

## Integration With Existing Import Flow

Fit event emission directly into the existing session lifecycle.

Recommended emission points:

- emit `started` at the beginning of `ImportSession.run(...)`
- emit `header_validated` immediately after `_validate_header(...)`
- emit `row_processed` from `_execute_rows()` using existing counters
- emit `completed` immediately before returning `ImportResult`
- emit `failed` from a top-level `try/except` in `run(...)`, then re-raise

Important semantic rule:

- `HEADER_INVALID` is a normal `completed` outcome
- `DATA_INVALID` is a normal `completed` outcome
- only unexpected exceptions produce `failed`

## How To Avoid Duplicating Logic

Reuse existing runtime state instead of recomputing anything.

Use:

- `ValidateHeaderResult` for header-validation details
- existing row counters in `ImportSession`
- existing final `ImportResult`

Do not duplicate behavior in:

- `src/excelalchemy/core/executor.py`
- `src/excelalchemy/core/rows.py`
- `src/excelalchemy/results.py`

The session should remain the sole place where lifecycle decisions are made and
where events are emitted.

## Exact Boundary Of Changes

In scope:

- add one optional `on_event=` parameter to `import_data(...)`
- thread that callback from facade to `ImportSession`
- add a small private emit helper inside `ImportSession`
- emit five event types from existing lifecycle points
- add contract tests for event order and payload shape
- document the new optional argument

Out of scope:

- new `stream_import_data(...)` method
- config-level observer registration
- public event classes
- config refactor
- executor refactor
- storage changes
- async/background job changes
- result payload changes

## Files To Modify

Source:

- `src/excelalchemy/core/abstract.py`
- `src/excelalchemy/core/alchemy.py`
- `src/excelalchemy/core/import_session.py`

Tests:

- `tests/contracts/test_import_contract.py`

Docs:

- `docs/public-api.md`
- `docs/architecture.md`
- `docs/domain-model.md`

Optional example update:

- `examples/employee_import_workflow.py`

Files that should stay untouched for this narrowed design:

- `src/excelalchemy/config.py`
- `src/excelalchemy/results.py`
- `src/excelalchemy/__init__.py`

## Verifier Checklist

- `import_data(...)` works unchanged when `on_event` is omitted
- successful imports emit:
  - `started`
  - `header_validated`
  - one or more `row_processed`
  - `completed`
- header-invalid imports emit:
  - `started`
  - `header_validated`
  - `completed`
- header-invalid imports emit no `row_processed`
- data-invalid imports emit `completed` with `result='DATA_INVALID'` and `url`
- unexpected exceptions emit `failed` and still re-raise the original exception
- existing `ImportResult`, `CellErrorMap`, `RowIssueMap`, and
  `last_import_snapshot` behavior remains unchanged
- no API payload smoke assets need regeneration unless an example is changed

## Verification Commands

When implementation starts, run:

- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pyright`
- `uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests`
- `uv run python scripts/smoke_package.py`
- `uv run python scripts/smoke_examples.py`
