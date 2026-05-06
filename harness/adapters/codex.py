"""Codex agent adapter boundary for the deterministic harness."""

from __future__ import annotations

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
