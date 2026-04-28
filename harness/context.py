"""Structured context loading for the deterministic harness."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from json import JSONDecodeError
from pathlib import Path
from typing import Self


class ContextLoadError(ValueError):
    """Raised when a context JSON file exists but cannot be parsed."""


@dataclass(frozen=True, slots=True)
class ContextBundle:
    repo_map: dict[str, object] = field(default_factory=dict)
    module_index: dict[str, object] = field(default_factory=dict)
    invariants: dict[str, object] = field(default_factory=dict)

    def summary(self) -> dict[str, object]:
        return {
            'repo_map': {
                'project': self.repo_map.get('project', {}),
                'top_level': self.repo_map.get('top_level', []),
                'workflow_entry_points': self.repo_map.get('workflow_entry_points', {}),
            },
            'module_index': {
                'public_api_modules': _module_names(self.module_index.get('public_api_modules')),
                'core_modules': _module_names(self.module_index.get('core_modules')),
                'internal_modules': _module_names(self.module_index.get('internal_modules')),
                'compatibility_modules': _module_names(self.module_index.get('compatibility_modules')),
                'harness_modules': _module_names(self.module_index.get('harness_modules')),
                'preferred_new_code_imports': self.module_index.get('preferred_new_code_imports', []),
                'avoid_in_application_code': self.module_index.get('avoid_in_application_code', []),
            },
            'invariants': {
                'agent_operating_invariants': _invariant_summaries(self.invariants.get('agent_operating_invariants')),
                'architecture_invariants': _invariant_summaries(self.invariants.get('architecture_invariants')),
                'domain_invariants': _invariant_summaries(self.invariants.get('domain_invariants')),
                'result_and_payload_invariants': _invariant_summaries(
                    self.invariants.get('result_and_payload_invariants')
                ),
                'locale_and_message_invariants': _invariant_summaries(
                    self.invariants.get('locale_and_message_invariants')
                ),
                'safety_boundaries': self.invariants.get('safety_boundaries', []),
            },
        }


@dataclass(frozen=True, slots=True)
class ContextLoader:
    repo_root: Path

    def load(self) -> ContextBundle:
        context_dir = self.repo_root / 'context'
        return ContextBundle(
            repo_map=self._read_json(context_dir / 'architecture' / 'repo_map.json'),
            module_index=self._read_json(context_dir / 'architecture' / 'module_index.json'),
            invariants=self._read_json(context_dir / 'instructions' / 'invariants.json'),
        )

    @classmethod
    def for_cwd(cls) -> Self:
        return cls(repo_root=Path.cwd())

    def _read_json(self, path: Path) -> dict[str, object]:
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except JSONDecodeError as exc:
            raise ContextLoadError(f'Invalid JSON in context file {path}: {exc.msg} at line {exc.lineno}') from exc
        if not isinstance(payload, dict):
            raise ContextLoadError(f'Context file {path} must contain a JSON object.')
        return payload


def _module_names(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    names: list[str] = []
    for item in value:
        if isinstance(item, dict):
            module = item.get('module')
            path = item.get('path')
            names.append(str(module or path or item))
        else:
            names.append(str(item))
    return names


def _invariant_summaries(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [
        {
            'id': item.get('id'),
            'statement': item.get('statement'),
            'paths': item.get('paths', []),
        }
        for item in value
        if isinstance(item, dict)
    ]
