# v2.4 Import Platform Layer Design Note

Status: `planned`

Related plan:

- [v2-4-import-platform-layer-design.md](./v2-4-import-platform-layer-design.md)

## Current Repository State

The repository already has the main pieces needed for an import platform story.
The gap is mostly documentation shape, not missing architecture.

Current alignment points:

- the facade already separates full import from preflight:
  - `ExcelAlchemy.import_data(...)`
  - `ExcelAlchemy.preflight_import(...)`
- preflight already has a dedicated internal path:
  - `src/excelalchemy/core/preflight.py`
- full import already has a dedicated runtime owner:
  - `src/excelalchemy/core/import_session.py`
- template-side guidance already lives in the public metadata layer:
  - `FieldMeta(...)`
  - `ExcelMeta(...)`
  - `WorkbookPresentationMeta`
- post-import consumption already lives in one public results layer:
  - `ImportPreflightResult`
  - `ImportResult`
  - `CellErrorMap`
  - `RowIssueMap`
  - `build_frontend_remediation_payload(...)`
- the main drift is doc-level:
  - `README.md` already tells an import workflow story
  - `docs/architecture.md` still centers internal collaborators
  - `docs/public-api.md` lists stable surfaces without fully grouping them as
    one platform model
  - `docs/result-objects.md` explains outcomes well, but not as one layer in a
    larger platform architecture

That means v2.4 should be documentation architecture consolidation, not a
system rewrite.

## Recommended Documentation Architecture

### Recommended decomposition

The cleanest platform-layer decomposition of the current system is four primary
capability layers plus three cross-cutting seams.

#### 1. Contract Authoring

Responsibility:

- define the workbook contract before upload
- make generated templates self-explanatory

Public surfaces:

- schema models
- `FieldMeta(...)`
- `ExcelMeta(...)`
- template generation methods on `ExcelAlchemy`

Internal alignment:

- `src/excelalchemy/metadata.py`
- `src/excelalchemy/core/schema.py`
- `src/excelalchemy/core/rendering.py`
- `src/excelalchemy/core/writer.py`
- `src/excelalchemy/codecs/`

#### 2. Structural Gate

Responsibility:

- answer whether a workbook is structurally importable before full execution

Public surfaces:

- `ExcelAlchemy.preflight_import(...)`
- `ImportPreflightResult`

Internal alignment:

- `src/excelalchemy/core/preflight.py`
- `src/excelalchemy/core/headers.py`
- `src/excelalchemy/core/schema.py`
- `src/excelalchemy/core/storage_protocol.py`

#### 3. Execution and Observability

Responsibility:

- run the real import workflow
- expose synchronous lifecycle visibility without introducing a job framework

Public surfaces:

- `ExcelAlchemy.import_data(..., on_event=...)`
- `ImporterConfig.for_create(...)`
- `ImporterConfig.for_update(...)`
- `ImporterConfig.for_create_or_update(...)`
- `ImportMode`

Internal alignment:

- `src/excelalchemy/core/import_session.py`
- `src/excelalchemy/core/executor.py`
- `src/excelalchemy/core/rows.py`
- `src/excelalchemy/helper/pydantic.py`

#### 4. Outcome and Remediation

Responsibility:

- expose the outcome of one import run for API, admin, and frontend consumers
- support remediation flows after the import, not during it

Public surfaces:

- `ImportResult`
- `CellErrorMap`
- `RowIssueMap`
- `build_frontend_remediation_payload(...)`

Internal alignment:

- `src/excelalchemy/results.py`
- `src/excelalchemy/core/rendering.py`
- `src/excelalchemy/core/writer.py`
- issue production paths in `src/excelalchemy/core/rows.py` and
  `src/excelalchemy/core/executor.py`

#### Cross-cutting seams

These should be documented as seams, not as top-level phases:

- `ExcelStorage`
  - workbook input and workbook output boundary
- locale
  - workbook-facing text policy
- result workbook rendering
  - bridge between failed execution and user remediation

### Internal architecture docs vs platform architecture docs

These two doc types should differ on purpose.

#### Platform architecture docs should answer:

- what capabilities exist in the import platform
- when each capability is used in the workflow
- which public APIs belong to each capability
- how backend and frontend integrators should think about the flow

Platform docs should emphasize:

- capability boundaries
- lifecycle order
- public surfaces
- integration patterns

Platform docs should avoid:

- file-by-file module ownership detail
- deep internal collaborator sequencing
- compatibility inventory beyond brief guardrails

#### Internal architecture docs should answer:

- which modules own each behavior
- how collaborators interact at runtime
- where to edit when behavior changes
- which internal seams are stable enough to preserve

Internal docs should emphasize:

- `core/*`, `helper/*`, `i18n/*`, `_primitives/*`
- component responsibilities
- change-impact mapping
- extension boundaries

