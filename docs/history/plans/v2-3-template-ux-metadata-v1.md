# v2.3 Template UX Metadata v1

Status: `planned`

## Problem Statement

ExcelAlchemy already generates user-facing workbook templates and already supports
template-side comments such as:

- required vs optional guidance
- date/number formatting guidance
- option lists
- free-form `hint`

That existing surface is useful, but it still leaves a common usability gap:
users may understand the rule while still not knowing what a valid value should
look like in practice.

For `v2.3`, this experiment should stay narrow. The goal is not to redesign
template generation or introduce a spreadsheet validation engine. The goal is to
add one small, stable layer of template UX metadata so generated templates do
more to prevent user mistakes before upload.

## Goals

- Strengthen template-side user guidance in generated workbooks.
- Keep the feature additive and backward-compatible.
- Reuse the existing stable metadata and template-comment path.
- Make the new capability easy to verify through tests, docs, examples, and
  smoke assets.
- Prefer one rendering strategy for v1 rather than several competing surfaces.

## Non-Goals

- Native Excel data-validation rules, dropdown matrices, or a validation engine.
- Async jobs, orchestration, or import remediation work.
- Import execution or runtime validation redesign.
- Broad schema metadata architecture redesign.
- Template layout redesign with extra sheets, guide tables, or hidden metadata
  structures.
- Broad public API renaming or compatibility cleanup.
- Storage redesign.

## Recommended Narrow v1 Scope

The recommended v1 slice is:

- add one new optional field-level metadata value for example guidance
- thread it through the existing public metadata entry points
- render it only into existing header comments for generated templates

Recommended new metadata field:

- `example_value: str | None = None`

Recommended public entry points:

- `FieldMeta(..., example_value=...)`
- `ExcelMeta(..., example_value=...)`

This keeps the feature explicit and small. It also avoids overloading the
existing sample-row path on `download_template(...)`, which already exists for
real row data rather than field metadata.

## Likely User-Visible Behavior

When a field declares `example_value`, the generated template header comment for
that field gains one additional localized line.

Representative examples:

- `示例：张三`
- `Example: alice@company.com`

Behavior rules for v1:

- if `example_value` is omitted, template output is unchanged
- no new rows, columns, or sheets are introduced
- import parsing and validation behavior remain unchanged
- the feature is purely workbook-guidance metadata
- template generation must still avoid native Excel data-validation rules

## Candidate Rendering Strategies

### Option 1. Header comment augmentation

Render the new metadata into the existing per-field header comment.

Why it fits:

- aligns with the current invariant that template guidance is encoded in
  comments and formatting
- reuses existing public metadata and writer/comment seams
- does not alter workbook structure
- is easy to verify in contract tests and locale tests

### Option 2. Prefilled example rows

Do not choose this for v1.

Why not:

- overlaps with the existing sample-row behavior on `download_template(...)`
- changes worksheet content rather than metadata only
- creates ambiguity about whether the values are placeholders, examples, or
  real user-editable rows

### Option 3. Native Excel validation or input-message rules

Do not choose this for v1.

Why not:

- conflicts with the current repository invariant that generated templates do
  not rely on Excel data-validation rules
- expands scope into validation policy rather than UX metadata
- would require a broader stable API and test matrix than this experiment
  should own

## Recommended Direction

Implement only Option 1 in v1:

- extend metadata with one optional `example_value`
- render it through existing header comments
- keep all other template behavior unchanged

## Likely Code Areas Affected

### Public metadata surface

- `src/excelalchemy/metadata.py`
  - add the new optional metadata input and thread it through the existing
    workbook-presentation metadata path

### Template comment rendering

- `src/excelalchemy/codecs/*.py`
  - update existing built-in comment builders that already compose field-level
    template comments
- `src/excelalchemy/core/writer.py`
  - inspect only if a small comment-assembly touch is needed; avoid unrelated
    rendering refactors

### Locale / workbook-facing text

- `src/excelalchemy/i18n/messages.py`
  - only if a localized label such as `Example:` / `示例：` needs to be added

### Tests

- `tests/contracts/test_template_contract.py`
- `tests/unit/test_field_metadata.py`
- representative codec-level unit tests only if existing comment assertions are
  already the local convention

### Docs / examples / smoke

- `docs/getting-started.md`
- `docs/public-api.md`
- one metadata-focused example such as `examples/annotated_schema.py`
- `tests/integration/test_examples_smoke.py`
- `scripts/smoke_examples.py`
- `scripts/smoke_docs_assets.py`
- `files/example-outputs/` only if a captured example output changes

## Test Strategy

