# Plans

This directory is for execution plans for repository work.
Use it when the work is large enough that a short issue, PR description, or commit message is not enough.

## Related docs

- [../AGENTS.md](../AGENTS.md) for repository-local change guidance.
- [../docs/repo-map.md](../docs/repo-map.md) for the main directories plans usually touch.
- [../tech_debt/README.md](../tech_debt/README.md) for recording maintenance burdens discovered while planning.
- [../adr/README.md](../adr/README.md) for decisions that should become lasting architecture records instead of plan notes.

## What belongs in a plan

- Multi-step implementation work that spans:
  - source code
  - tests
  - docs
  - examples
  - smoke scripts
- Changes that need explicit sequencing or checkpoints.
- Work that may affect public API, compatibility behavior, payload shape, or example outputs.
- Repository improvement work such as:
  - migrations
  - documentation restructures
  - refactors across `src/excelalchemy/`, `tests/`, and `docs/`

Do not use a plan for tiny one-file edits or obvious fixes with no coordination cost.

## Status conventions

Use one status per plan:

- `planned`
  - Work is defined but not started.
- `active`
  - Work is in progress.
- `completed`
  - Intended work is done and the plan remains as a record.
- `abandoned`
  - Work was intentionally stopped or superseded.

Put the status near the top of the file so it is easy to scan.

## Recommended plan contents

- Goal
  - What the change is trying to achieve in this repository.
- Scope
  - Which directories, modules, docs, examples, or scripts are expected to change.
- Non-goals
  - What the plan is not trying to change.
- Steps
  - Ordered execution steps.
- Risks or caution areas
  - For example public API, locale behavior, compatibility shims, payload shape, or example assets.
- Verification
  - Which tests, type checks, lint steps, and smoke scripts should pass.

## Progress logs

- Keep progress logs brief and append-only.
- Write each progress entry as:
  - date
  - short summary of what changed
  - current blockers or next step if relevant
- Prefer concrete repository references such as:
  - `src/excelalchemy/results.py`
  - `tests/contracts/test_import_contract.py`
  - `docs/public-api.md`

## Decision logs

- Record only plan-local decisions here.
- If a decision changes the repository’s architectural direction or public design, create an ADR under `adr/` instead of burying it in a plan.
- For plan-local decisions, include:
  - the decision
  - why it was made
  - affected paths
  - any follow-up work it creates

## Repository alignment

For this repository, plans should usually mention affected items from:

- `src/excelalchemy/`
- `tests/contracts/`
- `tests/integration/`
- `tests/unit/`
- `examples/`
- `docs/`
- `scripts/`
- `files/example-outputs/`
