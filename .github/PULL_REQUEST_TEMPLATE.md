Repository-local references:

- [AGENTS.md](../AGENTS.md)
- [docs/documentation-maintenance-checklist.md](../docs/documentation-maintenance-checklist.md)
- [docs/repo-map.md](../docs/repo-map.md)
- [docs/domain-model.md](../docs/domain-model.md)
- [docs/invariants.md](../docs/invariants.md)
- [src/excelalchemy/README.md](../src/excelalchemy/README.md)
- [tests/README.md](../tests/README.md)
- [examples/README.md](../examples/README.md)

## Summary

- Describe the user-facing or engineering goal of this change.

## Changes

- List the most important implementation changes.

## Validation

- [ ] `uv run ruff format --check .`
- [ ] `uv run ruff check .`
- [ ] `uv run pyright`
- [ ] `uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests`

## Checklist

- [ ] I updated documentation when behavior, workflows, or design changed.
- [ ] I updated the relevant repository-local knowledge docs listed above, following `docs/documentation-maintenance-checklist.md`.
- [ ] I did not include generated files or local-only artifacts.
- [ ] I confirmed this change does not require additional release steps.
