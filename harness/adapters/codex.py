"""Codex agent adapter boundary for the deterministic harness."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol


class AgentAdapter(Protocol):
    """Agent adapter interface consumed by the harness loop."""

    def run(self, prompt: str, context: Mapping[str, object]) -> object:
        """Return one agent response for the current prompt and context."""


@dataclass(slots=True)
class CodexAdapter:
    """Small adapter wrapper around a Codex-compatible callable."""

    runner: Callable[[str, Mapping[str, object]], object]

    def run(self, prompt: str, context: Mapping[str, object]) -> object:
        return self.runner(prompt, context)


@dataclass(frozen=True, slots=True)
class CommandAgentAdapter:
    """Run an external agent command with structured prompt/context input."""

    command: tuple[str, ...]
    timeout_seconds: int = 300

    def run(self, prompt: str, context: Mapping[str, object]) -> object:
        if not self.command:
            raise ValueError('Agent command must not be empty.')

        payload = json.dumps({'prompt': prompt, 'context': context}, ensure_ascii=False)
        try:
            completed = subprocess.run(
                self.command,
                input=payload,
                capture_output=True,
                check=False,
                text=True,
                timeout=self.timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(f'Agent command not found: {exc.filename}') from exc
        except subprocess.TimeoutExpired as exc:
            stderr = exc.stderr or ''
            raise RuntimeError(f'Agent command timed out after {self.timeout_seconds}s: {stderr}') from exc

        if completed.returncode != 0:
            stderr = completed.stderr[-4000:]
            raise RuntimeError(f'Agent command failed with exit code {completed.returncode}: {stderr}')
        return completed.stdout
