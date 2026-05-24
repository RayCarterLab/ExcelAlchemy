"""Structured context loading for the deterministic harness."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Self

DEFAULT_CONTEXT_BUDGET_CHARS = 12000


class ContextLoadError(ValueError):
    """Raised when a context JSON file exists but cannot be parsed."""


@dataclass(frozen=True, slots=True)
class ContextBundle:
    instructions: dict[str, object] = field(default_factory=dict)
    architecture: dict[str, dict[str, object]] = field(default_factory=dict)
    patterns: dict[str, dict[str, object]] = field(default_factory=dict)
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
            'instructions': {
                'root_agents_loaded': bool(self.instructions.get('root_agents')),
                'context_agents_loaded': bool(self.instructions.get('context_agents')),
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
            'patterns': {
                'validation': self.patterns.get('validation', {}),
            },
        }


@dataclass(frozen=True, slots=True)
class ContextLoader:
    repo_root: Path

    def load(self) -> ContextBundle:
        context_dir = self.repo_root / 'context'
        repo_map = self._read_json(context_dir / 'architecture' / 'repo_map.json')
        module_index = self._read_json(context_dir / 'architecture' / 'module_index.json')
        invariants = self._read_json(context_dir / 'instructions' / 'invariants.json')
        validation = self._read_json(context_dir / 'patterns' / 'validation.json')
        return ContextBundle(
            instructions={
                'root_agents': self._read_text(self.repo_root / 'AGENTS.md'),
                'context_agents': self._read_text(context_dir / 'instructions' / 'AGENTS.md'),
                'invariants': invariants,
            },
            architecture={
                'repo_map': repo_map,
                'module_index': module_index,
            },
            patterns={
                'validation': validation,
            },
            repo_map=repo_map,
            module_index=module_index,
            invariants=invariants,
        )

    def get_context(
        self,
        step: str,
        task: str,
        *,
        char_budget: int = DEFAULT_CONTEXT_BUDGET_CHARS,
    ) -> dict[str, object]:
        """Return dynamic context scoped to one workflow step."""

        bundle = self.load()
        sections = _budget_sections(_context_sections(step, bundle), char_budget)
        return {
            'step': step,
            'task': task,
            'char_budget': char_budget,
            'context_references': self.context_references(),
            'sections': sections,
            'instructions': _section_index(sections, 'instructions'),
            'architecture': _section_index(sections, 'architecture'),
            'patterns': _section_index(sections, 'patterns'),
            'validation': _validation_context(step, bundle.patterns.get('validation', {})),
            'summary': bundle.summary(),
        }

    def context_references(self) -> dict[str, object]:
        """Return compact context source references suitable for run artifacts."""

        sources: list[dict[str, object]] = []
        for source_id, relative_path, category in _context_source_specs():
            path = self.repo_root / relative_path
            if not path.exists():
                sources.append(
                    {
                        'id': source_id,
                        'path': relative_path,
                        'category': category,
                        'exists': False,
                    }
                )
                continue
            text = path.read_text(encoding='utf-8')
            sources.append(
                {
                    'id': source_id,
                    'path': relative_path,
                    'category': category,
                    'exists': True,
                    'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                    'chars': len(text),
                }
            )
        digest = hashlib.sha256(json.dumps(sources, sort_keys=True).encode('utf-8')).hexdigest()
        return {
            'schema_version': 1,
            'digest': digest,
            'source_count': len(sources),
            'sources': sources,
        }

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

    def _read_text(self, path: Path) -> str:
        if not path.exists():
            return ''
        return path.read_text(encoding='utf-8')


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


def _context_source_specs() -> tuple[tuple[str, str, str], ...]:
    return (
        ('instructions.root_agents', 'AGENTS.md', 'instructions'),
        ('instructions.context_agents', 'context/instructions/AGENTS.md', 'instructions'),
        ('instructions.invariants', 'context/instructions/invariants.json', 'instructions'),
        ('architecture.repo_map', 'context/architecture/repo_map.json', 'architecture'),
        ('architecture.module_index', 'context/architecture/module_index.json', 'architecture'),
        ('patterns.validation', 'context/patterns/validation.json', 'patterns'),
    )


def _context_sections(step: str, bundle: ContextBundle) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = [
        {
            'id': 'instructions.root_agents',
            'category': 'instructions',
            'content': str(bundle.instructions.get('root_agents', '')),
        },
        {
            'id': 'instructions.context_agents',
            'category': 'instructions',
            'content': str(bundle.instructions.get('context_agents', '')),
        },
        {
            'id': 'instructions.invariants',
            'category': 'instructions',
            'content': _json_text(bundle.invariants),
        },
        {
            'id': 'patterns.validation',
            'category': 'patterns',
            'content': _json_text(bundle.patterns.get('validation', {})),
        },
    ]
    if step in {'understand', 'plan', 'execute', 'review', 'fix'}:
        sections.extend(
            [
                {
                    'id': 'architecture.repo_map',
                    'category': 'architecture',
                    'content': _json_text(bundle.repo_map),
                },
                {
                    'id': 'architecture.module_index',
                    'category': 'architecture',
                    'content': _json_text(bundle.module_index),
                },
            ]
        )
    return sections


def _budget_sections(sections: list[dict[str, object]], char_budget: int) -> list[dict[str, object]]:
    remaining = max(char_budget, 0)
    budgeted: list[dict[str, object]] = []
    for section in sections:
        content = str(section.get('content', ''))
        original_chars = len(content)
        if remaining <= 0:
            budgeted.append({**section, 'content': '', 'original_chars': original_chars, 'truncated': True})
            continue
        truncated = original_chars > remaining
        included = content[:remaining]
        remaining -= len(included)
        budgeted.append(
            {
                **section,
                'content': included,
                'original_chars': original_chars,
                'included_chars': len(included),
                'truncated': truncated,
            }
        )
    return budgeted


def _section_index(sections: list[dict[str, object]], category: str) -> dict[str, object]:
    return {
        str(section['id']): {
            'included_chars': section.get('included_chars', 0),
            'original_chars': section.get('original_chars', 0),
            'truncated': section.get('truncated', False),
        }
        for section in sections
        if section.get('category') == category
    }


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def _validation_context(step: str, validation: dict[str, Any]) -> dict[str, object]:
    focused = validation.get('focused', [])
    release_level = validation.get('release_level', [])
    if step in {'validate', 'fix', 'report'}:
        return {
            'recommended_commands': focused if isinstance(focused, list) else [],
            'release_level_commands': release_level if isinstance(release_level, list) else [],
        }
    return {
        'recommended_commands': focused if step == 'plan' and isinstance(focused, list) else [],
        'release_level_commands': [],
    }
