# Architecture Decision Records

This directory contains historical architecture decision records for this
repository. These records explain past design decisions; they are not current
agent rules and do not override `AGENTS.md` or `docs/agent/*`.

## Related docs

- [../../../AGENTS.md](../../../AGENTS.md) for current repository-local change guidance.
- [../../domain-model.md](../../domain-model.md) for the concepts ADRs usually shape.
- [../../agent/invariants.md](../../agent/invariants.md) for current constraints.
- [../../../plans/README.md](../../../plans/README.md) for active harness plan artifacts.
- [../../tech-debt/README.md](../../tech-debt/README.md) for debt items that may motivate or result from an architectural decision.

## When to create an ADR

Create an ADR when the decision affects one or more of these areas:

- stable public API direction
- internal architecture boundaries
- storage architecture
- metadata and schema model design
- result payload structure
- compatibility and deprecation direction
- locale or message-layer policy
- testing or smoke-verification strategy when it changes repository-wide expectations

Do not create an ADR for:

- small local refactors
- obvious bug fixes
- one-off implementation choices that do not establish a lasting repository pattern

## Expected structure

Each ADR should include:

- Title
  - Short and specific.
- Status
  - For example:
    - `proposed`
    - `accepted`
    - `superseded`
    - `rejected`
- Context
  - What repository problem or pressure led to the decision.
- Decision
  - The choice that was made.
- Consequences
  - What becomes easier, harder, or required because of the decision.
- Relevant paths
  - The main code, docs, tests, examples, or scripts affected.
- Related records
  - Optional links to plans, debt entries, migrations, or superseding ADRs.

## Practical guidance

- Keep ADRs short and concrete.
- Write them so a future maintainer can understand why the repository looks the way it does.
- Prefer explicit repository references such as:
  - `src/excelalchemy/config.py`
  - `src/excelalchemy/metadata.py`
  - `src/excelalchemy/results.py`
  - `docs/public-api.md`
  - `MIGRATIONS.md`

## Repository alignment

In this repository, likely ADR-worthy topics include:

- why a behavior is public vs internal
- why `storage=...` is preferred over legacy Minio fields
- why compatibility shims remain in 2.x
- why result payloads or naming conventions changed
- why a workflow moved between `core/`, `helper/`, or public modules

