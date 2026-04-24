# v2.4 Minimal Platform Alignment Plan

Status: `planned`

Related docs:

- [platform-code-mapping.md](../docs/platform-code-mapping.md)
- [platform-architecture.md](../docs/platform-architecture.md)
- [runtime-model.md](../docs/runtime-model.md)
- [integration-blueprints.md](../docs/integration-blueprints.md)
- [v2-4-import-platform-layer-design.md](./v2-4-import-platform-layer-design.md)
- [v2-4-import-platform-layer-design-note.md](./v2-4-import-platform-layer-design-note.md)

## 1. Summary

The current code structure is already sufficiently aligned with the v2.4
platform model.
The repository does not need a platform rewrite, a new execution framework, or
major API cleanup to support the new documentation architecture.

Current overall alignment:

- strongly aligned:
  - preflight gate
  - import runtime
  - result intelligence
  - artifact and delivery
- partially aligned:
  - template authoring as a named platform concept
  - lifecycle event terminology at the platform-doc level

The main remaining work is therefore not architectural.
It is minimal alignment work focused on:

- terminology consistency
- clearer entry-point guidance
- small public-surface clarifications where they reduce user confusion
- explicit non-goals to prevent over-engineering

The default rule for this phase is:

- if a problem can be solved by documentation, do not change code
- if a code change only makes the repository look more "architected", do not do
  it

## 2. Alignment Categories

### A. Documentation-only alignment

These issues should be handled by documentation or cross-linking only.

#### A1. Standardize platform-stage vocabulary

Problem:

- docs now use `Template Authoring`, `Preflight Gate`, `Import Runtime`,
  `Result Intelligence`, and `Artifact / Delivery`
- older docs still use narrower or older terms without always connecting them
  back to the platform model

Why documentation-only:

- the implementation is already correct
- the mismatch is conceptual, not behavioral

Recommended handling:

- keep platform-stage labels in platform docs
- keep concrete API names in API/result docs
- add short boundary sentences where confusion is likely

#### A2. Clarify stage labels vs concrete event/API terms

Problem:

- the platform model uses stage labels such as `Rows Processed`
- the runtime emits concrete event names such as `row_processed`

Why documentation-only:

- event semantics are already stable enough
- renaming event payloads would carry compatibility risk and little immediate
  user value

Recommended handling:

- explicitly document:
  - stage name in architecture/runtime docs
  - concrete event name in runtime/API docs

#### A3. Clarify preflight vs import duplication concerns

Problem:

- header validation appears in both preflight and import runtime
- readers may interpret that as accidental duplication

Why documentation-only:

- the duplication is intentional stage separation
- code merging would reduce clarity rather than improve it

Recommended handling:

- continue explaining preflight as cheap structural gating
- continue explaining import as full execution certainty

#### A4. Clarify result intelligence hierarchy

Problem:

- `result intelligence` is a platform umbrella term
- `ImportResult`, `CellErrorMap`, `RowIssueMap`, and remediation payload are
  concrete surfaces

Why documentation-only:

- the code already models this relationship correctly

Recommended handling:

- keep the hierarchy explicit across `docs/public-api.md`,
  `docs/result-objects.md`, and `docs/api-response-cookbook.md`

#### A5. Fix planning and naming drift in planning records

Problem:

- planning records still refer to older platform doc names in some places

Why documentation-only:

- this is pure repository documentation debt

Recommended handling:

- align plan/design-note references to the implemented doc filenames

### B. Low-risk code alignment

These changes are acceptable only if they remain small, additive, and directly
reduce misuse or confusion.

#### B1. Docstring clarification for lifecycle event semantics

Problem:

- event semantics are currently clear in docs, but code-level discoverability is
  thinner

Why low-risk:

- docstrings do not alter runtime behavior
- they help backend integrators reading public or near-public implementation
  surfaces

Possible adjustments:

- clarify on `import_data(..., on_event=...)` that events are additive,
  best-effort runtime projections
- clarify in `ImportSession` comments that emitted event names are concrete
  payload names, not platform-stage labels

#### B2. Public export consistency review for platform docs

Problem:

- some platform-facing docs rely on stable public imports
- small mismatches in exported names or reference emphasis can create confusion

Why low-risk:

- only relevant if a tiny additive export or import-path clarification is needed
- should not introduce new APIs, only make intended usage more discoverable

Possible adjustments:

- verify that platform-facing types and helpers already documented as public are
  consistently surfaced from the package root
- if a documented stable surface is not exported consistently, consider a small
  additive export only if compatibility risk is negligible

Guardrail:

- do not add exports just to make the module graph look cleaner

#### B3. Example alignment where the public teaching story is ambiguous

Problem:

- examples may still teach older terminology or skip the new platform reading
  order

Why low-risk:

- example wording or small example comments can reduce misunderstanding without
  changing runtime behavior

Possible adjustments:

- light alignment in example READMEs or example comments
- no broad example rewrite

### C. Tech debt / future work

These should not be pulled into the minimal alignment patch set.

