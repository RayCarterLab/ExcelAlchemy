# Codebase Rules

This file defines codebase-shape rules that make `ExcelAlchemy` safer for
agent-assisted maintenance.

Agents are non-deterministic and context-limited. The codebase must therefore
make ownership, public boundaries, and validation paths obvious from the real
repository structure.

## Core Rule

Prefer deep, responsibility-named modules with narrow public interfaces and
strong nearby validation.

A module is agent-friendly when an agent can answer these questions from local
context before editing:

- What responsibility does this module own?
- Which symbols are public, stable, or compatibility-sensitive?
- Which collaborators may this module call?
- Which tests prove the behavior?
- Which docs or examples must be synchronized if behavior changes?

## Required Shape

Use these rules when adding or changing source code:

- Keep public entry points small, explicit, typed, and documented.
- Hide implementation complexity behind stable public functions, classes,
  protocols, or result objects.
- Use concrete responsibility names such as `schema`, `workbook`, `runtime`,
  `rendering`, `storage`, `messages`, or `codecs`.
- Prefer module-local helpers over cross-package shortcuts when the helper is
  not part of the public contract.
- Keep ownership boundaries aligned with
  [`architecture-boundaries.md`](architecture-boundaries.md).
- Put behavior-specific tests near the owned component.
- Make validation commands deterministic and runnable without hidden external
  state.

## Public Interface Rules

Public interfaces are the codebase's control surface for both humans and
agents.

Required rules:

- Treat `src/excelalchemy/__init__.py` exports as high-risk public API.
- Keep public result, config, storage, codec, and error contracts stable unless
  the task explicitly changes them.
- Route docs and examples through stable public imports instead of internal
  module paths.
- Preserve compatibility behavior unless the active task is explicitly scoped
  to ExcelAlchemy 3.0 removal work.
- Add or update contract tests when a public interface changes.

## Internal Module Rules

Internal code may be refactored only when the ownership and tests remain clear.

Required rules:

- Do not create generic catch-all packages or modules for unrelated behavior.
- Do not move behavior across ownership boundaries without updating the
  boundary docs and tests.
- Do not make callers depend on another module's private implementation detail.
- Do not duplicate parsing, formatting, validation, storage, or message logic
  outside its owning component.
- Do not add hidden time, randomness, network, filesystem, environment, or
  global-state dependencies to core logic unless the task explicitly requires
  them and tests control them.

## Test and Feedback Rules

Agent-safe changes need fast, local, meaningful feedback.

Required rules:

- For new logic, add or update focused tests that would fail before the change.
- For public behavior, prefer contract or integration coverage in addition to
  unit tests.
- For payloads, examples, docs assets, or generated expectations, regenerate
  and smoke-test the affected artifacts.
- Do not keep real validation commands in no-op task plans.
- Do not report a change as done unless relevant validation ran, or the exact
  validation gap is reported.

## Anti-Patterns

Avoid these patterns because they make agent work less controlled and less
recoverable:

- Thin wrapper modules that expose many implementation details.
- Large files with mixed ownership and no focused tests.
- Cross-package imports that bypass the public or ownership boundary.
- Docs that describe a different structure than the source code implements.
- Tests that only cover happy paths for compatibility-sensitive behavior.
- Broad refactors mixed into narrow behavior changes.
