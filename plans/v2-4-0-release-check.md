# v2.4.0 Release Check

Status: `ready`

## Summary

The branch is functionally healthy for a `v2.4.0` release:

- lint passes
- formatter check passes
- type check passes
- full test suite passes
- docs/examples/package smoke passes
- package build succeeds

It is now ready to publish as `v2.4.0`.

## Checks Performed

Executed:

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pyright`
- `uv run pytest --cov=excelalchemy --cov-report=term-missing:skip-covered tests`
- `uv run python scripts/smoke_docs_assets.py`
- `uv run python scripts/smoke_examples.py`
- `uv run python scripts/smoke_package.py`
- `uv run python scripts/smoke_api_payload_snapshot.py`
- `uv build`

Observed result:

- all checks passed
- package build succeeded
- built artifacts now resolve to `2.4.0`

## Version Check

Current version markers now point to `2.4.0`:

- `src/excelalchemy/__init__.py`
- `README.md`
- `README-pypi.md`
- `README_cn.md`
- `CHANGELOG.md`

Because Flit reads the package version dynamically, the build output also
resolves to `2.4.0`:

- `dist/excelalchemy-2.4.0.tar.gz`
- `dist/excelalchemy-2.4.0-py3-none-any.whl`

## Blocking

- none in the repository state after version alignment and verification

## Non-blocking

- test and smoke runs emit expected deprecation warnings for the legacy Minio
  compatibility path
- optional FastAPI-related example checks are skipped when local extras are not
  installed

## Follow-up Before Release

Required before cutting `v2.4.0`:

1. ensure the release commit is created
2. ensure the working tree is clean after the release commit
3. create the `v2.4.0` tag
4. push the branch and tag
5. create the GitHub release

## Recommended Decision

`v2.4.0` is ready to publish.

Recommended next step:

- create the release commit
- push the branch and `v2.4.0` tag
- publish the GitHub release using `docs/releases/2.4.0.md`
