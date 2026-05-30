"""Validate the repository-local context used by the deterministic harness."""

# ruff: noqa: I001

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.context import ContextLoadError, ContextLoader

REQUIRED_AGENT_DOCS = (
    'AGENTS.md',
    'docs/agent/v3-prd.md',
    'docs/agent/workflow.md',
    'docs/agent/architecture-boundaries.md',
    'docs/agent/invariants.md',
    'docs/agent/testing.md',
    'docs/agent/review.md',
    'context/instructions/AGENTS.md',
    'context/instructions/invariants.json',
    'context/architecture/repo_map.json',
    'context/architecture/module_index.json',
    'context/patterns/validation.json',
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate harness-readable agent context.')
    parser.add_argument('--repo-root', default='.', help='Repository root to validate.')
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    errors = validate_agent_context(repo_root)
    if errors:
        for error in errors:
            print(f'ERROR: {error}', file=sys.stderr)
        return 1

    print('Agent context smoke passed.')
    return 0


def validate_agent_context(repo_root: Path) -> list[str]:
    """Return context validation errors for a repository root."""

    errors: list[str] = []
    for relative_path in REQUIRED_AGENT_DOCS:
        path = repo_root / relative_path
        if not path.is_file():
            errors.append(f'missing required agent context file: {relative_path}')
        elif path.stat().st_size == 0:
            errors.append(f'required agent context file is empty: {relative_path}')

    loader = ContextLoader(repo_root=repo_root)
    try:
        context = loader.get_context('plan', 'agent context smoke')
        references = loader.context_references()
    except ContextLoadError as exc:
        errors.append(str(exc))
        return errors

    sources = references.get('sources')
    if not isinstance(sources, list) or not sources:
        errors.append('context references did not include any sources')
        return errors

    for source in sources:
        if not isinstance(source, dict):
            errors.append('context source entry is not an object')
            continue
        source_id = source.get('id', '<unknown>')
        path = source.get('path', '<unknown>')
        if not source.get('exists', False):
            errors.append(f'context source is missing: {source_id} -> {path}')
            continue
        if not source.get('sha256'):
            errors.append(f'context source is missing a sha256 digest: {source_id} -> {path}')
        if not source.get('chars'):
            errors.append(f'context source is empty: {source_id} -> {path}')

    summary = context.get('summary')
    if not isinstance(summary, dict):
        errors.append('loaded context did not include a summary object')
        return errors

    instructions = summary.get('instructions')
    if not isinstance(instructions, dict) or not instructions.get('root_agents_loaded'):
        errors.append('root AGENTS.md was not loaded into context summary')
    if not isinstance(instructions, dict) or not instructions.get('context_agents_loaded'):
        errors.append('context/instructions/AGENTS.md was not loaded into context summary')
    if not isinstance(instructions, dict) or not instructions.get('v3_prd_loaded'):
        errors.append('docs/agent/v3-prd.md was not loaded into context summary')

    source_ids = {source.get('id') for source in sources if isinstance(source, dict)}
    if 'instructions.v3_prd' not in source_ids:
        errors.append('context references did not include docs/agent/v3-prd.md')

    invariants = summary.get('invariants')
    if not isinstance(invariants, dict):
        errors.append('loaded context summary did not include invariants')
    else:
        version_invariants = invariants.get('version_scoped_invariants')
        if not isinstance(version_invariants, list):
            errors.append('loaded context summary did not include version-scoped invariants')
        elif not any(isinstance(item, dict) and item.get('id') == 'v3-prd-authority' for item in version_invariants):
            errors.append('version-scoped invariants did not include v3-prd-authority')

    validation = context.get('validation')
    if not isinstance(validation, dict) or not validation.get('recommended_commands'):
        errors.append('validation context did not expose recommended commands')

    return errors


if __name__ == '__main__':
    raise SystemExit(main())
