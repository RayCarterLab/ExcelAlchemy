# Agent Workflow

This file defines the deterministic workflow for agents working in the
`ExcelAlchemy` repository.

The agent may be non-deterministic, but the workflow is fixed. Do not skip
steps. Each step has explicit inputs and outputs.

## Core Responsibilities

Agents must:

- Understand and restate the task before changing files.
- Base all decisions on real repository context.
- Use tool interfaces to inspect, modify, and validate the repository.
- Keep all modifications scoped to the requested task.
- Make every behavior change verifiable by tests, smoke checks, or documented
  manual validation.
- Preserve recoverability by using small patches and clear summaries.
- Stop and report blockers when the task cannot be completed safely.

Agents must not:

- Modify code opportunistically.
- Rewrite unrelated modules.
- Invent code structure without reading the repository.
- Generate untested behavior changes.
- Hide test failures or validation gaps.
- Treat internal modules as stable public API unless the task explicitly targets
  internals.

## Step 1: Understand

Input:

- User request.
- Current repository state.
- Relevant docs, source files, tests, and examples.

Required actions:

- Identify the requested outcome.
- Identify affected public APIs, internal components, tests, docs, and examples.
- Identify constraints from `AGENTS.md` and related docs.
- Determine whether the task is a code change, documentation change, test
  change, review, investigation, or release/support task.

Output:

- Concise task understanding.
- Files or areas that must be inspected.
- Assumptions or blockers.

## Step 2: Plan

Input:

- Task understanding.
- Inspected repository context.

Required actions:

- Create an ordered plan before editing files.
- Keep the plan minimal and testable.
- Name the validation commands that will be run.
- Include rollback or recovery considerations for risky changes.

Output:

- Ordered execution plan.
- Expected files to modify.
- Validation plan.

## Step 3: Execute

Input:

- Approved or self-contained plan.
- Current file contents read through tools.

Required actions:

- Apply the smallest correct patch.
- Preserve public contracts unless the task explicitly changes them.
- Update tests near changed behavior.
- Update docs and examples when public behavior, recommended usage, payload
  shapes, or migration guidance changes.
- Keep generated assets unchanged unless the task requires regeneration.

Output:

- Patch applied through tool interfaces.
- Modified files.
- Notes on intentional behavior changes.

## Step 4: Validate

Input:

- Modified repository state.
- Validation plan.

Required actions:

- Run the narrowest relevant checks first.
- Run broader checks when public behavior, shared internals, examples, result
  payloads, storage, or compatibility behavior changed.
- Record exact commands and outcomes.

Output:

- Test and validation results.
- Failures with root-cause notes.

## Step 5: Review

Input:

- Patch diff.
- Validation results.
- Project invariants.

Required actions:

- Review the diff as if reviewing a pull request.
- Check for unrelated edits.
- Check API compatibility, typing, determinism, and test coverage.
- Check docs/examples if public usage changed.
- Check that no hidden state, nondeterministic behavior, or irreversible
  transformation was introduced.

Output:

- Self-review findings.
- Risk assessment.
- Decision: ready, needs fix, or blocked.

## Step 6: Fix

Input:

- Review findings or validation failures.

Required actions:

- Analyze the cause before changing anything.
- Adjust the plan when the original approach was wrong.
- Apply a targeted patch.
- Re-run relevant validation.
- Repeat only with a clear hypothesis.

Output:

- Fix patch.
- Updated validation results.
- Remaining risks or blockers.

## Step 7: Report

Input:

- Final diff.
- Final validation results.
- Self-review notes.

Required output:

1. Current task understanding.
2. Execution plan.
3. Changes made.
4. Test results.
5. Risk assessment.

For small tasks, keep the final report concise while still covering all five
items.

## Tool Usage

Logical tools:

- `read_file`: read exact file contents before editing.
- `search_code`: search for symbols, usages, tests, and docs.
- `apply_patch`: make file modifications.
- `run_tests`: run validation commands.

Rules:

- Do not imagine code structure.
- Do not edit a file that has not been read in the current task context.
- Search before changing shared APIs, public names, compatibility paths, or
  behavior used across modules.
- Use `apply_patch` or the harness equivalent for manual edits.
- Use deterministic commands for validation.
- Record exact commands when reporting results.
- Never use destructive repository commands such as hard resets unless the user
  explicitly asks for that operation.

Recommended search targets:

- Source: `src/excelalchemy/`
- Contract tests: `tests/contracts/`
- Integration tests: `tests/integration/`
- Unit tests: `tests/unit/`
- Examples: `examples/`
- Docs: `README.md`, `README-pypi.md`, `docs/`, `MIGRATIONS.md`
- Scripts: `scripts/`

## Failure and Retry Policy

Failures are part of the workflow. Blind retry is prohibited.

When validation fails:

1. Capture the exact failing command.
2. Read the error output.
3. Identify whether the failure is caused by the patch, environment, dependency
   state, flaky external service, or pre-existing repository state.
4. Inspect the relevant source and tests.
5. Update the plan with a specific hypothesis.
6. Apply a targeted fix.
7. Re-run the narrow failing check.
8. Run broader checks if the fix affects shared behavior.

Agents must not:

- Retry without a changed hypothesis.
- Mask failures by weakening tests.
- Delete assertions to make tests pass.
- Skip validation silently.
- Report success when checks failed or were not run.

If validation cannot run, report:

- Command attempted.
- Reason it could not run.
- Scope of unvalidated behavior.
- Recommended next validation step.
