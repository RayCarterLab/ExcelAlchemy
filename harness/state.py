"""Serializable run state for the deterministic harness."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Self

RunStatus = Literal['running', 'failed', 'success']
StepStatus = Literal['running', 'failed', 'success', 'skipped']


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(slots=True)
class StepRecord:
    """One deterministic workflow step record."""

    name: str
    status: StepStatus
    started_at: str = field(default_factory=_utc_now)
    finished_at: str | None = None
    input: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def finish(self, *, status: StepStatus, output: dict[str, Any] | None = None, error: str | None = None) -> None:
        self.status = status
        self.finished_at = _utc_now()
        self.output = output or {}
        self.error = error


@dataclass(slots=True)
class RunState:
    """Mutable, JSON-serializable state for one harness run."""

    task: str
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_step: str | None = None
    history: list[StepRecord] = field(default_factory=list)
    status: RunStatus = 'running'
    retry_count: int = 0
    last_error: str | None = None
    context_summary: dict[str, object] = field(default_factory=dict)
    plan_artifact_path: str | None = None
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)

    def start_step(self, name: str, *, input: dict[str, Any] | None = None) -> StepRecord:
        self.current_step = name
        self.updated_at = _utc_now()
        record = StepRecord(name=name, status='running', input=input or {})
        self.history.append(record)
        return record

    def finish_step(
        self,
        record: StepRecord,
        *,
        status: StepStatus,
        output: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        record.finish(status=status, output=output, error=error)
        self.updated_at = _utc_now()
        if status == 'failed':
            self.status = 'failed'
            self.last_error = error

    def record_retry(self, *, error: str | None = None) -> None:
        self.retry_count += 1
        if error is not None:
            self.last_error = error
        self.updated_at = _utc_now()

    def update_status(self, status: RunStatus) -> None:
        self.status = status
        if status == 'success':
            self.last_error = None
        self.updated_at = _utc_now()

    def get_step_records(self, name: str) -> list[StepRecord]:
        return [record for record in self.history if record.name == name]

    def get_latest_step(self, name: str) -> StepRecord | None:
        for record in reversed(self.history):
            if record.name == name:
                return record
        return None

    def get_failed_steps(self) -> list[StepRecord]:
        return [record for record in self.history if record.status == 'failed']

    def get_fix_context(self) -> dict[str, object]:
        previous_errors = [record.error for record in self.history if record.error]
        validation_failures = [
            {
                'step': record.name,
                'status': record.status,
                'error': record.error,
                'output': record.output,
            }
            for record in self.history
            if record.name in {'validate', 'fix'} and record.status == 'failed'
        ]
        review_findings: list[str] = []
        plan_alignment_issues: list[str] = []

        for record in self.history:
            findings = record.output.get('findings')
            if record.name == 'review' and isinstance(findings, list):
                _extend_unique(review_findings, findings)

            structured_issues = record.output.get('plan_alignment_issues')
            if isinstance(structured_issues, list):
                _extend_unique(plan_alignment_issues, structured_issues)

            deviations = record.output.get('deviations_from_plan')
            if isinstance(deviations, list):
                _extend_unique(plan_alignment_issues, deviations)

        return {
            'previous_errors': previous_errors,
            'validation_failures': validation_failures,
            'review_findings': review_findings,
            'plan_alignment_issues': plan_alignment_issues,
            'retry_count': self.retry_count,
            'last_error': self.last_error,
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Self:
        data = dict(payload)
        history = [StepRecord(**item) for item in data.pop('history', [])]
        return cls(**data, history=history)

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, payload: str) -> Self:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError('RunState JSON payload must be an object.')
        return cls.from_dict(data)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.to_json(), encoding='utf-8')

    @classmethod
    def load(cls, path: str | Path) -> Self:
        return cls.from_json(Path(path).read_text(encoding='utf-8'))


def _extend_unique(target: list[str], values: list[object]) -> None:
    for value in values:
        item = str(value)
        if item not in target:
            target.append(item)
