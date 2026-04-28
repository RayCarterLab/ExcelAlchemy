# Example, Docs, And Generated-Asset Synchronization Overhead

## Summary

Repository examples are treated as part of the public contract, and their behavior is synchronized across runnable examples, captured outputs, showcase docs, smoke scripts, and README surfaces.

## Impact

- Raises the cost of changing example behavior, even for small user-facing wording changes.
- Increases the number of places that must remain aligned:
  - example scripts
  - captured output assets
  - docs pages
  - smoke scripts
  - README surfaces
- Makes release verification stronger, but also more coupled.

## Current workaround

- Examples are smoke-tested directly.
- Captured outputs live under `files/example-outputs/`.
- Generation and validation scripts enforce consistency:
  - `scripts/generate_example_output_assets.py`
  - `scripts/smoke_examples.py`
  - `scripts/smoke_docs_assets.py`
- Example-driven docs link to the generated assets and runnable examples.

## Desired fix

- Keep the examples contract strong while reducing duplicated synchronization points where practical.
- Prefer a smaller number of authoritative example-output sources and clearer update paths when behavior changes.
- Make it easier to change examples intentionally without manually touching many separate surfaces.

## Priority

- `medium`

## Evidence

- `tests/integration/test_examples_smoke.py`
  - runs the main example entry points directly
- `scripts/generate_example_output_assets.py`
  - generates multiple captured output files plus `import-failure-api-payload.json`
- `scripts/smoke_docs_assets.py`
  - asserts the presence of specific docs fragments and generated assets
- `docs/examples-showcase.md`
  - embeds fixed outputs and links to generated assets
- `examples/README.md`
  - describes examples as smoke-tested and points readers to `files/example-outputs/`
- `README.md`
- `README-pypi.md`
  - both surface example-driven onboarding and fixed outputs
- `files/example-outputs/`
  - stores generated example output artifacts that docs and smoke scripts depend on

## Uncertainty

- The repository clearly shows synchronization cost.
- The best long-term reduction strategy is not explicit here: the codebase does not say whether the intended fix is fewer generated assets, stronger generation automation, fewer duplicated docs surfaces, or some combination.

## Relevant paths

- `examples/README.md`
- `examples/`
- `docs/examples-showcase.md`
- `README.md`
- `README-pypi.md`
- `files/example-outputs/`
- `tests/integration/test_examples_smoke.py`
- `scripts/generate_example_output_assets.py`
- `scripts/smoke_examples.py`
- `scripts/smoke_docs_assets.py`
