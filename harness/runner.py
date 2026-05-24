"""Public entry point for running the harness."""

from __future__ import annotations

import os
import shlex
from pathlib import Path

from eval.local import Evaluator
from harness.adapters.codex import CommandAgentAdapter
from harness.context import ContextLoader
from harness.loop import HarnessLoop, build_report


def run_task(task: str, *, agent_command: str | None = None) -> str:
    """Run one deterministic harness task and return the final report."""

    command = _agent_command(agent_command)
    loop = HarnessLoop(
        agent=None,
        agent_adapter=CommandAgentAdapter(command=command) if command is not None else None,
        evaluator=Evaluator(repo_root=Path.cwd()),
        state_dir=Path('runs'),
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
    return tuple(shlex.split(raw_command))


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
