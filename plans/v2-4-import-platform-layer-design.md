# v2.4 ExcelAlchemy Import Platform Layer Design Plan

Status: `planned`

## Problem Statement

The repository already exposes a meaningful set of import-related capabilities,
but the current documentation still presents them mostly as:

- isolated additive features
- internal components
- result-object details

That leaves a gap at the platform level.

Today, a reader can learn that ExcelAlchemy supports:

- template-side UX metadata
- lightweight structural preflight
- synchronous import lifecycle events
- structured result objects and remediation payloads

But the docs do not yet describe these as one coherent import platform model
with clear before-import, in-import, and after-import responsibilities.

The result is documentation drift risk:

- users may treat preflight, lifecycle events, and remediation as unrelated
  utilities instead of one import workflow story
- architecture docs may over-emphasize internal collaborators and under-explain
  platform capabilities
- public API docs may describe stable surfaces without showing how they compose
  into a recommended integration model

For v2.4, the goal is to make the platform layer explicit in docs and planning
without changing current public behavior.

## Goals

- Define a platform-layer architecture model for the existing import
  capabilities.
- Show how current public surfaces compose into one coherent import workflow.
- Preserve the current additive nature of:
  - template-side UX metadata
  - `preflight_import(...)`
  - `import_data(..., on_event=...)`
  - `ImportResult`, `CellErrorMap`, `RowIssueMap`, and
    `build_frontend_remediation_payload(...)`
- Add a documentation model that sits above internal component architecture.
- Standardize terminology across README, architecture docs, public API docs,
  and result-object docs.
- Keep the design compatible with current 2.x public API and compatibility
  policy.

## Non-goals

- No code implementation in this plan.
- No new public import method, config object, event class, or result type.
- No refactor of `src/excelalchemy/core/`.
- No change to current storage architecture or `ExcelStorage` semantics.
- No result payload shape changes.
- No change to locale policy.
- No background-job, streaming, or async redesign.
- No attempt to merge preflight, execution, and remediation into one overloaded
  API.
- No opportunistic cleanup of unrelated architecture or docs debt.

## Scope

This plan covers:

- platform-layer architecture framing
- documentation structure
- terminology alignment
- diagram planning
- phased rollout guidance for later implementation work

This plan does not itself update any doc other than adding this plan file.

## Current Repository Facts To Preserve

- Template-side UX metadata already exists as additive workbook guidance via
  public metadata declarations.
- Preflight already exists as a lightweight structural gate and is not a
  replacement for full import execution.
- Import lifecycle events already exist as additive synchronous hooks on
  `import_data(...)`.
- Result objects and remediation payloads already exist as post-import
  consumption surfaces.
- Internal architecture docs already describe core collaborators, but they do
  not yet make the platform-level capability model first-class.
- Stable public entry points remain rooted in:
  - `excelalchemy`
  - `excelalchemy.config`
  - `excelalchemy.metadata`
  - `excelalchemy.results`
  - `excelalchemy.exceptions`
  - `excelalchemy.codecs`

## Recommended Platform-Layer Decomposition

The recommended documentation model is a capability-oriented import platform
layer above the existing internal component map.

### 1. Contract Authoring Layer

Responsibility:

- define the workbook contract before upload
- make the template self-explanatory without changing worksheet structure

Current public surfaces:

- `FieldMeta(...)`
- `ExcelMeta(...)`
- template generation methods on `ExcelAlchemy`

Current capability framing:

- schema declaration
- workbook-facing labels and ordering
- additive guidance such as `hint` and `example_value`

Recommended platform name:

- `Contract Authoring`

### 2. Structural Gate Layer

Responsibility:

- answer whether a workbook is structurally importable before full execution

Current public surfaces:

- `ExcelAlchemy.preflight_import(...)`
- `ImportPreflightResult`

Current capability framing:

- sheet existence
- header validity
- lightweight structural validity
- estimated row count

Recommended platform name:

- `Structural Gate`

### 3. Execution And Observability Layer

Responsibility:

- run the real import workflow
- expose additive inline lifecycle visibility without changing the execution
  model

Current public surfaces:

- `ExcelAlchemy.import_data(..., on_event=...)`
- `ImportMode`
- `ImporterConfig.for_create(...)`
- `ImporterConfig.for_update(...)`
- `ImporterConfig.for_create_or_update(...)`

Current capability framing:

- row validation
- callback dispatch
- result-workbook generation
- synchronous lifecycle events

Recommended platform name:

- `Execution and Observability`

### 4. Outcome And Remediation Layer

Responsibility:

- expose machine-readable and UI-friendly post-import outputs
- support API responses, admin review, and retry/remediation flows

Current public surfaces:

- `ImportResult`
- `CellErrorMap`
- `RowIssueMap`
- `build_frontend_remediation_payload(...)`

Current capability framing:

- top-level import outcome
- cell-level issue inspection
- row-level issue summaries
- remediation-oriented payload shaping

Recommended platform name:

- `Outcome and Remediation`

### 5. Cross-cutting Integration Seams

These are not separate import phases, but the platform docs should call them
out as cross-cutting seams:

- `ExcelStorage`
  - input workbook read boundary
  - result workbook upload boundary
- locale
  - workbook-facing display text
  - not a separate platform capability
- result workbook rendering
  - shared bridge between execution failures and user remediation

### Recommended Documentation Rule

Future docs should describe import capabilities in this order:

1. contract authoring
2. structural gate
3. execution and observability
4. outcome and remediation

Then map those capabilities down to internal components such as
`schema.py`, `headers.py`, `import_session.py`, `executor.py`, and
`results.py`.

This keeps the platform story user-facing while preserving the current
component-level architecture docs.

## Proposed New Architecture Docs

### New doc

- `docs/import-platform.md`
  - purpose:
    - define the platform-layer capability model
    - show the before-import / in-import / after-import story
    - link outward to `docs/public-api.md`, `docs/result-objects.md`, and
      `docs/architecture.md`
  - recommended sections:
    - platform overview
    - capability layers
    - public surface by layer
    - internal component mapping
    - integration patterns for backend/API/frontend consumers
    - boundaries and non-goals

### Existing docs to update

- `README.md`
  - add a concise import-platform framing section and point to
    `docs/import-platform.md`
- `docs/architecture.md`
  - split the current content into:
    - platform view
    - component view
  - keep component ownership intact
- `docs/domain-model.md`
  - add platform-layer concepts as first-class domain concepts
- `docs/public-api.md`
  - regroup import-related public surfaces by platform layer
- `docs/result-objects.md`
  - position result objects explicitly as the outcome/remediation layer
- `docs/api-response-cookbook.md`
  - align wording with the platform-layer terminology
- `docs/integration-roadmap.md`
  - add a reading path for platform-oriented integrators
- `src/excelalchemy/README.md`
  - explain which internal modules implement each platform capability

## Terminology To Standardize

Use these terms consistently in v2.4 docs:

- `Import platform layer`
  - the capability-oriented view above internal components
- `Contract authoring`
  - schema declaration plus template-side workbook guidance
- `Template guidance`
  - workbook-facing additive metadata such as `hint` and `example_value`
- `Structural gate`
  - lightweight preflight before full execution
- `Execution and observability`
  - full import plus synchronous lifecycle visibility
- `Outcome and remediation`
  - post-import result objects, issue maps, and remediation payloads
- `Result surfaces`
  - `ImportResult`, `CellErrorMap`, `RowIssueMap`, and related serializers
- `Remediation payload`
  - the additive frontend-oriented payload helper, not the default result
    contract
- `Internal component architecture`
  - `core/*`, helper, renderer, writer, storage resolution, and related
    collaborators

Avoid these documentation drifts:

- describing remediation as part of import execution
- describing lifecycle events as a job system
- describing preflight as validation equivalent to `import_data(...)`
- describing template guidance as a separate template engine
- presenting internal components as the primary platform story for end users

## Suggested Mermaid Diagram Set

The v2.4 docs should converge on a small, reusable diagram set rather than
ad hoc diagrams per page.

### 1. Platform capability map

Purpose:

- show the four platform layers and the cross-cutting seams

Recommended home:

- `docs/import-platform.md`

### 2. Import lifecycle sequence

Purpose:

- show the recommended order:
  - template guidance
  - preflight
  - import execution
  - result consumption
  - remediation

Recommended home:

- `docs/import-platform.md`
- optionally summarized in `README.md`

### 3. Public surface to capability map

Purpose:

- map stable public APIs to each platform layer

Recommended home:

- `docs/public-api.md`

### 4. Capability to internal component map

Purpose:

- map platform layers to current internal modules without changing
  implementation ownership

Recommended home:

- `docs/architecture.md`
- `src/excelalchemy/README.md`

### 5. API and frontend consumption map

Purpose:

- show how `ImportPreflightResult`, `ImportResult`, `CellErrorMap`,
  `RowIssueMap`, and remediation payloads serve backend and frontend flows

Recommended home:

- `docs/result-objects.md`
- `docs/api-response-cookbook.md`