Internal docs should avoid:

- retelling the high-level import platform story as if end users are the main
  audience

### Official top-level concepts

These should become the official top-level concepts in v2.4 docs:

- `Import platform`
- `Contract authoring`
- `Template guidance`
- `Structural gate`
- `Execution`
- `Observability`
- `Outcome surfaces`
- `Remediation payload`
- `Storage seam`

Recommended usage rules:

- use `Contract authoring` for schema and template-facing guidance
- use `Template guidance` for additive workbook metadata such as `hint` and
  `example_value`
- use `Structural gate` for `preflight_import(...)` only
- use `Execution` for the full import path
- use `Observability` for `on_event=...` only
- use `Outcome surfaces` for `ImportResult`, `CellErrorMap`, and `RowIssueMap`
- use `Remediation payload` only for the opt-in helper, not for all result
  payloads
- use `Storage seam` for `ExcelStorage`, not as an import phase

Terms to avoid as top-level concepts:

- `job-friendly import`
- `pre-validation` as a synonym for the whole import system
- `frontend payloads` as the umbrella name for all result objects
- `internal architecture` as the primary reader-facing story

### Which docs should remain, split, or mainly be relinked

#### Should remain as distinct docs

- `docs/public-api.md`
  - still the stable-boundary reference
- `docs/result-objects.md`
  - still the detailed result and payload reference
- `docs/api-response-cookbook.md`
  - still the response-shape cookbook
- `docs/domain-model.md`
  - still the named-concepts reference
- `src/excelalchemy/README.md`
  - still the internal package guide
- `docs/integration-roadmap.md`
  - still the role-based reading map

#### Should be split in responsibility

- `docs/architecture.md`
  - should stop carrying both the platform story and the internal component
    story
  - recommended split:
    - new `docs/import-platform.md` for capability-layer architecture
    - retained `docs/architecture.md` for internal component architecture

#### Should mainly be relinked and lightly reframed

- `README.md`
  - keep short platform summary, then relink to `docs/import-platform.md`
- `docs/getting-started.md`
  - keep onboarding focus, then relink to platform/result docs
- `docs/integration-roadmap.md`
  - keep as reading-path map; mostly relink to the new platform doc
- `docs/examples-showcase.md`
  - keep visual/examples role; mainly relink rather than absorb architecture
- `README-pypi.md`
  - keep concise; mostly relink, do not expand architecture detail
- `examples/README.md`
  - keep example navigation role; only minor relinking if needed

### Mermaid diagrams that are most useful

Use three canonical diagrams and reuse them rather than inventing many
near-duplicates.

#### 1. Capability-layer view

Purpose:

- explain the platform model at a glance

Recommended content:

- `Contract authoring`
- `Structural gate`
- `Execution and observability`
- `Outcome and remediation`
- side seams:
  - `ExcelStorage`
  - `Locale`
  - `Result workbook rendering`

Recommended home:

- `docs/import-platform.md`

#### 2. Runtime sequence view

Purpose:

- show the runtime order without exposing internal component detail first

Recommended sequence:

1. author schema and template guidance
2. generate template
3. upload workbook
4. run structural gate
5. run full import execution
6. emit lifecycle events during execution
7. produce result workbook and result surfaces
8. optionally build remediation payload

Recommended home:

- `docs/import-platform.md`
- optionally summarized in `README.md`

#### 3. Integration blueprint view

Purpose:

- show how backend/API/frontend consumers connect to the platform surfaces

Recommended nodes:

- backend service
- `ExcelAlchemy`
- `ExcelStorage`
- spreadsheet user / uploaded workbook
- API response builder
- frontend/admin UI
- `ImportPreflightResult`
- `ImportResult`
- `CellErrorMap`
- `RowIssueMap`
- remediation payload

Recommended home:

- `docs/import-platform.md`
- `docs/api-response-cookbook.md`
- `docs/result-objects.md`

## Code Structure That Already Aligns And Should Not Be Refactored

These current boundaries already fit the proposed platform model well enough:

- `src/excelalchemy/core/alchemy.py`
  - one facade that exposes both preflight and full import
- `src/excelalchemy/core/preflight.py`
  - dedicated structural-gate path
- `src/excelalchemy/core/import_session.py`
  - dedicated runtime owner for full import and lifecycle events
- `src/excelalchemy/results.py`
  - one public outcome/remediation surface
- `src/excelalchemy/metadata.py`
  - already layered for declaration, presentation, and import constraints
- `src/excelalchemy/helper/pydantic.py`
  - already isolates the Pydantic boundary
- `src/excelalchemy/core/storage_protocol.py`
  - already models storage as a seam instead of a product decision
- `src/excelalchemy/core/rendering.py` and `src/excelalchemy/core/writer.py`
  - already centralize workbook output concerns

