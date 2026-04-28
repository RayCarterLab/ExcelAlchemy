"""Local evaluators for harness validation."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from harness.state import RunState


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    passed: bool
    reason: str = ''
    details: dict[str, object] = field(default_factory=dict)
    severity: Literal['error', 'warning'] = 'error'


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    passed: bool
    reason: str
    checks: list[CheckResult]

    def to_dict(self) -> dict[str, object]:
        return {
            'passed': self.passed,
            'reason': self.reason,
            'checks': [
                {
                    'name': check.name,
                    'passed': check.passed,
                    'severity': check.severity,
                    'reason': check.reason,
                    'details': check.details,
                }
                for check in self.checks
            ],
        }


@dataclass(slots=True)
class Evaluator:
    """Evaluate local repository state without external services."""

    repo_root: Path = field(default_factory=lambda: Path.cwd())
    test_commands: tuple[tuple[str, ...], ...] = ()
    max_diff_lines: int = 500
    allowed_paths: tuple[str, ...] = ()
    task: str | None = None
    state: RunState | None = None
    validation_commands_severity: Literal['error', 'warning'] = 'warning'

    def evaluate(self, state: RunState | None = None) -> EvaluationResult:
        active_state = state or self.state
        checks = [
            self.check_tests_passed(),
            self.check_diff_size(),
            self.check_unrelated_file_changes(),
        ]
        if active_state is not None:
            checks.extend(
                [
                    self.check_task_has_execution_evidence(active_state),
                    self.check_validation_commands_declared(active_state),
                    self.check_report_completeness(active_state),
                ]
            )

        failed = [check for check in checks if not check.passed and check.severity == 'error']
        if failed:
            return EvaluationResult(
                passed=False,
                reason='; '.join(check.reason for check in failed if check.reason),
                checks=checks,
            )
        return EvaluationResult(passed=True, reason='All evaluator checks passed.', checks=checks)

    def check_tests_passed(self) -> CheckResult:
        if not self.test_commands:
            return CheckResult(
                name='tests',
                passed=True,
                reason='No test commands configured.',
                details={'commands': []},
            )

        results: list[dict[str, object]] = []
        for command in self.test_commands:
            completed = subprocess.run(
                command,
                cwd=self.repo_root,
                capture_output=True,
                check=False,
                text=True,
            )
            results.append(
                {
                    'command': ' '.join(command),
                    'returncode': completed.returncode,
                    'stdout': completed.stdout[-4000:],
                    'stderr': completed.stderr[-4000:],
                }
            )
            if completed.returncode != 0:
                return CheckResult(
                    name='tests',
                    passed=False,
                    reason=f'Test command failed: {" ".join(command)}',
                    details={'results': results},
                )

        return CheckResult(
            name='tests', passed=True, reason='Configured test commands passed.', details={'results': results}
        )

    def check_diff_size(self) -> CheckResult:
        completed = self._git('diff', '--numstat')
        if completed.returncode != 0:
            return CheckResult(
                name='diff_size',
                passed=False,
                reason='Unable to inspect git diff size.',
                details={'stderr': completed.stderr},
            )

        changed_lines = 0
        files: list[str] = []
        for line in completed.stdout.splitlines():
            added, deleted, path = line.split('\t', maxsplit=2)
            files.append(path)
            if added != '-':
                changed_lines += int(added)
            if deleted != '-':
                changed_lines += int(deleted)

        for path in self._untracked_files():
            if path not in files:
                files.append(path)
            changed_lines += self._count_file_lines(path)

        passed = changed_lines <= self.max_diff_lines
        return CheckResult(
            name='diff_size',
            passed=passed,
            reason=(
                f'Diff size {changed_lines} lines is within limit {self.max_diff_lines}.'
                if passed
                else f'Diff size {changed_lines} lines exceeds limit {self.max_diff_lines}.'
            ),
            details={'changed_lines': changed_lines, 'max_diff_lines': self.max_diff_lines, 'files': files},
        )

    def check_unrelated_file_changes(self) -> CheckResult:
        changed_files = self._changed_files()
        if not self.allowed_paths:
            return CheckResult(
                name='unrelated_files',
                passed=True,
                reason='No allowed path filter configured.',
                details={'changed_files': changed_files},
            )

        normalized_allowed = tuple(path.replace('\\', '/').rstrip('/') for path in self.allowed_paths)
        unrelated = [
            path
            for path in changed_files
            if not any(path == allowed or path.startswith(f'{allowed}/') for allowed in normalized_allowed)
        ]
        return CheckResult(
            name='unrelated_files',
            passed=not unrelated,
            reason='Only allowed paths changed.'
            if not unrelated
            else f'Unrelated files changed: {", ".join(unrelated)}',
            details={'changed_files': changed_files, 'allowed_paths': list(normalized_allowed), 'unrelated': unrelated},
        )

    def check_task_has_execution_evidence(self, state: RunState) -> CheckResult:
        task_type = self._latest_output_value(state, 'understand', 'task_type')
        execute = state.get_latest_step('execute')
        no_op_allowed = {'investigation', 'review', 'release_support'}
        evidence_required = {'code_change', 'docs_change', 'test_change'}

        if task_type in no_op_allowed:
            return CheckResult(
                name='task_execution_evidence',
                passed=True,
                reason=f'Task type {task_type} may complete without file changes.',
                details={'task_type': task_type},
            )

        if task_type not in evidence_required:
            return CheckResult(
                name='task_execution_evidence',
                passed=True,
                severity='warning',
                reason='Task type is missing or unknown; execution evidence check was skipped.',
                details={'task_type': task_type},
            )

        if execute is None:
            return CheckResult(
                name='task_execution_evidence',
                passed=False,
                reason=f'Task type {task_type} requires an execute step.',
                details={'task_type': task_type},
            )

        changes = execute.output.get('changes')
        modified_files = execute.output.get('modified_files')
        has_changes = isinstance(changes, list) and len(changes) > 0
        has_modified_files = isinstance(modified_files, list) and len(modified_files) > 0

        return CheckResult(
            name='task_execution_evidence',
            passed=has_changes or has_modified_files,
            reason='Execution evidence is present.'
            if has_changes or has_modified_files
            else f'Task type {task_type} requires changes or modified_files evidence.',
            details={
                'task_type': task_type,
                'has_changes': has_changes,
                'has_modified_files': has_modified_files,
            },
        )

    def check_validation_commands_declared(self, state: RunState) -> CheckResult:
        plan = state.get_latest_step('plan')
        if plan is None:
            return CheckResult(
                name='validation_commands_declared',
                passed=False,
                severity=self.validation_commands_severity,
                reason='Plan step is missing; validation commands cannot be inspected.',
                details={},
            )

        commands = plan.output.get('validation_commands')
        has_commands = isinstance(commands, list) and len(commands) > 0
        return CheckResult(
            name='validation_commands_declared',
            passed=has_commands,
            severity=self.validation_commands_severity,
            reason='Validation commands were declared.'
            if has_commands
            else 'Plan output did not declare validation_commands.',
            details={'validation_commands': commands if isinstance(commands, list) else []},
        )

    def check_report_completeness(self, state: RunState) -> CheckResult:
        report = state.get_latest_step('report')
        required_fields = [
            'task_understanding',
            'execution_plan',
            'changes_made',
            'test_results',
            'risk_assessment',
        ]
        if report is None:
            return CheckResult(
                name='report_completeness',
                passed=True,
                severity='warning',
                reason='Report step is not present yet; completeness check was skipped.',
                details={'required_fields': required_fields},
            )

        missing = [field for field in required_fields if field not in report.output]
        return CheckResult(
            name='report_completeness',
            passed=not missing,
            reason='Report contains all required fields.'
            if not missing
            else f'Report is missing required fields: {", ".join(missing)}',
            details={'required_fields': required_fields, 'missing_fields': missing},
        )

    def _latest_output_value(self, state: RunState, step_name: str, key: str) -> object:
        record = state.get_latest_step(step_name)
        if record is None:
            return None
        return record.output.get(key)

    def _changed_files(self) -> list[str]:
        tracked = self._git('diff', '--name-only')
        untracked = self._untracked_files()
        files: list[str] = []
        if tracked.returncode == 0:
            files.extend(path.replace('\\', '/') for path in tracked.stdout.splitlines() if path)
        files.extend(path for path in untracked if path not in files)
        return files

    def _untracked_files(self) -> list[str]:
        completed = self._git('ls-files', '--others', '--exclude-standard')
        if completed.returncode != 0:
            return []
        return [path.replace('\\', '/') for path in completed.stdout.splitlines() if path]

    def _count_file_lines(self, relative_path: str) -> int:
        path = self.repo_root / relative_path
        if not path.is_file():
            return 0
        try:
            return len(path.read_text(encoding='utf-8', errors='ignore').splitlines())
        except OSError:
            return 0

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ('git', *args),
            cwd=self.repo_root,
            capture_output=True,
            check=False,
            text=True,
        )
