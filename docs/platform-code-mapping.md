# Platform-to-Code Mapping

This page maps the v2.4 `Import Platform Layer` vocabulary to the current
ExcelAlchemy 2.x code structure.

It does not propose a rewrite.
It answers a narrower question:

> Does the current code structure already support the v2.4 platform model?

The short answer is yes, mostly through existing facade, session, metadata,
results, and storage seams.
The main remaining gaps are naming alignment and a few boundaries that are
clearer in the documentation model than they are in the code layout.

Use this page together with:

- [`docs/platform-architecture.md`](platform-architecture.md)
- [`docs/runtime-model.md`](runtime-model.md)
- [`docs/public-api.md`](public-api.md)

## Assessment Summary

| Platform area | Primary code owners | Status |
| --- | --- | --- |
| Template Authoring Layer | `metadata.py`, `core/schema.py`, `core/rendering.py`, `core/writer.py`, `core/alchemy.py`, `codecs/` | partially aligned |
| Preflight Gate Layer | `core/preflight.py`, `core/headers.py`, `core/alchemy.py`, `results.py`, `core/storage_protocol.py` | fully aligned |
| Import Runtime Layer | `core/alchemy.py`, `core/import_session.py`, `core/rows.py`, `core/executor.py`, `helper/pydantic.py`, `core/schema.py` | fully aligned |
| Lifecycle Events | `core/import_session.py`, facade entry at `core/alchemy.py` | partially aligned |
| Result Intelligence Layer | `results.py`, `core/rows.py`, `core/import_session.py`, `core/executor.py` | fully aligned |
| Artifact / Delivery Layer | `artifacts.py`, `core/storage_protocol.py`, `core/storage.py`, `core/storage_minio.py`, `core/rendering.py`, `core/writer.py` | fully aligned |

The platform model is therefore already supportable without a broad code
refactor.
The largest mismatch is not missing behavior.
It is that some platform concepts span several modules while the code still
uses older or lower-level names.

## 1. Platform Layers to Code Modules

### Template Authoring Layer

Platform responsibility:

- define the workbook contract before upload
- attach workbook-facing guidance such as `hint` and `example_value`
- generate template workbooks from schema metadata

Primary code modules:

- `src/excelalchemy/metadata.py`
  - owns declared field metadata and workbook presentation metadata
  - contains `FieldMeta(...)`, `ExcelMeta(...)`, `FieldMetaInfo`,
    `WorkbookPresentationMeta`
- `src/excelalchemy/core/schema.py`
  - derives the runtime schema layout used for headers and field ordering
- `src/excelalchemy/codecs/`
  - owns field-level formatting and parsing behavior used when templates are
    rendered
- `src/excelalchemy/core/rendering.py`
- `src/excelalchemy/core/writer.py`
  - render workbook outputs
- `src/excelalchemy/core/alchemy.py`
  - exposes template-facing facade methods such as
    `download_template(...)` and `download_template_artifact(...)`

Public API entry points:

- `excelalchemy.FieldMeta`
- `excelalchemy.ExcelMeta`
- `excelalchemy.ExcelAlchemy.download_template`
- `excelalchemy.ExcelAlchemy.download_template_artifact`

Implementation status:

- `partially aligned`

Why:

- the capability exists and is stable
- the metadata model already cleanly expresses workbook guidance
- the code is not organized under a single explicit "template authoring"
  package or subsystem
- template authoring is distributed across metadata, schema layout, codecs,
  rendering, and facade entry points

### Preflight Gate Layer

Platform responsibility:

- make a lightweight structural decision before full import execution

Primary code modules:

- `src/excelalchemy/core/preflight.py`
  - dedicated read-only structural preflight workflow
- `src/excelalchemy/core/headers.py`
  - header extraction and validation
- `src/excelalchemy/core/alchemy.py`
  - public `preflight_import(...)` entry point
- `src/excelalchemy/results.py`
  - `ImportPreflightResult`, `ImportPreflightStatus`
