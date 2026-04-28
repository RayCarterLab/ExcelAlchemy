# AGENTS.md

## Project Positioning

`ExcelAlchemy` is a schema-driven Python library for typed Excel import/export
workflows built around Pydantic models.

This repository is maintained as an agent-native system:

- Agents are non-deterministic.
- The workflow harness is deterministic.
- Every action must be controlled, verifiable, and recoverable.

The root `AGENTS.md` is intentionally short. Detailed agent rules live in
[`docs/agent/`](docs/agent/).

## Document Priority

Use this order when documents conflict:

1. `AGENTS.md`
2. `docs/agent/*`
3. `context/*`
4. `docs/*`
5. `docs/history/*`

`docs/agent/*` is the authoritative rule source for agents and the repository's
agent-facing SSOT. `context/*` is machine-readable runtime context for the
harness and agents, not ordinary prose documentation. `docs/*` is supplementary
human documentation, including `docs/tech-debt/` maintenance debt records.
`docs/history/*` contains archived plans and historical ADRs only; it does not
override current rules and should be used only to debug past design decisions.
`plans/` is the harness runtime task-plan artifact directory, not a historical
documentation directory.

## High-Priority Rules

- Act only under an explicit task.
- Read real repository context before editing; do not imagine code structure.
- Use tool interfaces to inspect, patch, and validate files.
- Keep changes minimal and scoped to the task.
- Do not modify unrelated files.
- Preserve public API behavior unless the task explicitly changes it.
- Keep behavior deterministic and testable.
- Do not hide failed or unrun validation.
- Do not remove public exports, compatibility shims, or deprecation warnings
  casually.
- Do not move or rewrite `src/`, `tests/`, `examples/`, or existing non-agent
  docs as part of agent-structure work.
- Stop and report blockers when the task cannot be completed safely.

## Workflow

Follow the deterministic workflow in
[`docs/agent/workflow.md`](docs/agent/workflow.md):

1. Understand
2. Plan
3. Execute
4. Validate
5. Review
6. Fix if needed
7. Report

Validation failures must be analyzed before retrying. Blind retry is prohibited.

## Common Validation Commands

Use focused checks for narrow changes. For broad or public behavior changes,
prefer:

```bash
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest
```

For release-level or docs/payload-sensitive work, also consider:

```bash
uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests
uv run python scripts/smoke_package.py
uv run python scripts/smoke_examples.py
uv run python scripts/smoke_docs_assets.py
uv run python scripts/smoke_api_payload_snapshot.py
```

Testing details and failure handling are in
[`docs/agent/testing.md`](docs/agent/testing.md).

## Key Agent Docs

Core rules:

- [docs/agent/workflow.md](docs/agent/workflow.md): deterministic workflow,
  tool rules, and retry policy.
- [docs/agent/architecture-boundaries.md](docs/agent/architecture-boundaries.md):
  public/internal/compatibility boundaries and docs update rules.
- [docs/agent/invariants.md](docs/agent/invariants.md): ExcelAlchemy invariants
  and safety boundaries.
- [docs/agent/testing.md](docs/agent/testing.md): focused and full validation.
- [docs/agent/review.md](docs/agent/review.md): review mode, final response,
  and Definition of Done.

## Key Project Docs

- [README.md](README.md): user-facing overview.
- [docs/repo-map.md](docs/repo-map.md): repository navigation.
- [docs/domain-model.md](docs/domain-model.md): core concepts.
- [docs/public-api.md](docs/public-api.md): public API boundaries.
- [docs/platform-architecture.md](docs/platform-architecture.md): human
  platform architecture view.
- [docs/platform-code-mapping.md](docs/platform-code-mapping.md): human code
  mapping view.
- [docs/result-objects.md](docs/result-objects.md): result object contracts.
- [docs/api-response-cookbook.md](docs/api-response-cookbook.md): API payloads.
- [docs/locale.md](docs/locale.md): locale and message policy.
- [docs/limitations.md](docs/limitations.md): runtime constraints.
- [src/excelalchemy/README.md](src/excelalchemy/README.md): package layout.
- [tests/README.md](tests/README.md): test ownership.
- [examples/README.md](examples/README.md): examples as contract.

## Harness Placement

Harness runtime source belongs in:

- `harness/loop.py`
- `harness/state.py`
- `harness/runner.py`
- `harness/context.py`
- `harness/plan_artifact.py`

Local evaluation adapters belong in:

- `eval/local.py`

Harness-facing tool adapters belong in:

- `tools/repo_tools.py`

Harness run artifacts belong in `runs/` and are ignored by Git except for
tracked placeholders. Legacy `.harness-runs/` artifacts are also ignored.
Plan run artifacts belong in `plans/active/` or `plans/archive/`.

## Definition of Done

A task is done only when:

- The requested scope is handled.
- The patch is minimal and related.
- Public contracts and architecture boundaries are preserved or intentionally
  updated.
- Relevant validation ran, or validation gaps are reported.
- Self-review found no unresolved blocker.
- The final response includes task understanding, plan, changes, tests, and
  risks.
