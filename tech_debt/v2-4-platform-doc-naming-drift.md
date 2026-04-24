# Platform Doc Naming Drift In v2.4 Planning Records

## Summary

This note recorded the earlier mismatch where the v2.4 planning documents still
referred to `docs/import-platform.md`, while the implemented documentation
slice used `docs/platform-architecture.md`.

## Current status

Resolved in planning records.
The canonical platform doc set is now:

- `docs/platform-architecture.md`
- `docs/runtime-model.md`
- `docs/integration-blueprints.md`

## Historical impact

- creates avoidable confusion when moving between planning records and the
  current docs
- increases review friction for follow-up documentation work
- makes future cross-linking and checklist updates slightly harder

## Current workaround

- none needed after the planning-record alignment

## Resolution

- aligned the v2.4 plan and design-note references with the implemented doc
  names:
  - `docs/platform-architecture.md`
  - `docs/runtime-model.md`
  - `docs/integration-blueprints.md`
- retained one canonical naming scheme for the platform-layer docs

## Priority

`resolved`

## Relevant paths

- `plans/v2-4-import-platform-layer-design.md`
- `plans/v2-4-import-platform-layer-design-note.md`
- `docs/platform-architecture.md`
- `docs/runtime-model.md`
- `docs/integration-blueprints.md`