- `src/excelalchemy/core/storage_protocol.py`
  - workbook read seam through `ExcelStorage`

Public API entry points:

- `excelalchemy.ExcelAlchemy.preflight_import`
- `excelalchemy.ImportPreflightResult`

Implementation status:

- `fully aligned`

Why:

- there is already a dedicated preflight path
- its contract is structurally scoped rather than overloaded with runtime
  execution
- the code boundary closely matches the platform concept

### Import Runtime Layer

Platform responsibility:

- execute the real import path
- validate and transform workbook rows
- dispatch create, update, or create-or-update behavior

Primary code modules:

- `src/excelalchemy/core/alchemy.py`
  - public `import_data(...)` facade entry point
- `src/excelalchemy/core/import_session.py`
  - one-shot import run orchestration and session state
- `src/excelalchemy/core/rows.py`
  - row aggregation and issue tracking
- `src/excelalchemy/core/executor.py`
  - row execution boundary
- `src/excelalchemy/helper/pydantic.py`
  - Pydantic adaptation boundary
- `src/excelalchemy/core/schema.py`
  - runtime layout contract used during header and row processing

Public API entry points:

- `excelalchemy.ExcelAlchemy.import_data`
- `excelalchemy.ImporterConfig`
- `excelalchemy.ImportMode`

Implementation status:

- `fully aligned`

Why:

- the runtime already has a clear execution path
- import orchestration is concentrated in `ImportSession`
- the platform description maps directly to existing runtime behavior rather
  than needing a new engine

### Lifecycle Events

Platform responsibility:

- expose a lightweight operational view of a running import

Primary code modules:

- `src/excelalchemy/core/import_session.py`
  - owns event emission and event payload shapes
- `src/excelalchemy/core/alchemy.py`
  - exposes `on_event` on the public facade

Current event vocabulary in code:

- `started`
- `header_validated`
- `row_processed`
- `completed`
- `failed`

Implementation status:

- `partially aligned`

Why:

- the capability exists and is useful
- event emission is already additive and correctly scoped to the synchronous
  runtime
- naming drift remains:
  - the platform/runtime docs use `rows_processed` as the stage concept
  - the code emits repeated `row_processed` events
- the runtime semantics are sound, but the top-level event model is still
  closer to implementation detail than to a formally standardized platform
  vocabulary

### Result Intelligence Layer

Platform responsibility:

- expose structured post-run outcomes for API, admin, and frontend consumers

Primary code modules:

- `src/excelalchemy/results.py`
  - owns `ImportResult`, `CellErrorMap`, `RowIssueMap`,
    `build_frontend_remediation_payload(...)`
- `src/excelalchemy/core/rows.py`
  - owns issue collection and row aggregation helpers that feed result objects
- `src/excelalchemy/core/import_session.py`
  - assembles final import outcomes and artifact URL handling
- `src/excelalchemy/core/executor.py`
  - contributes row execution outcomes that populate issue maps

Public API entry points:

- `excelalchemy.ImportResult`
- `excelalchemy.CellErrorMap`
- `excelalchemy.RowIssueMap`
- `excelalchemy.build_frontend_remediation_payload`

Implementation status:

- `fully aligned`

Why:

- the code already has stable result surfaces
- remediation payloads are clearly additive on top of those surfaces
- this area is one of the strongest matches between the v2.4 platform model
  and the current codebase

### Artifact / Delivery Layer

Platform responsibility:

- package and deliver generated workbook artifacts
- keep storage concerns behind a stable seam

Primary code modules:

- `src/excelalchemy/artifacts.py`
  - artifact wrapper surface
- `src/excelalchemy/core/storage_protocol.py`
  - public `ExcelStorage` protocol seam
- `src/excelalchemy/core/storage.py`
  - storage gateway construction
- `src/excelalchemy/core/storage_minio.py`
  - legacy/default concrete implementation path
- `src/excelalchemy/core/rendering.py`
- `src/excelalchemy/core/writer.py`
  - workbook rendering for template and result outputs
