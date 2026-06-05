# 2026-06-05 Pydantic v2 requiredness semantics

## Problem

A Pydantic ecosystem review found that `PydanticFieldAdapter.required` in
`src/excelalchemy/adapters/pydantic.py` treated nullable annotations as workbook
optional:

```text
Annotated[str | None, ExcelColumn(...)] -> required=False
```

That disagreed with Pydantic v2. In Pydantic v2, `T | None` allows `None` as a
value but does not make the field optional. A field is optional only when
Pydantic reports it as not required, usually because a default exists.

## Evidence

Local probes against the locked runtime showed:

- `model_fields['email'].is_required() == True` for
  `email: Annotated[str | None, ExcelColumn(...)]`
- old ExcelAlchemy metadata reported `required == False`
- missing data still failed later with `This field is required`

Relevant files:

- `src/excelalchemy/adapters/pydantic.py`
- `tests/contracts/test_pydantic_contract.py`
- `docs/agent/invariants.md`
- `docs/domain-model.md`

## Clarified Constraint

The user clarified that ExcelAlchemy 3.0 has no compatibility burden for the old
behavior. The correct 3.0 contract is direct alignment with Pydantic v2.

The user also agreed that import-mode handling of missing worksheet values must
remain a runtime policy concern, not a schema declaration shortcut:

- schema declaration answers whether the Pydantic field is required
- `MISSING_VALUE_IMPORT_POLICY` answers how missing worksheet values are
  represented for each import mode

## Decision

ExcelAlchemy 3.0 requiredness follows Pydantic v2 semantics:

- `T | None` means nullable, not optional.
- a field is optional only when `FieldInfo.is_required()` is false, unless
  `ExcelColumn(required=...)` explicitly overrides workbook-facing
  requiredness.
- explicit `ExcelColumn(required=False)` is allowed as a workbook-facing
  override for ordinary fields.
- `unique=True` and `is_primary_key=True` remain required invariants. They must
  not be combined with `required=False`.
- `None` value handling is separate from requiredness: if the field is present
  and the annotation allows `None`, `None` is a valid value.
- missing worksheet value behavior remains owned by
  `MISSING_VALUE_IMPORT_POLICY`.

Future agents must not reintroduce `not allows_none` as the requiredness rule.

## Implementation Status

Implemented and pushed in commit:

```text
325a90f fix: 对齐 Pydantic v2 requiredness 语义
```

Implementation summary:

- `PydanticFieldAdapter.required` now uses `self.raw_field.is_required()`.
- `PydanticFieldAdapter.validate_value` allows `None` based on `allows_none`,
  independent of field requiredness.
- `unique=True` / `is_primary_key=True` plus `required=False` now raises
  `ProgrammaticError`.
- contract tests cover nullable required fields, nullable fields with defaults,
  workbook-facing required overrides, and unique/required conflicts.
- agent/domain docs state the requiredness and runtime missing-value boundary.

## Validation

Validation run after implementation:

```powershell
uv run pytest tests/contracts/test_pydantic_contract.py tests/contracts/test_v3_public_api_contract.py tests/contracts/test_v3_policy_contract.py
uv run ruff format --check src\excelalchemy\adapters\pydantic.py tests\contracts\test_pydantic_contract.py
uv run ruff check src\excelalchemy\adapters\pydantic.py tests\contracts\test_pydantic_contract.py
uv run pyright
uv run python scripts\smoke_agent_context.py
```

Review validation also ran:

```powershell
uv run pytest tests/contracts/test_pydantic_contract.py tests/contracts/test_v3_public_api_contract.py tests/contracts/test_import_contract.py tests/unit/test_field_metadata.py tests/unit/codecs/test_date_range_codec.py
```

All listed checks passed.

## Revisit Triggers

Revisit only if:

- Pydantic changes the public meaning of `FieldInfo.is_required()`.
- ExcelAlchemy introduces an explicit non-Pydantic schema declaration backend.
- 3.0 decides that workbook-facing requiredness should no longer allow
  `ExcelColumn(required=...)` overrides.
- import-mode missing-value behavior is redesigned away from
  `MISSING_VALUE_IMPORT_POLICY`.
