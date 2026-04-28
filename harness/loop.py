"""Deterministic harness loop for driving a non-deterministic agent."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from eval.local import EvaluationResult, Evaluator
from harness.context import ContextLoader
from harness.plan_artifact import append_plan_event, create_plan_artifact
from harness.state import RunState, StepRecord
from pydantic import BaseModel, ConfigDict, ValidationError

StepName = Literal[
    'understand',
    'plan',
    'execute',
    'validate',
    'review',
    'fix',
    'report',
]
AgentFn = Callable[[StepName, RunState], dict[str, Any]]


class AgentOutput(BaseModel):
    """Base schema for constrained agent step outputs."""

    model_config = ConfigDict(extra='forbid')


class UnderstandOutput(AgentOutput):
    understanding: str
    task_type: Literal['code_change', 'docs_change', 'test_change', 'review', 'investigation', 'release_support']
    relevant_areas: list[str]
    inspected_context: list[str]
    assumptions: list[str]
    blockers: list[str]


class PlanOutput(AgentOutput):
    goal: str
    steps: list[str]
    expected_files_to_modify: list[str]
    files_to_inspect: list[str]
    validation_commands: list[str]
    risks: list[str]
    rollback_plan: str


class ChangeRecord(AgentOutput):
    path: str
    action: Literal['create', 'modify', 'delete']
    summary: str
    plan_step: str | None


class ExecuteOutput(AgentOutput):
    changes: list[ChangeRecord]
    modified_files: list[str]
    commands_run: list[str]
    deviations_from_plan: list[str]
    plan_alignment_issues: list[str] = []
    note: str


class ReviewOutput(AgentOutput):
    findings: list[str]
    decision: Literal['ready', 'needs_fix', 'blocked']
    risks: list[str]
    missing_tests: list[str]
    unrelated_changes: list[str]


class FixOutput(AgentOutput):
    needed: bool
    root_cause: str
    hypothesis: str
    changes: list[ChangeRecord]
    modified_files: list[str]
    commands_run: list[str]
    plan_alignment_issues: list[str] = []
    note: str
    post_fix_validation: dict[str, object] | None = None


class ReportOutput(AgentOutput):
    task_understanding: str
    execution_plan: list[str]
    changes_made: list[str]
    test_results: list[str]
    risk_assessment: list[str]
    report: str


OUTPUT_SCHEMAS: dict[StepName, type[AgentOutput]] = {
    'understand': UnderstandOutput,
    'plan': PlanOutput,
    'execute': ExecuteOutput,
    'review': ReviewOutput,
    'fix': FixOutput,
    'report': ReportOutput,
}


def default_agent(step: StepName, state: RunState) -> dict[str, Any]:
    """Local placeholder for a real Codex adapter."""

    if step == 'understand':
        return {
            'understanding': state.task,
            'task_type': 'investigation',
            'relevant_areas': [],
            'inspected_context': [],
            'assumptions': ['Default local agent does not inspect repository context.'],
            'blockers': [],
        }
    if step == 'plan':
        return {
            'goal': state.task,
            'steps': ['understand', 'plan', 'execute', 'validate', 'review', 'fix_if_needed', 'report'],
            'expected_files_to_modify': [],
            'files_to_inspect': [],
            'validation_commands': [],
            'risks': ['Default local agent cannot perform repository edits.'],
            'rollback_plan': 'No file changes are made by the default local agent.',
        }
    if step == 'execute':
        return {
            'changes': [],
            'modified_files': [],
            'commands_run': [],
            'deviations_from_plan': [],
            'plan_alignment_issues': [],
            'note': 'No external agent adapter configured.',
        }
    if step == 'review':
        return {
            'findings': [],
            'decision': 'ready',
            'risks': ['Review is limited because the default local agent made no edits.'],
            'missing_tests': [],
            'unrelated_changes': [],
        }
    if step == 'fix':
        return {
            'needed': True,
            'root_cause': 'Validation failed or recovery was requested.',
            'hypothesis': 'No external agent adapter is configured to apply a targeted fix.',
            'changes': [],
            'modified_files': [],
            'commands_run': [],
            'plan_alignment_issues': [],
            'note': 'No external agent adapter configured.',
        }
    if step == 'report':
        return _default_report_output(state)
    return {}


@dataclass(slots=True)
class HarnessLoop:
    """Fixed workflow controller.

    The loop order is deterministic. The injected agent function may be
    non-deterministic, but it can only provide output inside the current step.
    """

    evaluator: Evaluator = field(default_factory=Evaluator)
    agent: AgentFn = default_agent
    state_dir: Path | None = None
    max_retries: int = 3
    context_loader: ContextLoader | None = None
    plan_artifacts_enabled: bool = True

    def run(self, task: str) -> RunState:
        state = RunState(task=task)
        state.context_summary = self._load_context_summary()
        if self.plan_artifacts_enabled:
            state.plan_artifact_path = str(create_plan_artifact(state))
        self._persist(state)

        try:
            self.step1_understand(state)
            self.step2_plan(state)
            self.step3_execute(state)
            validation = self.step4_validate(state)
            self.step5_review(state, validation)
            self.step6_fix_if_needed(state, validation)
            state.update_status('success' if state.status != 'failed' else 'failed')
            self.step7_report(state)
        except Exception as exc:
            state.update_status('failed')
            record = state.start_step('report', input={'exception': type(exc).__name__})
            self._finish(state, record, status='failed', error=str(exc), output={'report': build_report(state)})
            return state

        self._persist(state)
        return state

    def step1_understand(self, state: RunState) -> dict[str, Any]:
        record = state.start_step('understand', input=self._step_input(state))
        output = self._agent_output('understand', state, record)
        self._finish(state, record, output=output)
        return output

    def step2_plan(self, state: RunState) -> dict[str, Any]:
        record = state.start_step('plan', input=self._step_input(state))
        output = self._agent_output('plan', state, record)
        self._finish(state, record, output=output)
        return output

    def step3_execute(self, state: RunState) -> dict[str, Any]:
        record = state.start_step('execute', input=self._step_input(state))
        output = self._agent_output('execute', state, record)
        plan_issues = _plan_alignment_issues(state, output['changes'])
        output['plan_alignment_issues'].extend(plan_issues)
        output['deviations_from_plan'].extend(plan_issues)
        self._finish(state, record, output=output)
        return output

    def step4_validate(self, state: RunState) -> EvaluationResult:
        record = state.start_step('validate', input={'task': state.task})
        result = self.evaluator.evaluate(state)
        status = 'success' if result.passed else 'failed'
        self._finish(
            state, record, status=status, output=result.to_dict(), error=None if result.passed else result.reason
        )
        return result

    def step5_review(self, state: RunState, validation: EvaluationResult) -> dict[str, Any]:
        record = state.start_step('review', input=self._step_input(state, validation_passed=validation.passed))
        output = self._agent_output('review', state, record)
        self._finish(state, record, output=output)
        return output

    def step6_fix_if_needed(self, state: RunState, validation: EvaluationResult) -> dict[str, Any]:
        if validation.passed:
            record = state.start_step(
                'fix',
                input=self._step_input(state, validation_passed=True, attempt=0, max_retries=self.max_retries),
            )
            output = FixOutput(
                needed=False,
                root_cause='Validation passed.',
                hypothesis='No fix is required.',
                changes=[],
                modified_files=[],
                commands_run=[],
                plan_alignment_issues=[],
                note='Validation passed.',
            ).model_dump(exclude_none=True)
            output['retries_used'] = state.retry_count
            output['final_status'] = 'success'
            self._finish(state, record, status='success', output=output)
            return output

        current_validation = validation
        last_output: dict[str, Any] = {}

        for attempt in range(1, self.max_retries + 1):
            record = state.start_step(
                'fix',
                input={
                    'validation_passed': False,
                    'attempt': attempt,
                    'max_retries': self.max_retries,
                    'previous_error': current_validation.reason,
                    'fix_context': state.get_fix_context(),
                    'context_summary': state.context_summary,
                },
            )
            state.record_retry(error=current_validation.reason)
            output = self._agent_output('fix', state, record)
            plan_issues = _plan_alignment_issues(state, output['changes'])
            output['plan_alignment_issues'].extend(plan_issues)
            if plan_issues:
                output['note'] = f"{output['note']} Plan alignment issues: {'; '.join(plan_issues)}"
            next_validation = self.evaluator.evaluate(state)
            output['post_fix_validation'] = next_validation.to_dict()
            output['retries_used'] = state.retry_count
            output['final_status'] = 'success' if next_validation.passed else 'failed'
            last_output = output

            if next_validation.passed:
                state.update_status('running')
                self._finish(state, record, status='success', output=output)
                return output

            current_validation = next_validation
            self._finish(state, record, status='failed', output=output, error=next_validation.reason)

        state.last_error = current_validation.reason
        return last_output

    def step7_report(self, state: RunState) -> dict[str, Any]:
        record = state.start_step('report', input={'status': state.status})
        raw_output = self.agent('report', state)
        raw_output = {**_default_report_output(state), **raw_output}
        try:
            output = self._validate_agent_output('report', raw_output)
        except ValueError as exc:
            self._finish(state, record, status='failed', output={'raw_output': raw_output}, error=str(exc))
            raise
        self._finish(state, record, output=output)
        return output

    def _agent_output(self, step: StepName, state: RunState, record: StepRecord) -> dict[str, Any]:
        raw_output = self.agent(step, state)
        try:
            return self._validate_agent_output(step, raw_output)
        except ValueError as exc:
            self._finish(state, record, status='failed', output={'raw_output': raw_output}, error=str(exc))
            raise

    def _validate_agent_output(self, step: StepName, output: dict[str, Any]) -> dict[str, Any]:
        try:
            parsed = OUTPUT_SCHEMAS[step].model_validate(output)
        except ValidationError as exc:
            raise ValueError(f'Invalid agent output for step "{step}": {exc}') from exc
        return parsed.model_dump(exclude_none=True)

    def _finish(
        self,
        state: RunState,
        record: StepRecord,
        *,
        status: Literal['failed', 'success'] = 'success',
        output: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        state.finish_step(record, status=status, output=output, error=error)
        self._append_plan_step_event(state, record)
        self._persist(state)

    def _persist(self, state: RunState) -> None:
        if self.state_dir is None:
            return
        self.state_dir.mkdir(parents=True, exist_ok=True)
        state.save(self.state_dir / f'{state.run_id}.json')

    def _load_context_summary(self) -> dict[str, object]:
        if self.context_loader is None:
            return {}
        return self.context_loader.load().summary()

    def _step_input(self, state: RunState, **extra: object) -> dict[str, object]:
        return {'task': state.task, 'context_summary': state.context_summary, **extra}

    def _append_plan_step_event(self, state: RunState, record: StepRecord) -> None:
        if state.plan_artifact_path is None:
            return
        append_plan_event(Path(state.plan_artifact_path), _plan_event(state, record))


def build_report(state: RunState) -> str:
    lines = [
        f'Run ID: {state.run_id}',
        f'Status: {state.status}',
        '',
        'Steps:',
    ]
    for record in state.history:
        suffix = f' - {record.error}' if record.error else ''
        lines.append(f'- {record.name}: {record.status}{suffix}')
    return '\n'.join(lines)


def _plan_event(state: RunState, record: StepRecord) -> str:
    label = record.name
    if record.name == 'fix':
        attempt = record.input.get('attempt')
        max_retries = record.input.get('max_retries')
        if attempt:
            label = f'fix attempt {attempt}/{max_retries}'

    parts = [f'{label}: {record.status}']
    if record.error:
        parts.append(f'error={record.error}')
    if record.name == 'fix':
        previous_error = record.input.get('previous_error')
        if previous_error:
            parts.append(f'previous_error={previous_error}')
        final_status = record.output.get('final_status')
        if final_status:
            parts.append(f'final_status={final_status}')
    if record.name == 'validate':
        reason = record.output.get('reason')
        if reason:
            parts.append(f'reason={reason}')
    if record.name == 'report':
        parts.append(f'run_status={state.status}')

    summary = _step_output_summary(record.output)
    if summary:
        parts.append(summary)
    return '; '.join(parts)


def _step_output_summary(output: dict[str, Any]) -> str:
    if not output:
        return ''

    summary_parts: list[str] = []
    changes = output.get('changes')
    if isinstance(changes, list):
        summary_parts.append(f'changes={len(changes)}')
    modified_files = output.get('modified_files')
    if isinstance(modified_files, list):
        summary_parts.append(f'modified_files={len(modified_files)}')
    commands_run = output.get('commands_run')
    if isinstance(commands_run, list):
        summary_parts.append(f'commands_run={len(commands_run)}')
    decision = output.get('decision')
    if isinstance(decision, str):
        summary_parts.append(f'decision={decision}')
    retries_used = output.get('retries_used')
    if isinstance(retries_used, int):
        summary_parts.append(f'retries_used={retries_used}')
    return ', '.join(summary_parts)


def _default_report_output(state: RunState) -> dict[str, Any]:
    return {
        'task_understanding': _first_output_value(state, 'understand', 'understanding', default=state.task),
        'execution_plan': _first_output_value(state, 'plan', 'steps', default=[]),
        'changes_made': _collect_output_values(state, 'changes'),
        'test_results': _validation_results(state),
        'risk_assessment': _collect_output_values(state, 'risks'),
        'report': build_report(state),
    }


def _first_output_value(state: RunState, step_name: str, key: str, *, default: Any) -> Any:
    for record in state.history:
        if record.name == step_name and key in record.output:
            return record.output[key]
    return default


def _collect_output_values(state: RunState, key: str) -> list[str]:
    values: list[str] = []
    for record in state.history:
        value = record.output.get(key)
        if isinstance(value, list):
            values.extend(_stringify_list_item(item) for item in value)
        elif isinstance(value, str):
            values.append(value)
    return values


def _stringify_list_item(item: object) -> str:
    if isinstance(item, dict) and {'path', 'action', 'summary'} <= set(item):
        plan_step = item.get('plan_step')
        plan_suffix = f" (plan: {plan_step})" if plan_step else ' (plan: unlinked)'
        return f"{item['action']} {item['path']}: {item['summary']}{plan_suffix}"
    return str(item)


def _plan_alignment_issues(state: RunState, changes: list[dict[str, Any]]) -> list[str]:
    plan_steps = set(_first_output_value(state, 'plan', 'steps', default=[]))
    issues: list[str] = []
    for change in changes:
        plan_step = change.get('plan_step')
        path = change.get('path', '<unknown>')
        if plan_step is None:
            issues.append(f'{path} is not linked to a plan step.')
        elif plan_step not in plan_steps:
            issues.append(f'{path} references unknown plan step: {plan_step}.')
    return issues


def _validation_results(state: RunState) -> list[str]:
    results: list[str] = []
    for record in state.history:
        if record.name not in {'validate', 'fix'}:
            continue
        if record.error:
            results.append(f'{record.name}: failed - {record.error}')
        else:
            results.append(f'{record.name}: {record.status}')
    return results


def run(
    task: str,
    *,
    evaluator: Evaluator | None = None,
    agent: AgentFn = default_agent,
    max_retries: int = 3,
    context_loader: ContextLoader | None = None,
) -> RunState:
    return HarnessLoop(
        evaluator=evaluator or Evaluator(),
        agent=agent,
        max_retries=max_retries,
        context_loader=context_loader,
    ).run(task)
