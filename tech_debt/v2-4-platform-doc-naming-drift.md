# Platform Doc Naming Drift In v2.4 Planning Records

## Summary

The v2.4 planning documents still refer to `docs/import-platform.md`, while the
implemented documentation slice uses `docs/platform-architecture.md`.

## Impact

- creates avoidable confusion when moving between planning records and the
  current docs
- increases review friction for follow-up documentation work
- makes future cross-linking and checklist updates slightly harder

## Current workaround

- the repository-facing docs now consistently link to
  `docs/platform-architecture.md`
- planning records still contain the older filename

## Desired fix

- align the v2.4 plan and design-note references with the implemented doc names:
  - `docs/platform-architecture.md`
  - `docs/runtime-model.md`
  - `docs/integration-blueprints.md`
- keep one canonical naming scheme for the platform-layer docs

## Priority

`low`

## Relevant paths

- `plans/v2-4-import-platform-layer-design.md`
- `plans/v2-4-import-platform-layer-design-note.md`
- `docs/platform-architecture.md`
- `docs/runtime-model.md`
- `docs/integration-blueprints.md`
