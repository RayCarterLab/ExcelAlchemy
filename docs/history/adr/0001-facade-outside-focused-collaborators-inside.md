# ADR 0001: Facade Outside, Focused Collaborators Inside

## Status

- `accepted`
- Inference note: this ADR is inferred from current repository design, documentation, and code layout. No prior ADR file for this decision exists in the repository.

## Context

- The repository exposes a compact public entry point through `ExcelAlchemy`.
- Internal work is split across focused collaborators for:
  - schema/layout
  - header parsing and validation
  - row aggregation
  - import execution
  - rendering
  - storage
- The repository documentation presents this split as a deliberate architectural shape rather than an accidental implementation detail.

## Decision

- Keep `ExcelAlchemy` as the small public workflow facade.
- Keep major workflow responsibilities in focused internal collaborators under `src/excelalchemy/core/` instead of collapsing them into one large coordinator class.

## Consequences

- The top-level API stays compact and easier to document through `excelalchemy` and the stable public modules.
- Internal workflow components can evolve more independently.
- Behavior changes often require coordinated edits across multiple internal modules and their matching tests.
- Repository navigation depends on clear architecture docs and package-local guidance because the implementation is intentionally distributed.

## Evidence

- `ABOUT.md`
  - explicitly names “Facade Outside, Components Inside” as an architecture decision
- `docs/agent/architecture-boundaries.md`
  - maps `ExcelAlchemy` to `ExcelSchemaLayout`, `ExcelHeaderParser`, `ExcelHeaderValidator`, `RowAggregator`, `ImportExecutor`, `ExcelRenderer`, and `ExcelStorage`
- `src/excelalchemy/core/alchemy.py`
  - keeps the facade methods and delegates core work to collaborators
- `src/excelalchemy/core/schema.py`
- `src/excelalchemy/core/headers.py`
- `src/excelalchemy/core/rows.py`
- `src/excelalchemy/core/executor.py`
- `src/excelalchemy/core/rendering.py`
- `src/excelalchemy/core/storage.py`

## Uncertainty

- The repository strongly supports this decision as the current design.
- This ADR does not claim to reconstruct the original chronological discussion that led to it; it only records the decision as it is visible today.

## Relevant paths

- `ABOUT.md`
- `docs/agent/architecture-boundaries.md`
- `src/excelalchemy/core/alchemy.py`
- `src/excelalchemy/core/schema.py`
- `src/excelalchemy/core/headers.py`
- `src/excelalchemy/core/rows.py`
- `src/excelalchemy/core/executor.py`
- `src/excelalchemy/core/rendering.py`
- `src/excelalchemy/core/storage.py`