## Docs Likely Affected

Primary docs:

- `README.md`
- `docs/import-platform.md` (new)
- `docs/architecture.md`
- `docs/domain-model.md`
- `docs/public-api.md`
- `docs/result-objects.md`
- `docs/api-response-cookbook.md`
- `docs/integration-roadmap.md`
- `src/excelalchemy/README.md`

Potentially affected, depending on final wording and links:

- `README-pypi.md`
- `examples/README.md`
- `examples/fastapi_reference/README.md`
- `docs/getting-started.md`
- `docs/examples-showcase.md`

## Risks And Open Questions

### Risk: capability overlap wording

Risk:

- docs could blur the boundary between preflight, full import validation, and
  remediation

Mitigation:

- define one short boundary statement per layer
- repeat it consistently across README, platform docs, and result docs

### Risk: platform docs compete with component docs

Risk:

- adding a platform doc could duplicate `docs/architecture.md` instead of
  clarifying it

Mitigation:

- keep `docs/import-platform.md` focused on capabilities and public surfaces
- keep `docs/architecture.md` focused on internal collaborators and ownership

### Risk: accidental API signaling

Risk:

- a platform-layer framing could accidentally imply new abstractions or future
  guarantees that do not exist today

Mitigation:

- anchor every layer in current public APIs only
- mark aspirational follow-up ideas separately in future plans or tech debt

### Risk: terminology churn without implementation benefit

Risk:

- broad wording changes may create unnecessary review noise

Mitigation:

- standardize only the terms needed to describe the current import platform
- avoid renaming stable public APIs

### Open question: one new platform doc or a broader architecture rewrite

Recommendation:

- start with one new `docs/import-platform.md` and targeted edits elsewhere
- avoid a large architecture-doc rewrite in one pass

### Open question: should preflight and result objects stay in separate docs

Recommendation:

- yes
- keep detailed behavior in `docs/result-objects.md`
- use `docs/import-platform.md` to explain where those objects fit in the
  broader workflow

### Open question: should lifecycle events get a dedicated doc

Recommendation:

- not in this phase
- first group them under `Execution and Observability`
- create a dedicated doc later only if examples and integrations grow enough

### Open question: how to handle newly discovered design gaps

Recommendation:

- do not expand v2.4 scope inside the docs pass
- record follow-up gaps in `plans/` or `tech_debt/`

## Phased Implementation Plan

### Phase 1. Approve the platform model

- confirm the four-layer decomposition
- confirm the standardized terminology
- confirm the new-doc strategy centered on `docs/import-platform.md`

### Phase 2. Add the platform-level doc

- create `docs/import-platform.md`
- add the core capability map and lifecycle diagram
- link to existing public API, architecture, and result docs

### Phase 3. Align current docs to the platform model

- update `README.md`
- update `docs/architecture.md`
- update `docs/domain-model.md`
- update `docs/public-api.md`
- update `docs/result-objects.md`
- update `docs/api-response-cookbook.md`
- update `docs/integration-roadmap.md`
- update `src/excelalchemy/README.md`

### Phase 4. Align examples and reading paths only where needed

- update `examples/README.md` and `examples/fastapi_reference/README.md` only
  if the new platform framing materially improves navigation
- avoid example script churn unless the public teaching story is unclear

### Phase 5. Capture follow-up gaps separately

- record any platform/code mismatches in `plans/` or `tech_debt/`
- do not fold unrelated design or code changes into the doc-alignment work

## Acceptance Criteria

- A v2.4 plan exists that defines the import platform layer as a coherent
  architecture and documentation model.
- The plan preserves current public API and 2.x compatibility expectations.
- The recommended decomposition explicitly includes:
  - contract authoring
  - structural gate
  - execution and observability
  - outcome and remediation
- The plan names a concrete new architecture doc:
  - `docs/import-platform.md`
- The plan specifies terminology to standardize across docs.
- The plan specifies a reusable Mermaid diagram set.
- The plan identifies the primary docs likely to be updated.
- The plan records risks and open questions without expanding scope into code
  work.
- The phased plan keeps implementation additive, reviewable, and easy to
  revert.
- The plan makes clear that preflight, lifecycle events, and remediation are
  existing additive capabilities, not new v2.4 runtime features.

## Verification For Later Execution

When implementation begins, validate the documentation pass with:

- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pyright`
- `uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests`
- `uv run python scripts/smoke_package.py`
- `uv run python scripts/smoke_examples.py`
- `uv run python scripts/smoke_docs_assets.py`
- `uv run python scripts/smoke_api_payload_snapshot.py`
