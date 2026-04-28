# v2.4 Release Plan

Status: `planned`

## 1. Release Positioning

`v2.4` is an architecture-expression release that consolidates how the
repository explains and presents the existing import platform capabilities.

## 2. Release Theme

`ExcelAlchemy Import Platform Layer`

This release centers on making the import platform model explicit at the
repository level:

- template authoring
- preflight gate
- import runtime
- result intelligence
- artifact and delivery

It does not introduce a new runtime model or new core import features.

## 3. Change Categories

### Architecture

- defined the platform-level architecture view for the existing import system
- separated platform architecture from internal component architecture
- added a platform-to-code mapping for the current codebase
- clarified where current code already aligns and should not be refactored

### Documentation

- added `docs/platform-architecture.md`
- added `docs/runtime-model.md`
- added `docs/integration-blueprints.md`
- added `docs/platform-code-mapping.md`
- aligned repository-facing docs to the new platform model
- improved cross-linking between README, public API docs, result docs, and
  integration docs

### Developer Experience

- made the top-level import workflow easier to discover from entry-point docs
- clarified how backend and frontend integrators should combine:
  - preflight
  - import runtime
  - lifecycle events
  - result objects
  - remediation payloads
- added planning and review records that make the intended v2.4 scope explicit

### Internal Alignment

- completed a minimal alignment pass focused on terminology and doc clarity
- added low-risk code docstrings to clarify lifecycle event semantics
- completed self-review and readiness review for the v2.4 architecture scope
- preserved existing public API behavior and compatibility posture

## 4. Pre-release Checklist

### Versioning

- [ ] bump package version to `2.4.0`
- [ ] confirm built artifacts resolve to `2.4.0`

### Changelog

- [ ] add a `2.4.0` entry to `CHANGELOG.md`
- [ ] describe the release as architecture consolidation, not a feature release
- [ ] list only changes actually completed in this branch

### README And Entry Docs

- [ ] update release strings in:
  - `README.md`
  - `README-pypi.md`
  - `README_cn.md`
- [ ] confirm README entry paths still point to:
  - platform architecture
  - runtime model
  - integration blueprints
  - public API docs
  - result objects docs

### Docs Cross-linking

- [ ] confirm cross-links remain correct among:
  - `docs/platform-architecture.md`
  - `docs/runtime-model.md`
  - `docs/integration-blueprints.md`
  - `docs/platform-code-mapping.md`
  - `docs/public-api.md`
  - `docs/result-objects.md`
  - `docs/api-response-cookbook.md`
- [ ] confirm planning records use the final doc filenames consistently

### Examples And Teaching Surfaces

- [ ] confirm `examples/README.md` still matches the platform vocabulary
- [ ] confirm `examples/fastapi_reference/README.md` still matches the
      documented integration story
- [ ] confirm `src/excelalchemy/README.md` still cleanly distinguishes
      internal ownership from platform framing

### Verification

- [ ] `uv run ruff check .`
- [ ] `uv run ruff format --check .`
- [ ] `uv run pyright`
- [ ] `uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests`
- [ ] `uv run python scripts/smoke_package.py`
- [ ] `uv run python scripts/smoke_examples.py`
- [ ] `uv run python scripts/smoke_docs_assets.py`
- [ ] `uv run python scripts/smoke_api_payload_snapshot.py`
- [ ] `uv build`

## Release Notes Constraint

The `v2.4` release notes should state clearly:

- this release improves architecture expression and repository guidance
- this release does not add a new execution engine
- this release does not add a job framework
- this release does not change the core import pipeline behavior
- this release does not remove 2.x compatibility surfaces

## Bottom Line

`v2.4` should be released as a documentation and architecture-consolidation
version for the `Import Platform Layer`, with emphasis on clearer system
expression, better integrator guidance, and minimal safe alignment rather than
new runtime capability.