#### C1. Event vocabulary standardization at the payload level

Deferred issue:

- whether `row_processed` should ever be renamed or complemented by a more
  formal event vocabulary

Why defer:

- this is compatibility-sensitive
- documentation already solves the immediate comprehension problem

#### C2. Broader public naming cleanup for compatibility aliases

Deferred issue:

- older aliases such as `df`, `header_df`, `cell_errors`, and `row_errors`
  remain visible

Why defer:

- 2.x compatibility policy still protects them
- broader cleanup would exceed the v2.4 documentation-first goal

#### C3. Stronger template-authoring code grouping

Deferred issue:

- template authoring is conceptually clear but distributed across several
  modules

Why defer:

- code ownership is already workable
- regrouping would be a structural cleanup, not a minimum alignment task

#### C4. ImportSession orchestration boundary cleanup

Deferred issue:

- import runtime and result-workbook rendering remain adjacent in one session
  flow

Why defer:

- current behavior is coherent
- extracting a cleaner orchestration split would be architecture cleanup, not
  urgent platform alignment

### D. Explicit non-goals

These should not be done in the v2.4 minimal platform alignment phase.

- do not introduce a new runtime framework
- do not redesign `ImportSession` or `ImportExecutor`
- do not add job persistence, queue semantics, or polling protocols
- do not build an async engine around lifecycle events
- do not merge preflight into full import
- do not split `results.py` into new platform-specific public modules
- do not rename stable event payloads for aesthetic consistency alone
- do not remove compatibility aliases as part of this phase
- do not create a new template-authoring subsystem just to mirror doc labels
- do not reorganize `core/` packages to match platform layers

## 3. Recommended Minimal Patch Set

Only the smallest useful set should be considered for execution.

### Patch 1. Finish doc terminology alignment in remaining entry-point docs

Why:

- this provides the biggest comprehension gain at the lowest risk
- it reduces drift between platform docs and repository-facing guidance

Affected files:

- `README.md`
- `README-pypi.md`
- `README_cn.md`
- `docs/public-api.md`
- `docs/result-objects.md`
- `docs/api-response-cookbook.md`
- `docs/domain-model.md`
- `docs/integration-roadmap.md`
- `src/excelalchemy/README.md`

Risk:

- low
- mostly wording and cross-link changes

Verifier:

- manual doc read-through for terminology consistency
- `uv run python scripts/smoke_docs_assets.py`

### Patch 2. Align planning-record filenames and cross-links

Why:

- it removes a known source of confusion with almost no risk

Affected files:

- `plans/v2-4-import-platform-layer-design.md`
- `plans/v2-4-import-platform-layer-design-note.md`
- related tech-debt note if its status wording should be updated

Risk:

- very low

Verifier:

- manual link check
- repository text search for stale platform doc filenames

### Patch 3. Add small code-level docstrings only if discoverability remains weak

Why:

- a tiny amount of code-adjacent explanation can prevent misuse of
  `on_event=...` and reduce confusion around runtime semantics

Affected files:

- `src/excelalchemy/core/alchemy.py`
- `src/excelalchemy/core/import_session.py`

Risk:

- low if limited to docstrings/comments only
- medium if it starts to drift into behavior or event-shape changes

Verifier:

- focused review that no runtime behavior changed
- `uv run ruff check .`
- `uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests`

### Patch 4. Light example and internal-package README alignment if needed

Why:

- examples and internal package guides are part of the teaching surface
- small wording updates can reduce future drift

Affected files:

- `examples/README.md`
- `examples/fastapi_reference/README.md`
- `src/excelalchemy/README.md`

Risk:

- low

Verifier:

- manual review for terminology consistency
- `uv run python scripts/smoke_examples.py`

## 4. Acceptance Criteria

This minimal alignment phase should be considered complete when all of the
following are true:

- The repository has a documented plan that clearly separates:
  - documentation-only alignment
  - low-risk code alignment
  - tech debt
  - explicit non-goals
- The plan concludes that the current code structure already supports the v2.4
  platform model without structural rewrite.
- Remaining documentation updates use one consistent platform vocabulary while
  still naming the concrete public APIs.
- Planning-record filename drift is either fixed in follow-up work or clearly
  tracked as documentation debt.
- Any code changes chosen from this plan are limited to low-risk clarity work
  such as docstrings, public-surface clarification, or example alignment.
- No patch in this phase changes runtime behavior, result payload shapes,
  storage behavior, or compatibility guarantees.
- No patch in this phase introduces a new framework abstraction, async
  execution model, or job-oriented runtime concept.
- The minimal patch set remains easy to review and easy to revert.

## Final Recommendation

The recommended v2.4 alignment strategy is:

1. finish the remaining documentation and cross-link cleanup
2. only then consider tiny code-adjacent clarity improvements
3. defer naming cleanups and structural tidying that are not necessary for user
   understanding
4. explicitly reject framework-like follow-up work in this phase

In short, the repository is already architecturally ready enough.
The next step is disciplined clarification, not additional system design.
