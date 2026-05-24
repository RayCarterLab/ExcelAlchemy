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


def test_agent_context_smoke_passes_for_current_repository() -> None:
    _prepend_repo_root()
    from scripts.smoke_agent_context import validate_agent_context

    assert validate_agent_context(Path.cwd()) == []


def test_agent_context_smoke_reports_missing_and_invalid_context(tmp_path: Path) -> None:
    _prepend_repo_root()
    from scripts.smoke_agent_context import validate_agent_context

    _write_minimal_context(tmp_path)
    (tmp_path / 'context' / 'architecture' / 'repo_map.json').write_text('{', encoding='utf-8')

    errors = validate_agent_context(tmp_path)

    assert any('docs/agent/workflow.md' in error for error in errors)
    assert any('Invalid JSON' in error for error in errors)


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
                'validation_commands': [],
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


def test_runner_uses_external_agent_command(tmp_path: Path, monkeypatch) -> None:
    _prepend_repo_root()
    from harness.runner import run_task

    _write_minimal_context(tmp_path)
    agent = tmp_path / 'agent.py'
    agent.write_text(
        """
from __future__ import annotations

import json
import sys

payload = json.loads(sys.stdin.read())
step = payload["context"]["step"]

if step == "understand":
    output = {
        "understanding": "command-backed task",
        "task_type": "investigation",
        "relevant_areas": ["harness"],
        "inspected_context": ["context"],
        "assumptions": [],
        "blockers": [],
    }
elif step == "plan":
    output = {
        "goal": "command-backed task",
        "steps": ["inspect", "validate"],
        "expected_files_to_modify": [],
        "files_to_inspect": [],
        "validation_commands": [],
        "risks": [],
        "rollback_plan": "No file changes.",
    }
elif step == "execute":
    output = {
        "changes": [],
        "modified_files": [],
        "commands_run": [],
        "deviations_from_plan": [],
        "note": "No changes needed.",
    }
elif step == "review":
    output = {
        "findings": [],
        "decision": "ready",
        "risks": [],
        "missing_tests": [],
        "unrelated_changes": [],
    }
elif step == "fix":
    output = {
        "needed": False,
        "root_cause": "Validation passed.",
        "hypothesis": "No fix required.",
        "changes": [],
        "modified_files": [],
        "commands_run": [],
        "note": "No fix required.",
    }
else:
    output = {}

print(json.dumps(output))
""",
        encoding='utf-8',
    )

    monkeypatch.chdir(tmp_path)
    report = run_task('command-backed task', agent_command=f'{sys.executable} {agent}')

    assert 'Run ID:' in report
    assert '- report: success' in report
    assert list((tmp_path / 'runs').glob('*.json'))
    assert list((tmp_path / 'plans' / 'active').glob('*.md'))


def test_loop_runs_plan_validation_commands_through_evaluator(monkeypatch) -> None:
    _prepend_repo_root()
    import eval.local
    from eval.local import Evaluator
    from harness.loop import HarnessLoop

    calls: list[tuple[str, dict[str, object]]] = []

    def fake_execute_tool(name: str, args: dict[str, object] | None = None) -> dict[str, bool | str]:
        calls.append((name, args or {}))
        return {'success': True, 'output': 'pytest ok', 'error': ''}

    monkeypatch.setattr(eval.local, 'execute_tool', fake_execute_tool)

    def agent(step: str, _state) -> dict[str, object]:
        if step == 'understand':
            return {
                'understanding': 'validate from plan',
                'task_type': 'investigation',
                'relevant_areas': ['harness'],
                'inspected_context': [],
                'assumptions': [],
                'blockers': [],
            }
        if step == 'plan':
            return {
                'goal': 'validate from plan',
                'steps': ['inspect', 'validate'],
                'expected_files_to_modify': [],
                'files_to_inspect': [],
                'validation_commands': ['uv run pytest tests/unit/test_harness_wiring.py'],
                'risks': [],
                'rollback_plan': 'No file changes.',
            }
        if step == 'execute':
            return {
                'changes': [],
                'modified_files': [],
                'commands_run': [],
                'deviations_from_plan': [],
                'note': 'No changes needed.',
            }
        if step == 'review':
            return {
                'findings': [],
                'decision': 'ready',
                'risks': [],
                'missing_tests': [],
                'unrelated_changes': [],
            }
        if step == 'fix':
            return {
                'needed': False,
                'root_cause': 'Validation passed.',
                'hypothesis': 'No fix required.',
                'changes': [],
                'modified_files': [],
                'commands_run': [],
                'note': 'No fix required.',
            }
        return {}

    state = HarnessLoop(
        agent=agent,
        evaluator=Evaluator(max_diff_lines=99999),
        plan_artifacts_enabled=False,
    ).run('validate from plan')

    validate = state.get_latest_step('validate')
    assert state.status == 'success'
    assert validate is not None
    assert calls == [
        (
            'tests',
            {
                'repo_root': str(Path.cwd()),
                'extra_args': ['tests/unit/test_harness_wiring.py'],
            },
        )
    ]


def _write_minimal_context(root: Path) -> None:
    _write_json(root / 'context' / 'architecture' / 'repo_map.json', {})
    _write_json(root / 'context' / 'architecture' / 'module_index.json', {})
    _write_json(root / 'context' / 'instructions' / 'invariants.json', {})
    _write_json(root / 'context' / 'patterns' / 'validation.json', {})
    (root / 'AGENTS.md').write_text('# Rules', encoding='utf-8')
    (root / 'context' / 'instructions' / 'AGENTS.md').write_text('# Context', encoding='utf-8')


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding='utf-8')


def _prepend_repo_root() -> None:
    root = Path(__file__).resolve().parents[2]
    root_string = str(root)
    if root_string not in sys.path:
        sys.path.insert(0, root_string)
