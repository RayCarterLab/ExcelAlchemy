# Technical Debt

This directory is for explicit technical debt records in this repository.
Use it to capture implementation compromises that should be visible and actionable, not just known informally.

## Related docs

- [../AGENTS.md](../AGENTS.md) for repository-local change guidance.
- [../docs/repo-map.md](../docs/repo-map.md) for locating the affected files.
- [../plans/README.md](../plans/README.md) for execution plans tied to debt repayment work.
- [../adr/README.md](../adr/README.md) for the architecture decisions that may explain or constrain a debt item.

## What qualifies as technical debt here

- Compatibility code that is necessary in 2.x but adds maintenance cost.
- Temporary duplication or awkward layering in:
  - `src/excelalchemy/`
  - `docs/`
  - `examples/`
  - `tests/`
- Implementation patterns that are correct today but harder to maintain than the desired design.
- Gaps between the recommended public API and the current implementation reality.
- Missing automation or smoke coverage that creates avoidable risk.

Do not use this directory for:

- vague wishes
- feature requests with no implementation debt
- bugs that should be fixed immediately and do not represent a broader maintenance burden

## Required fields for each debt entry

Each entry should include:

- Summary
  - One short description of the debt.
- Impact
  - What cost it creates in this repository.
  - Examples: harder maintenance, compatibility drag, confusing API shape, duplicated docs/tests, fragile smoke behavior.
- Current workaround
  - How the repository currently lives with the debt.
- Desired fix
  - What the target state should be.
- Priority
  - Use a simple priority label such as:
    - `low`
    - `medium`
    - `high`
- Relevant paths
  - Point to the code, tests, docs, or examples involved.

## Practical guidance

- Be concrete and repository-local.
- Prefer debt entries that point to specific files and seams such as:
  - `src/excelalchemy/types/`
  - `src/excelalchemy/core/storage_minio.py`
  - `docs/public-api.md`
  - `tests/unit/test_deprecation_policy.py`
- If the debt is tightly coupled to a planned piece of work, link the relevant plan under `plans/`.
- If the debt exists because of a deliberate architecture choice, link the relevant ADR under `adr/`.

## Repository alignment

Common debt categories in this repository are likely to involve:

- 2.x compatibility shims and deprecation paths
- duplicated public vs compatibility naming
- result payload evolution and smoke snapshots
- example and docs synchronization cost
- storage abstraction vs legacy Minio behavior
- metadata layering and Pydantic boundary complexity