- `src/excelalchemy/core/alchemy.py`
  - facade upload and artifact-return methods

Public API entry points:

- `excelalchemy.ExcelStorage`
- `excelalchemy.ExcelArtifact`
- artifact-returning facade methods
- result workbook URL on `ImportResult`

Implementation status:

- `fully aligned`

Why:

- the storage seam already exists as a public extension point
- artifact generation is already separated from business-row execution
- the platform model accurately describes existing delivery behavior

## 2. Layer-by-Layer Alignment Notes

### Fully aligned areas

These layers already map cleanly to current code and should not be broadly
refactored for the sake of the v2.4 model:

- Preflight Gate Layer
- Import Runtime Layer
- Result Intelligence Layer
- Artifact / Delivery Layer

These areas already have:

- a real implementation boundary
- stable public entry points
- enough conceptual separation to support the platform docs

### Partially aligned areas

These layers are valid in the platform model, but the code expresses them in a
more distributed or lower-level way:

- Template Authoring Layer
- Lifecycle Events

These do not require immediate refactoring.
They mainly require consistent terminology and careful documentation.

### Misaligned areas

No platform layer is fundamentally misaligned.
The repository does not need a system rewrite to support the v2.4 platform
model.

The current issues are mostly:

- naming drift
- concept overlap between old and new doc vocabulary
- some public surfaces that still expose lower-level runtime terms

## 3. Important Inconsistencies

### Naming inconsistency

#### Event-stage naming drift

Observed:

- docs describe the runtime stage as `rows_processed`
- code emits repeated `row_processed` events

Why it matters:

- the platform model wants a stage-level concept
- the code surface currently exposes a per-row progress event name

Suggested direction:

- standardize the documentation hierarchy as:
  - `Rows Processed` for the platform/runtime stage
  - `row_processed` for the concrete event payload currently emitted
- avoid changing code unless event naming standardization becomes a deliberate
  compatibility decision

#### Result-language overlap

Observed:

- platform docs use `Result Intelligence Layer`
- existing code and older docs use `ImportResult`, `result objects`,
  `CellErrorMap`, `RowIssueMap`, and `remediation payload`

Why it matters:

- `result intelligence` is a useful top-level platform phrase
- it can be misread as a new subsystem rather than a doc-level umbrella term

Suggested direction:

- keep `Result Intelligence Layer` as the platform-stage label
- keep `ImportResult`, `CellErrorMap`, `RowIssueMap`, and remediation payload
  as the concrete implementation terms

#### Template naming remains implicit

Observed:

- the code has strong metadata and template-rendering capability
- it does not use one explicit code-level name such as `template authoring`

Why it matters:

- the platform concept is accurate
- the implementation ownership is spread across metadata, schema, codec, and
  rendering modules

Suggested direction:

- keep the platform term in docs
- map it explicitly to metadata plus rendering rather than trying to create a
  new subsystem name in code

### Concept duplication

#### Header validation appears in both preflight and import runtime

Observed:

- preflight validates headers
- import runtime also validates headers

Why it matters:

- this can look like duplication
- in practice it is intentional stage separation rather than accidental
  duplication

Suggested direction:

- document it as two distinct uses of the same header contract:
  - preflight for cheap structural gating
  - runtime for execution-time certainty
- do not merge the two paths just for conceptual neatness

#### Result and remediation surfaces overlap by design

Observed:

- `ImportResult`, `CellErrorMap`, `RowIssueMap`, and remediation payload all
  describe the same run at different levels

Why it matters:

- without documentation, integrators may not know which one is primary

Suggested direction:

- consistently describe the relationship as:
  - `ImportResult` = top-level outcome
  - maps = detailed stable inspection surfaces
  - remediation payload = frontend-oriented projection

### Blurry boundaries

#### Template authoring spans public and internal structures

Observed:

- public users interact with `FieldMeta(...)`, `ExcelMeta(...)`, and facade
  template methods
- implementation ownership spans `metadata.py`, schema layout, codecs, and
  rendering internals

Why it matters:

