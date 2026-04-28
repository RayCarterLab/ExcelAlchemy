# ADR 0003: Keep 2.x Compatibility Shims, But Treat Them As A Migration Layer Scheduled For 3.0 Removal

## Status

- `accepted`
- Inference note: this ADR is inferred from current repository design, migration docs, and tests. No prior ADR file for this decision exists in the repository.

## Context

- The repository currently supports both:
  - preferred public modules and names
  - older compatibility import paths and aliases
- The migration and public-API docs explicitly describe this as a 2.x compatibility policy, not the preferred long-term design.
- Tests exist specifically to verify deprecation warnings and replacement guidance.

## Decision

- Keep compatibility shims and alias paths active throughout the 2.x line.
- Treat them as a migration layer rather than as preferred public API.
- Keep deprecation warnings explicit and point users toward the preferred replacements.
- Treat removal as a 3.0 concern rather than removing compatibility paths casually during 2.x maintenance.

## Consequences

- Existing users have a smoother migration path into the newer public module layout.
- The repository must carry extra maintenance cost in source, docs, and tests for deprecated paths.
- Public guidance must continue to distinguish “still works” from “recommended”.
- New code and docs should prefer:
  - `excelalchemy`
  - `excelalchemy.config`
  - `excelalchemy.metadata`
  - `excelalchemy.results`
  - `excelalchemy.exceptions`
  - `excelalchemy.codecs`
  - `storage=...`
  - `worksheet_table`, `header_table`, `cell_error_map`, `row_error_map`

## Evidence

- `docs/public-api.md`
  - explicitly separates stable public modules from compatibility modules
- `MIGRATIONS.md`
  - states that `excelalchemy.types.*` remains available in 2.x and is scheduled for removal in ExcelAlchemy 3.0
  - states that old import-inspection names still work in 2.x but clearer names are preferred
- `docs/agent/architecture-boundaries.md`
  - includes a compatibility policy section for 2.x imports
- `src/excelalchemy/types/`
- `src/excelalchemy/exc.py`
- `src/excelalchemy/identity.py`
- `src/excelalchemy/header_models.py`
- `src/excelalchemy/util/convertor.py`
  - implement the compatibility layer directly in the package
- `tests/unit/test_deprecation_policy.py`
  - verifies deprecation warnings and replacement targets
- `src/excelalchemy/core/alchemy.py`
  - still exposes compatibility property aliases such as `df`, `header_df`, `cell_errors`, and `row_errors`

## Uncertainty

- The repository explicitly documents the 3.0 removal direction for some compatibility paths.
- This ADR does not infer a more detailed deprecation timeline or exact 3.0 scope beyond what is already written in the repository.

## Relevant paths

- `docs/public-api.md`
- `MIGRATIONS.md`
- `docs/agent/architecture-boundaries.md`
- `src/excelalchemy/types/`
- `src/excelalchemy/exc.py`
- `src/excelalchemy/identity.py`
- `src/excelalchemy/header_models.py`
- `src/excelalchemy/util/convertor.py`
- `src/excelalchemy/core/alchemy.py`
- `tests/unit/test_deprecation_policy.py`

