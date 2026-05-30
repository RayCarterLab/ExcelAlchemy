from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import cast


def test_run_state_round_trips_and_collects_fix_context(tmp_path: Path) -> None:
    _prepend_repo_root()
    from harness.state import RunState

    state = RunState(task='runtime test', run_id='run-1')
    validate = state.start_step('validate')
    state.finish_step(validate, status='failed', output={'reason': 'bad'}, error='bad')
    review = state.start_step('review')
    state.finish_step(review, status='success', output={'findings': ['missing test']})
    state.record_retry(error='bad')

    path = tmp_path / 'state.json'
    state.save(path)

    loaded = RunState.load(path)
    fix_context = loaded.get_fix_context()
    assert loaded.run_id == 'run-1'
    assert loaded.status == 'failed'
    assert fix_context['previous_errors'] == ['bad']
    assert fix_context['review_findings'] == ['missing test']
    assert fix_context['retry_count'] == 1


def test_context_loader_loads_instruction_architecture_and_validation_patterns(tmp_path: Path) -> None:
    _prepend_repo_root()
    from harness.context import ContextLoader

    _write_json(tmp_path / 'context' / 'architecture' / 'repo_map.json', {'project': {'name': 'X' * 100}})
    _write_json(
        tmp_path / 'context' / 'architecture' / 'module_index.json',
        {'harness_modules': [{'module': 'harness.loop'}]},
    )
    _write_json(
        tmp_path / 'context' / 'instructions' / 'invariants.json',
        {'agent_operating_invariants': [{'id': 'deterministic', 'statement': 'fixed loop'}]},
    )
    _write_json(tmp_path / 'context' / 'patterns' / 'validation.json', {'focused': ['uv run pytest']})
    (tmp_path / 'AGENTS.md').write_text('# Root rules', encoding='utf-8')
    (tmp_path / 'docs' / 'agent').mkdir(parents=True)
    (tmp_path / 'docs' / 'agent' / 'v3-prd.md').write_text('# V3 PRD', encoding='utf-8')
    (tmp_path / 'context' / 'instructions' / 'AGENTS.md').write_text('# Context rules', encoding='utf-8')

    loader = ContextLoader(repo_root=tmp_path)
    context = loader.get_context('plan', 'task', char_budget=80)
    references = loader.context_references()
    sections = cast(list[dict[str, object]], context['sections'])
    instructions = cast(dict[str, dict[str, object]], context['instructions'])

    assert references['source_count'] == 7
    assert references['digest']
    assert instructions['instructions.root_agents']['included_chars'] != 0
    assert instructions['instructions.v3_prd']['included_chars'] != 0
    assert sum(cast(int, section.get('included_chars', 0)) for section in sections) <= 80
    assert any(section['truncated'] for section in sections)
    assert cast(dict[str, object], context['validation'])['recommended_commands'] == ['uv run pytest']


def test_plan_artifact_create_and_append_use_active_plans_dir(tmp_path: Path, monkeypatch) -> None:
    _prepend_repo_root()
    import harness.plan_artifact as plan_artifact
    from harness.state import RunState

    monkeypatch.chdir(tmp_path)
    state = RunState(task='write artifact', run_id='run-2')
    state.context_summary = {
        'sources': [
            {
                'id': 'instructions.root_agents',
                'path': 'AGENTS.md',
                'exists': True,
                'sha256': 'abc123def456',
                'chars': 12,
            }
        ]
    }

    path = plan_artifact.create_plan_artifact(state)
    plan_artifact.append_plan_event(path, 'validate: success')

    text = path.read_text(encoding='utf-8')
    assert path == Path('plans') / 'active' / 'run-2.md'
    assert 'Run ID: `run-2`' in text
    assert 'write artifact' in text
    assert 'Context sources are stored by reference' in text
    assert '```json' not in text
    assert 'validate: success' in text
    assert (tmp_path / plan_artifact.ARCHIVE_DIR).is_dir()


def test_local_evaluator_checks_state_contracts_without_external_services(tmp_path: Path) -> None:
    _prepend_repo_root()
    from eval.local import Evaluator
    from harness.state import RunState

    state = RunState(task='state contract')
    understand = state.start_step('understand')
    state.finish_step(understand, status='success', output={'task_type': 'code_change'})
    plan = state.start_step('plan')
    state.finish_step(plan, status='success', output={'validation_commands': ['uv run pytest']})
    execute = state.start_step('execute')
    state.finish_step(execute, status='success', output={'changes': [], 'modified_files': []})

    evaluator = Evaluator(repo_root=tmp_path)

    execution_check = evaluator.check_task_has_execution_evidence(state)
    validation_check = evaluator.check_validation_commands_declared(state)
    report_check = evaluator.check_report_completeness(state)

    assert execution_check.passed is False
    assert 'requires changes' in execution_check.reason
    assert validation_check.passed is True
    assert report_check.passed is True
    assert report_check.severity == 'warning'


def test_runner_writes_run_state_and_plan_artifact(tmp_path: Path, monkeypatch) -> None:
    _prepend_repo_root()
    from harness.runner import run_task

    _write_minimal_context(tmp_path)
    monkeypatch.chdir(tmp_path)

    report = run_task('local harness smoke')
    run_id = report.splitlines()[0].removeprefix('Run ID: ')

    run_state = tmp_path / 'runs' / f'{run_id}.json'
    plan = tmp_path / 'plans' / 'active' / f'{run_id}.md'
    payload = json.loads(run_state.read_text(encoding='utf-8'))
    plan_text = plan.read_text(encoding='utf-8')
    state_text = run_state.read_text(encoding='utf-8')

    assert run_state.is_file()
    assert plan.is_file()
    assert payload['status'] == 'success'
    assert payload['history'][0]['input']['context']['context_digest'] == payload['context_summary']['digest']
    assert 'sources' not in payload['history'][0]['input']['context']
    assert payload['context_summary']['sources'][0]['sha256']
    assert '# Rules' not in state_text
    assert '- report: success' in report
    assert 'Context sources are stored by reference' in plan_text
    assert '```json' not in plan_text
    assert 'Plan artifact created.' in plan_text


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
