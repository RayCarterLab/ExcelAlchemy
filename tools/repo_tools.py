"""Deterministic repository tool command definitions for harness adapters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RepoTool:
    """One deterministic local command exposed to a harness adapter."""

    name: str
    command: tuple[str, ...]
    description: str


REPO_TOOLS: tuple[RepoTool, ...] = (
    RepoTool(
        name='format_check',
        command=('uv', 'run', 'ruff', 'format', '--check', '.'),
        description='Check repository formatting without rewriting files.',
    ),
    RepoTool(
        name='lint',
        command=('uv', 'run', 'ruff', 'check', '.'),
        description='Run Ruff lint checks.',
    ),
    RepoTool(
        name='type_check',
        command=('uv', 'run', 'pyright'),
        description='Run Pyright type checking.',
    ),
    RepoTool(
        name='tests',
        command=('uv', 'run', 'pytest'),
        description='Run the test suite.',
    ),
)


def get_repo_tools() -> tuple[RepoTool, ...]:
    """Return the deterministic local tool registry."""

    return REPO_TOOLS
