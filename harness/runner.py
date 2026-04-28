"""Public entry point for running the harness."""

from __future__ import annotations

from pathlib import Path

from eval.local import Evaluator
from harness.context import ContextLoader
from harness.loop import HarnessLoop, build_report


def run_task(task: str) -> str:
    """Run one deterministic harness task and return the final report."""

    loop = HarnessLoop(
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


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run the deterministic AI harness.')
    parser.add_argument('task', help='Task description for the harness run.')
    args = parser.parse_args()
    print(run_task(args.task))
