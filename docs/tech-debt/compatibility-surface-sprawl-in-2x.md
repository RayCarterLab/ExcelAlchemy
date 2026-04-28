# Compatibility Surface Sprawl In 2.x

## Summary

The repository maintains the same conceptual surface through both preferred public APIs and multiple 2.x compatibility paths.

## Impact

- Increases maintenance cost across source, docs, and tests.
- Makes navigation noisier because “available” and “recommended” are not the same.
- Requires continued testing and documentation for deprecated import paths and old facade aliases.

## Current workaround

- The repository documents the preferred public modules and names in:
  - `docs/public-api.md`
  - `MIGRATIONS.md`
- Deprecated modules and aliases remain available but emit warnings where applicable.
- Tests explicitly protect the compatibility layer and deprecation guidance.

## Desired fix

- Continue narrowing usage toward the preferred public surface:
  - `excelalchemy`
  - `excelalchemy.config`
  - `excelalchemy.metadata`
  - `excelalchemy.results`
  - `excelalchemy.exceptions`
  - `excelalchemy.codecs`
- Reduce the amount of duplicated compatibility surface that must remain active in the runtime and documentation.
- Keep the deprecation path explicit and easy to remove when the 3.x line allows it.

## Priority

- `medium`

## Evidence

- `docs/public-api.md`
  - distinguishes stable public modules from compatibility modules and internal modules
- `MIGRATIONS.md`
  - states that `excelalchemy.types.*` remains available in 2.x and is scheduled for removal in 3.0
  - documents old vs preferred import-inspection names
- `src/excelalchemy/core/alchemy.py`
  - still exposes compatibility aliases:
    - `df`
    - `header_df`
    - `cell_errors`
    - `row_errors`
- `src/excelalchemy/types/`
  - compatibility namespace retained for migrations
- `src/excelalchemy/exc.py`
- `src/excelalchemy/identity.py`
- `src/excelalchemy/header_models.py`
- `src/excelalchemy/util/convertor.py`
  - compatibility shims still exist in the package
- `tests/unit/test_deprecation_policy.py`
  - verifies that compatibility imports still work and emit replacement guidance

## Uncertainty

- The repository clearly shows that compatibility surface exists and carries cost.
- The exact removal schedule beyond the documented `ExcelAlchemy 3.0` direction is not established here, so this record should not assume a more specific timeline.

## Relevant paths

- `docs/public-api.md`
- `MIGRATIONS.md`
- `src/excelalchemy/core/alchemy.py`
- `src/excelalchemy/types/`
- `src/excelalchemy/exc.py`
- `src/excelalchemy/identity.py`
- `src/excelalchemy/header_models.py`
- `src/excelalchemy/util/convertor.py`
- `tests/unit/test_deprecation_policy.py`