### Contract tests

Add or extend contract coverage to verify:

- generated templates still return the same payload/artifact types
- generated templates still contain no Excel data validations
- a field with `example_value` produces a header comment containing the example
  line
- English locale templates render the English example label
- templates without `example_value` remain unchanged in the relevant assertions

### Unit tests

Add focused metadata tests to verify:

- `FieldMeta(..., example_value=...)` stores the expected metadata
- `ExcelMeta(..., example_value=...)` stores the expected metadata
- any comment-ready example accessor is localized correctly
- blank or `None` example values do not create comment text

### Example and smoke coverage

Keep this narrow:

- update one runnable example to show the feature
- keep example smoke passing
- regenerate captured outputs only if example stdout or durable example assets
  intentionally change

## Docs, Examples, And Smoke Updates Required

If the feature is implemented, update the minimum repository-facing material
that teaches template metadata:

- `docs/getting-started.md`
  - add one concise metadata example using `example_value`
- `docs/public-api.md`
  - document the new optional metadata field on the stable public metadata
    surface
- `examples/annotated_schema.py`
  - show one practical use of `example_value`
- `examples/README.md`
  - only if the example description should explicitly mention template guidance
- `README.md` and `README-pypi.md`
  - only if the chosen example snippet there is intentionally updated

If example output changes intentionally, also update:

- `files/example-outputs/`
- `scripts/generate_example_output_assets.py`
- `scripts/smoke_docs_assets.py`

`scripts/smoke_api_payload_snapshot.py` should remain untouched unless this
experiment accidentally spills into API payload work, which it should not.

## Risks And Open Questions

### 1. Field naming should stay narrow

Recommended decision:

- use `example_value`, not a broader name like `example`

Why:

- avoids confusion with sample rows
- avoids implying richer structured examples in v1

### 2. Comment composition is distributed across codecs

Risk:

- built-in field codecs already own portions of comment rendering, so the
  change should be applied conservatively rather than used as an excuse for a
  shared comment abstraction refactor

Planned response:

- keep implementation boring and explicit
- touch only the codecs that already participate in template comment building

### 3. Locale wording must follow workbook-facing policy

Risk:

- the example label is workbook-facing text, so it should follow the workbook
  locale rather than the runtime/API English-first policy

Planned response:

- localize the label through the existing workbook-facing message path

### 4. Scope can easily drift into validation UX

Risk:

- once template UX is in scope, it is tempting to add dropdowns, rules,
  prefilled rows, guide sheets, or other Excel features

Planned response:

- keep v1 to one metadata field and one rendering surface
- record broader ideas in `docs/tech-debt/` or a later plan instead of expanding
  this slice

## Phased Implementation Steps

### Phase 1. Lock the metadata contract

- add the new optional metadata field to the accepted v1 scope
- confirm that the public surface is limited to `FieldMeta(...)` and
  `ExcelMeta(...)`

### Phase 2. Implement narrow rendering

- thread the metadata into the existing workbook-presentation metadata path
- render the example line in header comments only
- keep workbook structure and import behavior unchanged

### Phase 3. Protect behavior with tests

- extend template contract tests
- extend metadata unit tests
- add the minimum representative comment-rendering assertions needed

### Phase 4. Update repository-facing materials

- update the smallest useful set of docs and one runnable example
- refresh example outputs only if durable example artifacts change
- keep smoke scripts passing

## Acceptance Criteria

- `FieldMeta` accepts `example_value` without breaking existing call sites
- `ExcelMeta` accepts `example_value` without breaking existing call sites
- generated templates remain structurally unchanged except for an added comment
  line when `example_value` is present
- generated templates still contain no native Excel data-validation rules
- workbook-facing example labels are localized for `zh-CN` and `en`
- templates without `example_value` preserve existing behavior
- tests cover the new comment behavior and the existing template invariants
- at least one user-facing example and the relevant metadata docs show the new
  capability

## Verification

Expected verification once implementation exists:

- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pyright`
- `uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests`
- `uv run python scripts/smoke_examples.py`
- `uv run python scripts/smoke_docs_assets.py`

## Decision Log

- Decision: keep v1 on the existing header-comment surface only.
  - Why: this is the smallest additive path that matches current invariants and
    avoids workbook-structure changes.
  - Affected paths: `src/excelalchemy/metadata.py`, built-in codec comment
    builders, template contract tests, metadata docs/examples.

- Decision: prefer a single `example_value` field instead of a broader template
  guidance model.
  - Why: narrower stable API surface, clearer semantics, easier verification.
  - Affected paths: public metadata constructors, metadata docs, example usage.
