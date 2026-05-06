from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast


def test_execute_tool_reads_only_inside_repo(tmp_path: Path) -> None:
    _prepend_repo_root()
    from tools.executor import execute_tool

    target = tmp_path / 'sample.txt'
    target.write_text('hello harness', encoding='utf-8')

    result = execute_tool('read_file', {'repo_root': str(tmp_path), 'path': 'sample.txt'})
    escaped = execute_tool('read_file', {'repo_root': str(tmp_path), 'path': '../sample.txt'})

    assert result == {'success': True, 'output': 'hello harness', 'error': ''}
    assert escaped['success'] is False
    assert 'escapes repository root' in str(escaped['error'])


def test_context_loader_injects_step_scoped_validation_context() -> None:
    _prepend_repo_root()
    from harness.context import ContextLoader

    context = ContextLoader(repo_root=Path.cwd()).get_context('plan', 'wire harness')

    assert context['step'] == 'plan'
    assert context['task'] == 'wire harness'
    assert 'instructions' in context
    assert 'architecture' in context
    assert 'patterns' in context
    validation = cast(dict[str, object], context['validation'])
    assert 'uv run pytest' in cast(list[str], validation['recommended_commands'])


def test_evaluator_runs_configured_test_tools_through_executor(tmp_path: Path) -> None:
    _prepend_repo_root()
    from eval.local import Evaluator

    result = Evaluator(repo_root=tmp_path, test_tools=('missing_tool',)).check_tests_passed()

    assert result.passed is False
    assert result.reason == 'Test tool failed: missing_tool'
    results = cast(list[dict[str, object]], result.details['results'])
    assert results[0]['success'] is False


def test_evaluator_rejects_unregistered_test_commands(tmp_path: Path) -> None:
    _prepend_repo_root()
    from eval.local import Evaluator

    result = Evaluator(repo_root=tmp_path, test_commands=(('python', '-m', 'pytest'),)).check_tests_passed()

    assert result.passed is False
    assert 'not registered as a repository tool' in result.reason


def test_loop_injects_context_parses_adapter_json_and_executes_tools() -> None:
    _prepend_repo_root()
    from eval.local import Evaluator
    from harness.adapters.codex import CodexAdapter
    from harness.context import ContextLoader
    from harness.loop import HarnessLoop

    seen_context_steps: list[str] = []

    def runner(prompt: str, context: Mapping[str, object]) -> object:
        step = str(context['step'])
        seen_context_steps.append(step)
        output: dict[str, Any]
        if step == 'understand':
            output = {
                'understanding': 'wire harness',
                'task_type': 'investigation',
                'relevant_areas': ['harness', 'tools', 'eval'],
                'inspected_context': ['context'],
                'assumptions': [],
                'blockers': [],
            }
        elif step == 'plan':
            output = {
                'goal': 'wire harness',
                'steps': ['inspect', 'wire', 'validate'],
                'expected_files_to_modify': [],
                'files_to_inspect': [],
                'validation_commands': ['uv run pytest'],
                'risks': [],
                'rollback_plan': 'Revert harness-only changes.',
            }
        elif step == 'execute':
            output = {
                'changes': [],
                'modified_files': [],
                'commands_run': [],
                'deviations_from_plan': [],
                'note': 'read context through a controlled tool',
                'tool_calls': [{'name': 'read_file', 'args': {'path': 'AGENTS.md', 'max_chars': 20}}],
                'tool_results': [{'name': 'spoofed', 'args': {}, 'success': False, 'output': '', 'error': 'ignored'}],
            }
        elif step == 'review':
            output = {
                'findings': [],
                'decision': 'ready',
                'risks': [],
                'missing_tests': [],
                'unrelated_changes': [],
            }
        elif step == 'fix':
            output = {
                'needed': False,
                'root_cause': 'Validation passed.',
                'hypothesis': 'No fix required.',
                'changes': [],
                'modified_files': [],
                'commands_run': [],
                'note': 'No fix required.',
            }
        else:
            output = {}
        assert f'Workflow step: {step}' in prompt
        return json.dumps(output)

    state = HarnessLoop(
        agent_adapter=CodexAdapter(runner=runner),
        agent=None,
        evaluator=Evaluator(max_diff_lines=99999),
        context_loader=ContextLoader(repo_root=Path.cwd()),
        plan_artifacts_enabled=False,
    ).run('wire harness')

    execute = state.get_latest_step('execute')
    assert state.status == 'success'
    assert seen_context_steps == ['understand', 'plan', 'execute', 'review', 'report']
    assert execute is not None
    assert execute.output['tool_results'][0]['success'] is True


def _prepend_repo_root() -> None:
    root = Path(__file__).resolve().parents[2]
    root_string = str(root)
    if root_string not in sys.path:
        sys.path.insert(0, root_string)
