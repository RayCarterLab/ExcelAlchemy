# v2.3 Template UX Metadata v1 Design Note

Status: `planned`

## Recommended Approach

The narrowest additive public entry point for `Template UX metadata v1` should
be one new optional metadata argument on the existing stable metadata
constructors:

- `FieldMeta(..., example_value=...)`
- `ExcelMeta(..., example_value=...)`

Recommended field:

- `example_value: str | None = None`

This should extend the existing metadata path, not introduce a new helper
module or template-specific wrapper API.

### Why this is the recommended approach

The current repository state already points to this design:

- template guidance is already modeled as metadata plus header comments
- `WorkbookPresentationMeta` already owns workbook-facing comment metadata such
  as `hint`
- `FieldMetaInfo` already exposes `presentation_meta` and `comment_*` accessors
- `download_template(sample_data=...)` already covers the separate use case of
  visible example rows
- `docs/agent/invariants.md` and `tests/contracts/test_template_contract.py` lock in
  the rule that generated templates do not rely on Excel data-validation rules

So the smallest stable API surface is:

- extend existing metadata structures
- keep the render target as header comments only
- avoid any new runtime helper layer

## Relationship To Existing `hint`

`hint` and the new feature should be complementary, not merged.

Recommended semantics:

- `hint`
  - free-form instruction or rule text
  - answers “what should the user keep in mind?”
- `example_value`
  - concrete sample value text
  - answers “what does a valid value look like?”

Recommended rendering policy:

- if both are present, render both
- keep them as separate comment lines
- do not infer one from the other
- do not overload `hint` to carry example semantics

Recommended ordering inside comments:

- keep existing comment ordering stable
- append the example line after existing hint-style text when present

That makes `example_value` the most concrete final cue without changing the
meaning of `hint`.

## Rendering Strategy Decision

Use one rendering strategy only for v1:

- workbook header comments

This is the best fit among the candidate surfaces.

### Why comments are best for v1

- already supported and stable in the repo
- already verified by template contract tests
- localized through the workbook display locale path
- additive without changing workbook structure
- easy to revert if needed

### Rejected alternative

Reject a visible helper row or dedicated example row area for v1.

Reasoning:

- the repo already has a visible sample-row path through
  `download_template(sample_data=...)`
- adding a second visible example surface would blur the distinction between
  field metadata and actual worksheet data
- it would change the worksheet layout and create more verifier churn than a
  comment-only additive change

I would also reject a dedicated instruction/help sheet for the same reason: it
creates a larger workbook contract change than this v1 needs, and the current
template UX contract is comment-centric rather than sheet-centric.

## Precise Implementation Boundaries

Implementation should stay within these boundaries:

- extend `WorkbookPresentationMeta` with one new optional value:
  - `example_value`
- expose a comment-ready accessor in the existing metadata layer:
  - `comment_example`
- thread the new field through:
  - `FieldMetaInfo.__init__(...)`
  - `_build_excel_metadata(...)`
  - `ExcelMeta(...)`
  - `FieldMeta(...)`
- expose the value through the existing `FieldMetaInfo` facade in the same
  style as `hint` and `comment_hint`
- localize the workbook-facing example label through `src/excelalchemy/i18n/messages.py`
- update built-in codec `build_comment(...)` paths to include the example line
  where comments are already produced

Implementation should explicitly stay out of these areas:

- no new package-root helper
- no new template serializer/helper module
- no change to `download_template(...)` arguments or sample-row semantics
- no new worksheet, hidden sheet, helper area, or validation rule surface
- no compatibility shim changes
- no import pipeline or storage behavior changes

## Likely File Change Checklist

Core implementation:

- `src/excelalchemy/metadata.py`
- `src/excelalchemy/i18n/messages.py`
- built-in comment-producing codecs under `src/excelalchemy/codecs/`

Most likely touched codecs:

- `src/excelalchemy/codecs/string.py`
- `src/excelalchemy/codecs/date.py`
- `src/excelalchemy/codecs/number.py`
- `src/excelalchemy/codecs/boolean.py`
- `src/excelalchemy/codecs/radio.py`
- `src/excelalchemy/codecs/multi_checkbox.py`
- `src/excelalchemy/codecs/organization.py`
- `src/excelalchemy/codecs/staff.py`
- `src/excelalchemy/codecs/tree.py`
- `src/excelalchemy/codecs/date_range.py`

Tests:

- `tests/contracts/test_template_contract.py`
- `tests/unit/test_field_metadata.py`
- representative codec unit tests only where comment text is already asserted
- `tests/integration/test_examples_smoke.py` if an example is updated

Docs and examples:

- `docs/getting-started.md`
- `docs/public-api.md`
- `examples/annotated_schema.py`

Smoke and generated assets:

- `scripts/smoke_examples.py` if example output changes
- `scripts/smoke_docs_assets.py` if doc-facing assets change
- `files/example-outputs/` only if an updated example intentionally changes
  captured output

## Strongest Verifier Anchors

The strongest existing verifier anchors are:

### Public behavior

- `tests/contracts/test_template_contract.py`
  - strongest anchor for template comment behavior, locale-visible workbook
    text, required styling, merged headers, and the invariant that templates do
    not use Excel data validations

### Metadata layering

- `tests/unit/test_field_metadata.py`
  - strongest anchor for deciding that v1 should extend existing metadata
    structures rather than add a helper layer
  - already asserts split metadata layers and `comment_hint` behavior

### Examples

- `tests/integration/test_examples_smoke.py`
  - strongest anchor for making one example carry the new public usage story

### Smoke assets

- `scripts/smoke_examples.py`
- `scripts/smoke_docs_assets.py`

`scripts/smoke_api_payload_snapshot.py` is not a relevant anchor for this
feature and should remain untouched.

## Docs That Must Change If Implemented Correctly

These should change if the feature is implemented:

- `docs/public-api.md`
  - because `FieldMeta(...)` and `ExcelMeta(...)` are stable public entry
    points and the new argument belongs on that public metadata surface
- `docs/getting-started.md`
  - because it is the shortest schema declaration guide and should show the new
    metadata in at least one concise example
- `examples/annotated_schema.py`
  - because it is the clearest metadata-focused example surface in the repo

These are likely optional rather than required:

- `examples/README.md`
  - only if the example description should explicitly mention template guidance
- `README.md`
- `README-pypi.md`
  - only if the main snippet is intentionally updated to showcase the new field
- `docs/locale.md`
  - only if the implementation adds enough workbook-facing wording that the
    locale guide should explicitly mention example-comment labels

## Final Recommendation

Implement `Template UX metadata v1` as a small extension of the existing public
metadata layer:

- add `example_value` to `FieldMeta(...)` and `ExcelMeta(...)`
- store it in `WorkbookPresentationMeta`
- expose a localized `comment_example`
- render it in header comments only

This is the smallest additive API surface, it aligns with the current template
invariants, it keeps `hint` intact as a separate concept, and it has the
strongest existing verifier story in the repository.

