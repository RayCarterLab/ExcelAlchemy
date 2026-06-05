"""Public entry point for running the harness."""

from __future__ import annotations

import os
import shlex
from pathlib import Path

from harness.adapters.codex import CommandAgentAdapter
from harness.context import ContextLoader
from harness.evaluators.local import Evaluator
from harness.loop import HarnessLoop, build_report


def run_task(task: str, *, agent_command: str | None = None) -> str:
    """Run one deterministic harness task and return the final report."""

    command = _agent_command(agent_command)
    loop = HarnessLoop(
        agent=None,
        agent_adapter=CommandAgentAdapter(command=command) if command is not None else None,
        evaluator=Evaluator(repo_root=Path.cwd()),
        state_dir=Path('harness') / 'runs',
        context_loader=ContextLoader(repo_root=Path.cwd()),
        plan_artifacts_enabled=True,
    )
    state = loop.run(task)
    report_step = next((record for record in reversed(state.history) if record.name == 'report'), None)
    if report_step is not None:
        report = report_step.output.get('report')
        if isinstance(report, str):
            return report
    return build_report(state)


def _agent_command(agent_command: str | None) -> tuple[str, ...] | None:
    raw_command = agent_command or os.environ.get('EXCELALCHEMY_HARNESS_AGENT_COMMAND')
    if raw_command is None or not raw_command.strip():
        return None
    return _split_agent_command(raw_command, platform=os.name)


def _split_agent_command(raw_command: str, *, platform: str) -> tuple[str, ...]:
    if platform == 'nt':
        return tuple(_strip_wrapping_quotes(part) for part in shlex.split(raw_command, posix=False))
    return tuple(shlex.split(raw_command))


def _strip_wrapping_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run the deterministic AI harness.')
    parser.add_argument('task', help='Task description for the harness run.')
    parser.add_argument(
        '--agent-command',
        help='External agent command. The harness sends prompt/context JSON on stdin and expects step JSON on stdout.',
    )
    args = parser.parse_args()
    print(run_task(args.task, agent_command=args.agent_command))
