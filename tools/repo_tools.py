"""Deterministic repository tool command definitions for harness adapters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RepoTool:
    """One deterministic local command exposed to a harness adapter."""

    name: str
    command: tuple[str, ...]
    description: str
    timeout_seconds: int = 300
    allow_extra_args: bool = False


REPO_TOOLS: tuple[RepoTool, ...] = (
    RepoTool(
        name='read_file',
        command=(),
        description='Read a UTF-8 text file from inside the repository.',
    ),
    RepoTool(
        name='search_code',
        command=(),
        description='Search repository text with ripgrep.',
        timeout_seconds=60,
    ),
    RepoTool(
        name='apply_patch',
        command=(),
        description='Apply a unified diff patch to files inside the repository.',
    ),
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
        timeout_seconds=600,
        allow_extra_args=True,
    ),
    RepoTool(
        name='run_tests',
        command=('uv', 'run', 'pytest'),
        description='Run pytest with optional deterministic extra arguments.',
        timeout_seconds=600,
        allow_extra_args=True,
    ),
)


def get_repo_tools() -> tuple[RepoTool, ...]:
    """Return the deterministic local tool registry."""

    return REPO_TOOLS