- the platform concept is clean
- the code boundary is not represented by one obvious implementation module

Suggested direction:

- keep docs explicit that template authoring is a composed capability, not a
  single subsystem

#### Import runtime and artifact rendering meet inside one session flow

Observed:

- `ImportSession` both executes rows and, on failure, renders/uploads the
  result workbook

Why it matters:

- platform docs distinguish runtime from artifact/delivery
- code keeps them adjacent in the same orchestration path

Suggested direction:

- document this as orchestration convenience, not as a conceptual collapse of
  the layers
- avoid refactoring unless artifact delivery needs independent lifecycle or
  policy later

### API awkwardness

#### Public facade naming still mixes new and compatibility terms

Observed:

- newer docs prefer `worksheet_table`, `header_table`, `cell_error_map`,
  `row_error_map`
- compatibility aliases still expose `df`, `header_df`, `cell_errors`,
  `row_errors`

Why it matters:

- the platform model prefers clearer names
- the code intentionally preserves 2.x compatibility

Suggested direction:

- keep documenting the clearer names first
- keep the compatibility aliases documented as compatibility-only surfaces

#### Runtime is synchronous in behavior but `import_data(...)` is async in API shape

Observed:

- platform docs correctly describe the runtime as synchronous-first in behavior
- the public import method is `async` and awaits inline execution

Why it matters:

- integrators may overread this as a job or background execution model

Suggested direction:

- keep describing the runtime as synchronous-first at the library execution
  level
- make it explicit that the coroutine shape does not imply a separate async job
  architecture

## 4. Recommendations

These are documentation and naming recommendations only.
They are not implementation tasks.

### Recommendation 1

Keep the v2.4 platform model as a documentation architecture layered above the
existing code structure.

Reason:

- the code already supports the model
- forcing a one-to-one package reorganization would add churn without improving
  user-facing clarity

### Recommendation 2

Treat `Result Intelligence Layer` and `Template Authoring Layer` as top-level
documentation concepts, not as required new module names.

Reason:

- these concepts are useful for integrators
- the code already implements them across stable existing modules

### Recommendation 3

Standardize the distinction between stage labels and concrete API/event terms.

Recommended pattern:

- platform stage: `Rows Processed`
- concrete event: `row_processed`
- platform stage: `Result Intelligence`
- concrete surfaces: `ImportResult`, `CellErrorMap`, `RowIssueMap`,
  remediation payload

Reason:

- this preserves clarity without forcing compatibility-sensitive renames

### Recommendation 4

Use this page as the human platform-to-code bridge. Agent-facing ownership rules
live in `docs/agent/architecture-boundaries.md`.

Reason:

- internal architecture docs and platform docs serve different readers
- merging them would make both less clear

### Recommendation 5

Do not refactor the storage boundary to fit the platform wording more tightly.

Reason:

- `ExcelStorage` already provides the correct seam
- the artifact/delivery layer is already well represented in code

## 5. What Already Aligns Well Enough

The following code structure already supports the v2.4 platform model well
enough and should not be refactored just to mirror the docs:

- `ExcelAlchemy` facade methods as the main user-facing composition surface
- `ImportPreflight` as a distinct structural gate
- `ImportSession` as the one-shot import runtime orchestrator
- `results.py` as the stable result surface module
- `ExcelStorage` as the delivery and workbook-access seam
- metadata layering in `metadata.py`, especially:
  - `DeclaredFieldMeta`
  - `WorkbookPresentationMeta`
  - `ImportConstraints`
- compatibility aliases that preserve 2.x behavior

These areas already give the repository the implementation support needed for
the new platform documentation model.

## 6. Bottom Line

The current code structure already supports the v2.4 platform model.

More precisely:

- the implementation is already capable enough
- the public API already exposes the critical platform surfaces
- the main work is conceptual alignment, not subsystem redesign

The codebase is therefore:

- not in need of a platform rewrite
- not blocked by major structural gaps
- mainly in need of terminology discipline and clearer platform-to-code
  mapping
