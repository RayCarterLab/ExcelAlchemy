"""Persistent task plan artifacts for harness runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from harness.state import RunState

PLANS_ROOT = Path('plans')
ACTIVE_DIR = PLANS_ROOT / 'active'
ARCHIVE_DIR = PLANS_ROOT / 'archive'
TEMPLATE_PATH = PLANS_ROOT / 'template.md'

DEFAULT_TEMPLATE = """# Task Plan

## Goal

## Context

## Constraints

## Plan

## Done When

## Validation

## Risks

## Execution Log
"""


@dataclass(frozen=True, slots=True)
class PlanArtifact:
    """A persistent markdown record for one harness run."""

    path: Path
    run_id: str
    task: str


def create_plan_artifact(state: RunState) -> Path:
    """Create the active plan artifact for a run and return its path."""

    ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    template = _read_template()
    path = ACTIVE_DIR / f'{state.run_id}.md'
    path.write_text(_render_initial_plan(template, state), encoding='utf-8')
    return path


def append_plan_event(path: Path, event: str) -> None:
    """Append one timestamped execution-log event to a plan artifact."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as file:
        file.write(f'\n- {_utc_now()} {event}\n')


def _read_template() -> str:
    if TEMPLATE_PATH.exists():
        return TEMPLATE_PATH.read_text(encoding='utf-8')
    return DEFAULT_TEMPLATE


def _render_initial_plan(template: str, state: RunState) -> str:
    title = template.splitlines()[0] if template.strip() else '# Task Plan'
    return f"""{title}

Run ID: `{state.run_id}`
Status: `{state.status}`

## Goal

{state.task}

## Context

{_render_context_references(state.context_summary)}

## Constraints

- Follow root `AGENTS.md` and detailed rules in `docs/agent/`.
- Keep the workflow deterministic and recoverable.
- Do not modify unrelated files.
- Preserve ExcelAlchemy public API and invariants unless explicitly requested.

## Plan

- Pending agent plan step.

## Done When

- Requested scope is handled.
- Relevant validation is run or gaps are reported.
- Final report records changes, tests, and risks.

## Validation

- Pending plan validation commands.

## Risks

- Pending review.

## Execution Log

- {_utc_now()} Plan artifact created.
"""


def _render_context_references(context_summary: dict[str, object]) -> str:
    sources = context_summary.get('sources')
    if not isinstance(sources, list) or not sources:
        return '- No context source references recorded.'

    lines = ['Context sources are stored by reference; run artifacts do not embed full context payloads.']
    for source in sources:
        if not isinstance(source, dict):
            continue
        source_id = source.get('id', '<unknown>')
        path = source.get('path', '<unknown>')
        if not source.get('exists', False):
            lines.append(f'- `{source_id}` -> `{path}` (missing)')
            continue
        digest = str(source.get('sha256', ''))[:12]
        chars = source.get('chars', 0)
        lines.append(f'- `{source_id}` -> `{path}` (sha256 `{digest}`, {chars} chars)')
    return '\n'.join(lines)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
