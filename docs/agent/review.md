# Agent Review and Reporting

This file defines review behavior and final response expectations for AI agents.

## Review Mode

When asked to review code, prioritize findings over summary.

Review output order:

1. Bugs, regressions, missing tests, unsafe behavior, or contract violations.
2. Open questions or assumptions.
3. Brief change summary only if useful.

Findings must include file and line references when possible.

## Self-Review Checklist

Before final response, verify:

- The diff is scoped to the task.
- No unrelated files were modified.
- Public API compatibility is preserved or intentionally updated.
- Type safety is preserved.
- Behavior remains deterministic.
- Tests cover new logic or validation gaps are stated.
- Docs/examples are updated when public usage changed.
- Generated assets are regenerated only when needed and validated.
- No hidden state, nondeterministic behavior, or irreversible transformation was
  introduced.

## Final Response Format

Every final agent report must include these five sections:

### Current Task Understanding

State what was requested and what scope was handled.

### Execution Plan

List the executed plan. If the plan changed, state why.

### Changes Made

List modified files and summarize the meaningful changes.

### Test Results

List commands run and their outcomes. If not run, explain why.

### Risk Assessment

State remaining risks, compatibility concerns, validation gaps, or follow-up
work.

Keep reports concise. Do not include large diffs unless requested.

## Definition of Done

A task is done only when:

- The requested scope is handled.
- The patch is minimal and related.
- Public contracts and architecture boundaries are preserved or intentionally
  updated.
- Tests or validation were run, or validation gaps are explicitly reported.
- Self-review found no unresolved blocking issue.
- The final report includes task understanding, plan, changes, tests, and risks.
