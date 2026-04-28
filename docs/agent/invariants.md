# Agent Invariants

This file records ExcelAlchemy-specific invariants and code modification rules
for AI agents.

## Codec Abstraction

- Field behavior belongs in codecs under `src/excelalchemy/codecs/`.
- Do not bypass codec parsing, formatting, normalization, or header-comment
  behavior with ad hoc logic elsewhere.
- Composite codecs must preserve stable flattened labels, keys, offsets, and
  reconstruction behavior.
- Codec-specific changes require nearby unit tests under `tests/unit/codecs/`
  or contract tests when behavior is public.

## Reversible Transformations

- Workbook transformations must be explainable and round-trippable for supported
  types.
- Preserve enough structure to map parsed values, validation errors, and rendered
  feedback back to workbook coordinates.
- Do not introduce lossy normalization unless it is explicitly required,
  documented, and tested.
- Imports must preserve the distinction between cell-level and row-level issues.

## Type Safety

- Prefer explicit types over untyped dictionaries and implicit conventions.
- Preserve Pydantic boundary behavior in `src/excelalchemy/helper/pydantic.py`.
- Public result objects and config objects must remain typed and stable.
- Do not silence type errors without a narrow documented reason.

## No Implicit State

- Import sessions must not leak state across runs.
- Avoid module-level mutable state, hidden caches, environment-dependent
  behavior, time-dependent behavior, random ordering, and implicit global
  configuration.
- Any cache must have deterministic keys, bounded scope, and tests that prove it
  does not affect correctness.

## Workbook and Storage Contracts

- Runtime workbook tables use `WorksheetTable`, not pandas-first internals.
- Storage is a protocol boundary through `ExcelStorage`; do not hard-wire Minio
  into core architecture.
- Uploaded workbook payloads must remain binary `.xlsx` content, not prefixed
  data URLs.
- Template generation does not require a configured storage backend.
- Header-invalid imports end without uploading a result workbook.
- Data-invalid imports upload a result workbook and report a download URL.
- Explicit `storage` takes precedence over legacy Minio settings when both are
  supplied.
- Storage readers are expected to return `WorksheetTable` and preserve
  merged-header gaps as empty cells.
- Generated templates do not rely on native Excel data-validation rules; user
  guidance is encoded in comments, formatting, and runtime validation.

## Result and Locale Contracts

- Result payloads and API-facing shapes are stable 2.x surfaces.
- Preserve `ImportResult`, `CellErrorMap`, and `RowIssueMap` behavior unless the
  task explicitly changes it.
- `ImportResult` has exactly three top-level result states: `SUCCESS`,
  `HEADER_INVALID`, and `DATA_INVALID`.
- Workbook-facing display locale supports `zh-CN` and `en`.
- Runtime exceptions and diagnostics are English-first in 2.x.
- Do not change message wording casually when tests or docs treat it as contract.
- `ImportResult.from_validate_header_result(...)` is only valid for failed
  header validation.
- Template and export APIs expose both browser-friendly data URLs and
  binary-friendly `ExcelArtifact` paths. Do not collapse these transport shapes.
- Workbook-facing text covers import instructions, header comments,
  result/reason labels, row status text, and workbook-facing value text.
- Import result workbooks prepend result and reason columns and mark failures
  visually.
- Required template headers are visually distinguished and annotated with
  comments.
- `excelalchemy.const` compatibility constants represent stable `zh-CN`
  defaults, not the full locale policy.

## Schema and Validation Contracts

- Excel metadata is attached to Pydantic fields without turning the field object
  into `FieldMetaInfo`.
- Schema extraction flattens composite fields into ordered unique labels, keys,
  and offsets.
- Repeated child labels are valid when they belong to different parent labels.
- Row aggregation reconstructs composite columns back into parent-shaped
  payloads before validation and callbacks.
- Pydantic field-level validation errors become `ExcelCellError`; model-level
  validation errors become `ExcelRowError`.
- Missing-field and field-format validation messages are normalized into
  workbook-facing ExcelAlchemy errors.

## Public Behavior and Compatibility

- Stable public behavior is protected primarily by `tests/contracts/` and
  `tests/integration/`.
- Examples are part of the user-facing contract.
- Deprecated modules and aliases still exist in 2.x and must continue to emit
  explicit deprecation warnings.
- Legacy Minio config still works but emits deprecation warnings.
- `excelalchemy.types.*` is preserved for 2.x migrations and scheduled for
  removal in 3.0.
- Older import-inspection aliases remain available in 2.x, even though
  `worksheet_table`, `header_table`, `cell_error_map`, and `row_error_map` are
  preferred.
- Compatibility warnings must point to replacement import paths.

## Code Modification Rules

Agents must follow minimal-diff engineering.

Required rules:

- Make the smallest change that satisfies the task.
- Preserve existing public interfaces by default.
- Preserve deterministic behavior.
- Add or update tests for all new logic.
- Prefer established local patterns over new abstractions.
- Keep source, tests, docs, examples, and generated expectations synchronized.
- Use stable public imports in docs and examples.

Prohibited changes without explicit task scope:

- Deleting core modules.
- Removing compatibility shims.
- Replacing `WorksheetTable` with pandas-first internals.
- Reframing storage as Minio-only.
- Presenting internal modules as stable application-facing API.
- Touching generated outputs without regeneration and validation.
- Reformatting unrelated files.

## Safety Boundaries

Never do the following without explicit user instruction:

- Delete or replace `src/excelalchemy/` core modules.
- Remove public exports from `src/excelalchemy/__init__.py`.
- Remove compatibility modules or deprecation warnings.
- Modify unrelated files.
- Rewrite repository history.
- Change generated output snapshots without running their generator or smoke
  check.
- Add network, filesystem, time, or randomness dependencies to core logic unless
  the task explicitly requires them and tests control them.
- Commit secrets, credentials, tokens, or private endpoint details.
