# About ExcelAlchemy

## What Kind of Project This Is

ExcelAlchemy began as a practical response to a recurring backend problem:
Excel was the delivery format, but the real work was template control, validation, data normalization, and row-level feedback.

Over time, this repository became more than a utility library.
It became a place to practice and demonstrate architecture decisions in public:

- how to evolve a codebase without rewriting it from scratch
- how to isolate framework churn behind adapters
- how to remove dependencies that no longer fit the problem
- how to expose extension points without making the API noisy

## Problem Framing

The project is built around one core belief:

> Excel import/export is not a file problem first. It is a contract problem first.

The “file” is only the transport.
The actual system has to answer harder questions:

- What is the expected shape of the data?
- Which fields are required?
- How should users discover valid input?
- Where should validation errors be written back?
- How do we keep backend code and spreadsheet semantics aligned?
- How do we avoid hard-wiring infrastructure choices into business logic?

ExcelAlchemy answers those questions with schema-driven design.

## 23 Design Principles In Practice

1. Prefer explicit schemas over implicit conventions.
2. Keep workbook metadata separate from validation-framework internals.
3. Treat Excel as a contract, not a loosely structured blob.
4. Keep the public API small and boring.
5. Move complexity behind focused internal components.
6. Prefer composition over giant coordinator classes.
7. Put adapters at unstable integration boundaries.
8. Depend on protocols where implementations can vary.
9. Optimize for migration-friendly seams.
10. Avoid hidden runtime magic.
11. Make user-facing failures easy to understand.
12. Keep architecture honest to the real problem domain.
13. Remove dependencies that do not earn their cost.
14. Use modern Python features where they reduce incidental complexity.
15. Prefer typed contracts over stringly typed plumbing.
16. Make storage a strategy, not a product lock-in.
17. Keep tests focused on behavior and contracts.
18. Modernize incrementally, not theatrically.
19. Separate workbook display text from runtime error text.
20. Let internationalization start with message boundaries, not with global complexity.
21. Accept compatibility where it helps adoption, but isolate it.
22. Document tradeoffs, not just outcomes.
23. Build a library that teaches its own architecture.

## Architecture Decisions

### 1. Facade Outside, Components Inside

`ExcelAlchemy` is intentionally a facade.
It exposes the user-facing workflow, but delegates internals to specialized components:

- schema extraction
- header parsing and validation
- row aggregation
- import execution
- rendering
- storage

This lets the public surface stay stable while the inside evolves.

### 2. Excel Metadata Owns Excel Semantics

`FieldMetaInfo` is the center of workbook metadata.
It knows about:

- labels
- ordering
- required-ness
- comments
- option mappings
- date and numeric display constraints

This metadata does not belong to Pydantic internals.
That separation was critical for the Pydantic v2 migration.

### 3. Pydantic Is an Adapter Boundary

The project used to be more tightly coupled to Pydantic implementation details.
Today the approach is different:

- Pydantic models define structure
- ExcelAlchemy extracts model shape through a small adapter layer
- runtime Excel validation remains owned by ExcelAlchemy

This is not “anti-framework”; it is a boundary decision.

### 4. Storage Is a Protocol

Minio is useful, but it is not the architecture.
The architecture is `ExcelStorage`.

That means the system can support:

- Minio-compatible object storage
- local file storage
- in-memory test doubles
- custom backends

without making those choices leak into the core workflow.

### 5. Workbook Display Text Is Different From Runtime Errors

Runtime exceptions are aimed at developers and integrators.
Workbook text is aimed at Excel users.

That is why the project now separates:

- runtime message lookup
- display message lookup

This is a small but meaningful design distinction.

## Major Evolution Steps

### `src/` Layout Migration

The move to `src/excelalchemy` eliminated misleading import behavior from repository-root execution.
That change made packaging and test semantics more honest.

### Pydantic Metadata Decoupling

Before the v2 migration, the dangerous part was not syntax changes.
It was the deeper coupling between Excel metadata and Pydantic field internals.

The metadata layer was pulled apart first.
That reduced migration risk dramatically.

### Pydantic v2 Migration

The migration replaced older patterns with:

- `model_fields`
- `model_validate`
- an adapter layer around field access

The key win was not just “support v2”.
It was making future framework upgrades less invasive.

### Python 3.12-3.14 Modernization

The codebase now uses:

- `type` aliases
- PEP 695 generic syntax in core places
- a tighter modern Python target

This was done after narrowing the support policy.
The syntax decision followed the compatibility decision, not the other way around.

### pandas Removal

`pandas` was mostly acting as a transport layer, not as a data analysis engine.
Replacing it with `openpyxl + WorksheetTable` better matched the actual workload and removed a dependency chain the project did not need.

### Storage Abstraction

Minio support remains available, but the project no longer treats it as the only meaningful storage model.
That shift makes the library more reusable and architecturally cleaner.

### i18n Foundation

Internationalization was intentionally staged:

1. unify runtime errors
2. introduce a message layer
3. move workbook display text onto locale-aware display messages

That sequence avoided premature framework complexity.

## Pydantic v1 vs v2: The Real Difference

| Concern | Earlier coupling risk | Current design |
| --- | --- | --- |
| Field access | direct dependence on internals | adapter over stable v2 APIs |
| Excel metadata | mixed with validation details | owned by `FieldMetaInfo` |
| Custom validation flow | framework-driven | explicitly orchestrated |
| Migration surface | wide | narrowed |

The important lesson is not “v2 is newer”.
The important lesson is that framework upgrades are easier when the framework does not own the whole architecture.

## Why Remove pandas

This project does not need:

- joins
- groupby pipelines
- vectorized analysis
- multi-index machinery

It does need:

- deterministic workbook IO
- cell-level error positioning
- header semantics
- light table manipulation

So the code now uses a table abstraction that matches the problem.
That is a better engineering fit.

## Why `uv`

The switch to `uv` was part of the broader modernization effort:

- faster setup
- simpler CI flow
- clearer local commands
- less tool sprawl

The build backend remains conservative (`flit_core`), while the workflow frontend is modern.
That was an intentional risk balance.

## Tradeoffs

No design here is “free”.
Some deliberate tradeoffs:

- The library favors explicit structure over maximum implicit flexibility.
- Workbook comments and labels are verbose by design because user guidance matters.
- The public API remains smaller than the set of available internal extension points.
- Compatibility is preserved where it reduces migration pain, but older patterns are gradually de-emphasized.

## How To Read This Repository

If you want the shortest path:

1. Start with [README.md](./README.md)
2. Read [docs/architecture.md](./docs/architecture.md)
3. Look at `src/excelalchemy/core/`
4. Then inspect tests under `tests/contracts/`

That path shows both the architecture and the behavioral safety net.

## Final Note

ExcelAlchemy is intentionally opinionated.
It is not trying to be every possible spreadsheet abstraction.
Its goal is narrower and, because of that, stronger:

to make typed Excel workflows explicit, maintainable, and evolvable.