Specific non-refactor guidance:

- do not merge preflight into `ImportSession`
- do not split `results.py` into new platform-specific public modules
- do not move template guidance out of `metadata.py`
- do not turn lifecycle events into a separate execution framework
- do not revisit compatibility-only modules as part of this documentation work

## One Rejected Alternative

### Rejected option

Use `docs/architecture.md` as the single umbrella document for both:

- user-facing platform architecture
- internal component architecture
- API integration story
- result-surface story

### Why reject it

This would keep the repository in the same ambiguous state:

- the platform view would remain mixed with implementation detail
- the internal component map would keep competing with the public workflow story
- readers would still need to jump between sections to understand whether they
  were reading:
  - a capability model
  - an implementation map
  - an integration guide

It also creates maintenance pressure:

- every new import-facing capability would enlarge one already overloaded page
- diagrams would keep drifting between audiences
- `README.md`, `docs/public-api.md`, and `docs/result-objects.md` would still
  need to restate architecture context anyway

The cleaner design is:

- new `docs/import-platform.md` for capability architecture
- retained `docs/architecture.md` for internal component architecture

## Exact Scope Boundaries

### In scope

- define the platform-layer decomposition
- define the doc boundary between platform architecture and internal
  architecture
- define official top-level terms
- define which docs remain, split, or mainly relink
- define the canonical Mermaid diagram set
- identify code structure that already aligns and should stay put
- document later file targets for the docs pass

### Out of scope

- code implementation
- public API additions or renames
- result payload changes
- `src/excelalchemy/core/` refactors
- async/job framework design
- storage redesign
- compatibility cleanup
- locale-policy changes
- example-script rewrites unless a doc update clearly requires them
- broad movement of content into new doc trees beyond the one new platform doc

## Likely File Change Checklist

### New doc

- [ ] `docs/import-platform.md`

### Docs to update directly

- [ ] `README.md`
- [ ] `docs/architecture.md`
- [ ] `docs/domain-model.md`
- [ ] `docs/public-api.md`
- [ ] `docs/result-objects.md`
- [ ] `docs/api-response-cookbook.md`
- [ ] `docs/integration-roadmap.md`
- [ ] `src/excelalchemy/README.md`

### Docs likely limited to relinking or light wording updates

- [ ] `docs/getting-started.md`
- [ ] `docs/examples-showcase.md`
- [ ] `examples/README.md`
- [ ] `examples/fastapi_reference/README.md`
- [ ] `README-pypi.md` only if the public doc map changes should be reflected

### Files that should usually stay untouched in this phase

- [ ] `src/excelalchemy/core/alchemy.py`
- [ ] `src/excelalchemy/core/preflight.py`
- [ ] `src/excelalchemy/core/import_session.py`
- [ ] `src/excelalchemy/results.py`
- [ ] `src/excelalchemy/metadata.py`
- [ ] compatibility modules under `src/excelalchemy/types/`

### Smoke and asset files only if doc references change materially

- [ ] `scripts/smoke_docs_assets.py`
- [ ] `scripts/generate_example_output_assets.py` only if example capture links change
- [ ] `files/example-outputs/` only if doc-visible examples intentionally change

## Verifier Checklist

- [ ] The new design note clearly separates platform architecture from internal
      component architecture.
- [ ] The recommended decomposition uses current public capabilities rather than
      proposing a new runtime model.
- [ ] The official top-level concepts are few, reusable, and consistent with
      existing docs.
- [ ] The recommendation introduces only one new primary architecture doc:
      `docs/import-platform.md`.
- [ ] `docs/architecture.md` remains the internal/component architecture
      reference.
- [ ] `docs/result-objects.md` remains the detailed result reference rather than
      being absorbed into the platform doc.
- [ ] The recommended Mermaid set includes:
      capability-layer view, runtime sequence view, integration blueprint view.
- [ ] The design note explicitly identifies modules that already align and
      should not be refactored.
- [ ] The scope boundaries exclude code redesign, job frameworks, compatibility
      cleanup, and broad refactors.
- [ ] The likely file checklist is documentation-first and additive.

## Final Recommendation

For v2.4, the cleanest design is a documentation architecture with one new
platform-level doc and no architectural rewrite:

- add `docs/import-platform.md` as the capability-layer architecture page
- keep `docs/architecture.md` as the internal component map
- keep `docs/public-api.md`, `docs/result-objects.md`, and
  `docs/api-response-cookbook.md` as separate reference docs
- standardize the top-level concepts around contract authoring, structural
  gate, execution, observability, and outcome/remediation
- treat current code structure as already aligned enough to support this model
  without refactoring

This gives the repository one explicit import platform story while preserving
the current public API, compatibility posture, and internal architecture seams.
