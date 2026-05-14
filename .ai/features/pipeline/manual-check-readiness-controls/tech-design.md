# Technical Design: Manual Check Readiness Controls

## Change Delta

Add explicit state-transition and scope-change commands, split planning-package
validation from implementation readiness, strengthen docs-consulted validation,
add opt-in real Codex e2e scaffolding, and add manual-check preflight coverage.

## Implementation Summary

The implementation extends `featurectl_core/cli.py`, `validation.py`, and
supporting helpers without changing existing command behavior. New tests prove
default behavior remains deterministic. Skills and shared knowledge are updated
to formalize `events.yaml`, review artifact types, project profile artifacts,
and subagent fallback evidence.

## Modules And Responsibilities

- `featurectl_core/cli.py`: add `step set` and `scope-change` command handlers.
- `featurectl_core/validation.py`: add `planning_package` validation and
  structured docs-consulted checks.
- `featurectl_core/events.py`: render new structured event types.
- `featurectl_core/evidence.py`: reuse stale target behavior for scope change.
- `tests/feature_pipeline`: add command, validation, skill, real e2e, and
  preflight tests.
- `.agents/skills`: update skill instructions for readiness, review, context,
  and TDD fallback.

## Dependency And Ownership Plan

No new runtime dependencies are required. Real Codex e2e uses the existing
`codex` binary only when explicitly enabled by environment variables. The
manual preflight script is a small shell script under `pipeline-lab`.

## Contracts

- `state.yaml` stores current machine state.
- `events.yaml` stores append-only machine-readable event history.
- `execution.md` stores human-readable run context and docs-consulted proof.
- `reviews/*.yaml` stores machine-readable review findings.
- `reviews/*-review.md` stores human-readable review narratives.

## API/Event/Schema Details

New commands:

```bash
featurectl.py step set --workspace <path> --step <step> --by <actor> --note <note>
featurectl.py scope-change --workspace <path> --reason <reason> --return-step <step> --stale <artifact> ...
featurectl.py validate --planning-package --workspace <path>
```

New event types can use the existing schema vocabulary where possible:
`step_changed` and `scope_changed` are added to the event schema and validator.

## Core Code Sketches

```python
state["current_step"] = normalize_step_name(args.step)
append_execution_event(workspace, "Step Events", render_execution_event(...))
write_latest_status(workspace, state["current_step"])
```

```python
blockers.extend(validate_planning_package(workspace, state))
```

## Data Model

`scope-change.md` records the latest scope-change reason, return step, stale
artifacts, actor, timestamp, and status. Multiple scope changes append history
inside the same file.

## Error Handling

Invalid steps, unknown stale artifacts, missing docs-consulted usage, and
missing review YAML files produce actionable validation errors. Optional real
e2e tests skip when `RUN_REAL_CODEX_E2E` is not set.

## Security Considerations

No secret material is introduced. Real e2e runs must use temporary workspaces
and must capture artifacts without exposing credentials.

## Test Strategy

- Add failing tests for step set, planning-package validation, scope-change, and
  docs-consulted proof.
- Add skipped-by-default real Codex e2e behavioral tests.
- Add skill contract tests for all `nfp-*` skills.
- Add preflight script tests.
- Run full `tests/feature_pipeline`, public raw check, compileall, and diff
  check before promotion.

## Migration Plan

Existing workspaces remain valid. New validations apply when gates or modes are
explicitly invoked. Historical docs-consulted sections are not globally migrated.

## Rollback Plan

Revert the command slices and tests. Existing `gate set`, `mark-stale`, and
`validate --implementation` behavior can remain intact if planning-package or
scope-change additions need to be backed out.

## Integration Notes

Manual-check preflight will run existing `featurectl.py status`, `validate`,
`validate --planning-package`, `validate --implementation`, and
`worktree-status` commands. It should not perform destructive operations.

## Decision Traceability

- FR-001 through FR-004 map to `featurectl.py` command additions.
- FR-005 maps to docs-consulted validation.
- FR-006 and FR-007 map to skill/doc updates.
- FR-008 and FR-010 map to real e2e and manual preflight scaffolding.
- FR-009 maps to skill contract tests.
