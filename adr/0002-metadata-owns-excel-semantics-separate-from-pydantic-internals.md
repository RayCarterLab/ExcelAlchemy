# ADR 0002: Metadata Owns Excel Semantics, Separate From Pydantic Internals

## Status

- `accepted`
- Inference note: this ADR is inferred from current repository design, documentation, and code layout. No prior ADR file for this decision exists in the repository.

## Context

- The repository treats workbook semantics as a first-class concern:
  - labels
  - order
  - comments and hints
  - options
  - formatting hints
  - import constraints
- The docs describe a shift away from tighter coupling to Pydantic internals, especially during the Pydantic v2 migration.
- The implementation now uses a metadata layer plus a Pydantic adapter boundary rather than making Pydantic field internals the owner of Excel-specific behavior.

## Decision

- Keep Excel-specific semantics in the metadata layer centered on `src/excelalchemy/metadata.py`.
- Keep Pydantic integration behind the adapter layer in `src/excelalchemy/helper/pydantic.py`.
- Preserve `FieldMetaInfo` as the 2.x compatibility-facing metadata object while the internal model remains layered.

## Consequences

- Workbook semantics remain explicit and controlled by ExcelAlchemy rather than by framework internals.
- Framework upgrades are less likely to require invasive changes across the whole runtime path.
- The implementation carries some complexity because the 2.x public surface still exposes `FieldMetaInfo` while internal code is moving toward layered metadata objects.
- Metadata, schema extraction, and validation-message normalization must stay aligned across multiple files.

## Evidence

- `ABOUT.md`
  - explicitly states “Excel Metadata Owns Excel Semantics” and “Pydantic Is an Adapter Boundary”
- `docs/architecture.md`
  - describes metadata as a stable public layer and Pydantic integration as a separate adapter
- `src/excelalchemy/metadata.py`
  - defines `FieldMetaInfo` as a compatibility facade over:
    - `DeclaredFieldMeta`
    - `RuntimeFieldBinding`
    - `WorkbookPresentationMeta`
    - `ImportConstraints`
- `src/excelalchemy/helper/pydantic.py`
  - extracts metadata from Pydantic models and maps validation errors into ExcelAlchemy errors
- `tests/contracts/test_pydantic_contract.py`
  - verifies that Excel metadata stays outside direct `FieldInfo` subclassing and that validation is mapped into `ExcelCellError` and `ExcelRowError`

## Uncertainty

- The repository clearly shows the current separation and its rationale.
- This ADR does not claim that every internal consumer already uses the layered metadata API uniformly; the codebase itself still documents `FieldMetaInfo` as a 2.x compatibility facade.

## Relevant paths

- `ABOUT.md`
- `docs/architecture.md`
- `src/excelalchemy/metadata.py`
- `src/excelalchemy/helper/pydantic.py`
- `tests/contracts/test_pydantic_contract.py`
- `tests/unit/test_field_metadata.py`
