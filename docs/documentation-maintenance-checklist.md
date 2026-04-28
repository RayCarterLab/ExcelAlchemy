# Documentation Maintenance Checklist

Use this checklist to keep repository-local knowledge aligned with code changes.
It is intentionally lightweight and specific to the current `ExcelAlchemy` repository.

## Related docs

- [../AGENTS.md](../AGENTS.md) for repository-local editing guidance.
- [repo-map.md](repo-map.md) for the top-level repository map.
- [domain-model.md](domain-model.md) for core concepts and relationships.
- [agent/invariants.md](agent/invariants.md) for behavior that should not drift accidentally.
- [../src/excelalchemy/README.md](../src/excelalchemy/README.md) for the main package implementation guide.
- [../tests/README.md](../tests/README.md) and [../examples/README.md](../examples/README.md) for executable contract surfaces.
- [../plans/README.md](../plans/README.md), [tech-debt/README.md](tech-debt/README.md), and [history/adr/README.md](history/adr/README.md) for planning, debt tracking, and historical architecture records.

## Use this checklist when

- a PR changes public API shape or recommended usage
- a PR changes internal module boundaries or workflow structure
- a PR changes examples, tests, or generated example outputs
- a PR changes locale behavior, result payloads, storage behavior, or compatibility paths

## Update `AGENTS.md` when

- the recommended public import surface changes:
  - `src/excelalchemy/__init__.py`
  - `src/excelalchemy/config.py`
  - `src/excelalchemy/metadata.py`
  - `src/excelalchemy/results.py`
  - `src/excelalchemy/exceptions.py`
- the repo’s main entry points, safe edit zones, or caution areas change
- the preferred workflow, validation commands, or documentation update expectations change
- the current 2.x guidance changes for:
  - `storage=...` vs legacy Minio fields
  - compatibility imports under `src/excelalchemy/types/`, `src/excelalchemy/exc.py`, `src/excelalchemy/identity.py`, `src/excelalchemy/header_models.py`, `src/excelalchemy/util/convertor.py`
  - the `WorksheetTable` storage seam in `src/excelalchemy/core/table.py`

## Update `docs/repo-map.md` when

- a top-level directory is added, removed, renamed, or repurposed
- a new root-level file becomes an important starting point
- a new major source area appears under `src/excelalchemy/`
- a new docs, examples, tests, scripts, or asset path becomes important for understanding the repo
- the recommended starting points for:
  - public API
  - import flow
  - export/template generation
  - storage integration
  - tests
  change materially

## Update `docs/domain-model.md` when

- a new core concept becomes part of the library vocabulary
- an existing concept is renamed, split, merged, or removed
- responsibilities move between major collaborators such as:
  - `src/excelalchemy/core/schema.py`
  - `src/excelalchemy/core/headers.py`
  - `src/excelalchemy/core/rows.py`
  - `src/excelalchemy/core/executor.py`
  - `src/excelalchemy/core/rendering.py`
  - `src/excelalchemy/core/storage_protocol.py`
  - `src/excelalchemy/helper/pydantic.py`
- the public vs internal distinction changes for a concept
- import, template, export, or storage lifecycle steps change in a way users or maintainers need to reason about

## Update `docs/agent/invariants.md` when

- a public behavior becomes newly stable or stops being stable
- a result state, payload shape, fallback rule, or compatibility expectation changes
- a new rule is enforced by tests or docs and should be treated as intentional behavior
- locale behavior changes for:
  - runtime messages
  - workbook display text
  - compatibility constants in `src/excelalchemy/const.py`
- storage contract expectations change, especially around:
  - `ExcelStorage`
  - `WorksheetTable`
  - upload payload shape
  - explicit storage precedence over legacy Minio fields

## Update module README files when

- update `src/excelalchemy/README.md` when:
  - responsibilities move between public modules and internal modules
  - major internal flows change
  - the recommended edit points for public API, import validation, export/template generation, storage, or locale behavior change
- update `tests/README.md` when:
  - test directories are reorganized
  - a different test layer becomes the right place for a class of changes
  - new smoke checks or fixture areas become part of the normal workflow
- update `examples/README.md` when:
  - examples are added, removed, regrouped, or reclassified
  - an example becomes a compatibility example instead of a recommended example
  - example changes imply updates to `files/example-outputs/` or smoke scripts

## Create a new ADR when

- a change establishes or changes a lasting repository pattern
- the decision affects:
  - stable public API direction
  - internal architecture boundaries
  - storage architecture
  - metadata and schema design
  - result payload structure
  - compatibility and deprecation direction
  - locale or message-layer policy
- the reasoning should outlive a single PR or execution plan

Use `docs/history/adr/README.md` for the expected structure.

## Create a new execution plan when

- the work spans multiple areas such as:
  - `src/excelalchemy/`
  - `tests/`
  - `docs/`
  - `examples/`
  - `scripts/`
  - `files/example-outputs/`
- the work needs explicit sequencing, checkpoints, or risk tracking
- the change is large enough that a PR description is not sufficient

Use `plans/README.md` for status conventions and logging format.

## Record technical debt when

- the change exposes a known compromise that will remain after the PR
- the repo carries a temporary workaround that adds maintenance cost
- the recommended public API and the current implementation still diverge
- documentation, examples, tests, or smoke scripts must stay synchronized through awkward manual steps

Use `docs/tech-debt/README.md` and include:

- impact
- current workaround
- desired fix
- priority
- relevant paths

## Verify before merging a PR

- `AGENTS.md`, `docs/repo-map.md`, `docs/domain-model.md`, and `docs/agent/invariants.md` still match the changed code paths.
- `src/excelalchemy/README.md`, `tests/README.md`, and `examples/README.md` still describe the current implementation and workflow shape.
- `docs/public-api.md` is updated if public-vs-internal or compatibility guidance changed.
- `MIGRATIONS.md` is updated if deprecation or migration guidance changed.
- `docs/result-objects.md` and `docs/api-response-cookbook.md` are updated if result payloads changed.
- `docs/locale.md` is updated if locale-visible behavior changed.
- `examples/` and `files/example-outputs/` are updated if examples or captured outputs changed.
- Run the repo’s normal verification commands for the affected area:
  - `uv run ruff format --check .`
  - `uv run ruff check .`
  - `uv run pyright`
  - `uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests`
  - `uv run python scripts/smoke_package.py`
  - `uv run python scripts/smoke_examples.py`
  - `uv run python scripts/smoke_docs_assets.py`
  - `uv run python scripts/smoke_api_payload_snapshot.py`

## Short rule of thumb

- If a code change alters how someone should navigate, reason about, or safely modify this repo, update the matching repository-local knowledge document in the same PR.
