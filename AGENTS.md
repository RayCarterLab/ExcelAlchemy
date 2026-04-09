# AGENTS.md

## Repository purpose

- ExcelAlchemy is a schema-driven Python library for typed Excel import/export workflows built around Pydantic models.
- The main user flows in this repo are: template generation, workbook import validation, result workbook rendering, storage-backed upload/download, and backend/API integration.

## Core architecture overview

- Public facade: `excelalchemy.ExcelAlchemy`.
- Public config objects: `ImporterConfig`, `ExporterConfig`, `ImportMode`.
- Public schema metadata entry points: `FieldMeta(...)` and `Annotated[..., ExcelMeta(...)]`.
- Main internal collaborators live under `src/excelalchemy/core/`:
  - schema/layout
  - header parsing/validation
  - row aggregation
  - import execution
  - workbook rendering
  - storage gateway resolution
- Public import result surface: `ImportResult`, `CellErrorMap`, `RowIssueMap`.
- Storage is modeled as the `ExcelStorage` protocol.
- Current 2.x reality: custom storage adapters return `WorksheetTable`; examples import it from `excelalchemy.core.table`.

## Important directories

- `src/excelalchemy/`: package source.
- `src/excelalchemy/core/`: internal orchestration and workflow components.
- `src/excelalchemy/codecs/`: built-in field codecs and codec base classes.
- `src/excelalchemy/metadata.py`, `config.py`, `results.py`, `exceptions.py`: stable public modules.
- `src/excelalchemy/_primitives/`: internal helpers, constants, payloads, deprecation utilities.
- `src/excelalchemy/types/`, `exc.py`, `identity.py`, `header_models.py`, `const.py`: compatibility/deprecation layer retained in 2.x.
- `tests/contracts/`: public behavior and contract tests.
- `tests/integration/`: workflow and example integration tests.
- `tests/unit/`: focused unit coverage.
- `tests/support/`: test fixtures, helpers, and in-memory storage/test models.
- `examples/`: runnable examples used as user-facing reference material.
- `examples/fastapi_reference/`: copyable FastAPI-oriented reference project.
- `docs/`: usage, architecture, integration, locale, and release documentation.
- `docs/releases/`: release notes/checklists.
- `scripts/`: smoke checks and generated-doc/example asset helpers.
- `files/example-outputs/`: generated outputs referenced by docs and smoke tests.
- `.github/workflows/`: CI and PyPI publish workflows.

## Public API boundaries

- Prefer imports from `excelalchemy` package root for common public types.
- Additional stable public modules:
  - `excelalchemy.config`
  - `excelalchemy.metadata`
  - `excelalchemy.results`
  - `excelalchemy.exceptions`
  - `excelalchemy.codecs`
- Treat these as internal implementation details unless a task is explicitly about internals:
  - `excelalchemy.core.*`
  - `excelalchemy.helper.*`
  - `excelalchemy.i18n.*`
  - `excelalchemy._primitives.*`
- 2.x compatibility-only imports:
  - `excelalchemy.exc`
  - `excelalchemy.identity`
  - `excelalchemy.header_models`
  - `excelalchemy.types.*`
  - `excelalchemy.util.convertor`
- In new code/docs, prefer:
  - `storage=...` over legacy `minio=...`, `bucket_name=...`, `url_expires=...`
  - `worksheet_table`, `header_table`, `cell_error_map`, `row_error_map` over old aliases like `df`, `header_df`, `cell_errors`, `row_errors`

## Coding style and naming conventions

- Python support target is `>=3.12`; CI runs `3.12`, `3.13`, and `3.14`.
- Use `uv` for setup, test, lint, type-check, build, and smoke commands.
- Ruff is the formatter/linter. Configured line length is `120`.
- Pyright is used for static typing; many source files are listed as strict.
- The codebase uses modern typing syntax consistent with Python 3.12+.
- Tests are behavior-oriented; prefer contract coverage for public behavior over implementation-only assertions.
- Docs and examples are practical and backend-oriented; avoid marketing language and unsupported claims.

## Testing commands

- `uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests`
- `uv run python scripts/smoke_package.py`
- `uv run python scripts/smoke_examples.py`
- `uv run python scripts/smoke_docs_assets.py`
- `uv run python scripts/smoke_api_payload_snapshot.py`

## Lint and type-check commands

- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pyright`

## Documentation update expectations

- Update docs when public behavior, examples, payload shapes, migration guidance, or compatibility guidance changes.
- Keep `README.md`, `README-pypi.md`, `docs/`, and `examples/` aligned when the onboarding story changes.
- If example output changes intentionally, regenerate captured assets:
  - `uv run python scripts/generate_example_output_assets.py`
- Keep docs smoke checks passing after doc/example changes.
- If import failure payload shape changes intentionally, update the generated snapshot in `files/example-outputs/` and keep `scripts/smoke_api_payload_snapshot.py` passing.

## Rules for making changes

- Preserve stable public API modules unless the task explicitly includes a deprecation/migration change.
- Add or update tests near the affected behavior:
  - `tests/contracts/` for public contracts
  - `tests/integration/` for workflows/examples
  - `tests/unit/` for focused logic
- Prefer the helper constructors already used across docs/examples:
  - `ImporterConfig.for_create`
  - `ImporterConfig.for_update`
  - `ImporterConfig.for_create_or_update`
  - `ExporterConfig.for_storage`
- Keep examples runnable from the repo root.
- Keep locale behavior explicit:
  - workbook-facing display locale supports `zh-CN` and `en`
  - docs say runtime exceptions/messages are English-first in 2.x
- When touching compatibility behavior, also check `MIGRATIONS.md`, `docs/public-api.md`, and deprecation tests.

## Things to avoid

- Do not present internal modules as stable application-facing API in docs/examples unless the current repo requires it and the limitation is stated clearly.
- Do not reintroduce pandas-first workflows; the repo explicitly moved to `openpyxl + WorksheetTable`.
- Do not hard-wire Minio into core architecture changes; storage is a protocol boundary.
- Do not remove compatibility imports or old facade aliases casually; 2.x still tests and documents them.
- Do not invent new docs-site or release workflows; this repo currently uses Markdown files plus smoke scripts and GitHub workflows.

## Examples and backward compatibility

- Examples are part of the user-facing contract; `tests/integration/test_examples_smoke.py` and `scripts/smoke_examples.py` exercise them.
- `examples/fastapi_reference/` is the most complete backend integration reference in the repo.
- Keep example response shapes aligned with:
  - `docs/result-objects.md`
  - `docs/api-response-cookbook.md`
- For new examples and docs, prefer the recommended 2.x path:
  - public imports from stable modules
  - explicit `storage=...`
  - new facade inspection names
- Backward compatibility is active in 2.x:
  - deprecated modules still exist
  - legacy Minio config still works but emits deprecation warnings
  - old import-inspection aliases still exist
- If a change touches backward-compatible behavior, check tests under `tests/unit/test_deprecation_policy.py`, `tests/unit/test_config_options.py`, and relevant contract/integration coverage.
