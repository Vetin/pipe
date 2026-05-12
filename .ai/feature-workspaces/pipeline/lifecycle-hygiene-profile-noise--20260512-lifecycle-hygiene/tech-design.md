# Technical Design: Lifecycle Hygiene And Profile Noise

## Change Delta
Update `featurectl.py` to write and validate workspace lifecycle metadata, normalize execution status, reject duplicate completion events, make `complete-slice` idempotent, and split generated feature discovery output. Update policy docs, legacy reference docs, tests, and current generated artifacts.

## Implementation Summary
Promotion sets the source workspace to `promoted-readonly` with `state.lifecycle` and `state.read_only`. Repository validation accepts duplicate canonical workspaces only when lifecycle metadata is inactive. Execution validation parses headings and completion-event lines. Profiling filters generated/spec paths and writes `discovered-signals.md`.

## Modules And Responsibilities
- `.agents/pipeline-core/scripts/featurectl.py`: lifecycle state, validation, promotion, profile rendering.
- `tests/feature_pipeline/test_finish_promote.py`: promotion and lifecycle validation regressions.
- `tests/feature_pipeline/test_gates_and_evidence.py`: complete-slice idempotency regression.
- `tests/feature_pipeline/test_featurectl_core.py`: profile filtering and discovered-signal split regression.
- `tests/feature_pipeline/test_agents_policy.py`: updated root policy assertions.
- `AGENTS.md`: selective pipeline trigger policy.
- `skills/native-feature-pipeline/references/README.md`: legacy reference warning.

## Dependency And Ownership Plan
Lifecycle validation should land before migrating existing workspace artifacts. Execution/idempotency changes are independent but share `featurectl.py`. Profile filtering should land before regenerating `.ai/knowledge`. Policy docs can land after tests describe the new behavior.

## Contracts
Workspace lifecycle values are `active`, `promoted-readonly`, `archived`, and `abandoned`. A promoted source workspace records `feature.yaml.status: promoted-readonly`, `state.yaml.lifecycle: promoted-readonly`, and `state.yaml.read_only: true`.

## API/Event/Schema Details
`featurectl.py complete-slice` gains `--append-retry`. Without it, a slice already marked complete causes a deterministic failure before evidence manifest mutation. With it, the command may append retry metadata/event while preserving explicit intent.

## Core Code Sketches
`validate_repository_source_truth` checks `workspace_inactive_lifecycle(feature, state)` when a complete canonical feature has a matching workspace. `validate_execution_latest_status` counts `## Latest Status`, rejects active legacy step headings, and calls a duplicate completion-event helper.

## Data Model
`state.yaml` gains optional lifecycle metadata:

```yaml
lifecycle: promoted-readonly
read_only: true
```

`feature.yaml.status` accepts `promoted-readonly` for run workspaces. Canonical feature status remains `complete`.

## Error Handling
Validation returns deterministic blocker strings. `complete-slice` exits non-zero with an explicit already-complete message when a duplicate completion lacks retry intent.

## Security Considerations
The change does not process secrets. Reduced context drift helps prevent future agents from applying stale generated lab knowledge to real feature work.

## Test Strategy
Add focused unit tests for promotion lifecycle, duplicate active workspace rejection, latest-status structure, duplicate slice event validation, complete-slice idempotency, and profile signal separation. Run full `python -m pytest tests/feature_pipeline`.

## Migration Plan
Migrate existing promoted workspaces to `promoted-readonly`, normalize their execution logs, deduplicate slice completion lines, regenerate project profile, and validate canonical/workspace artifacts.

## Rollback Plan
Revert the feature branch. If migration has been applied to workspace artifacts, restore previous `feature.yaml`, `state.yaml`, and `execution.md` from Git history.

## Integration Notes
No external dependencies are introduced. The CLI remains backwards-compatible except that duplicate `complete-slice` calls now require `--append-retry`.

## Decision Traceability
FR-001 and FR-002 map to promotion and repository source-truth validation. FR-003 and FR-004 map to execution validation. FR-005 maps to `complete-slice`. FR-006 and FR-007 map to profile rendering and policy docs. FR-008 maps to the legacy reference README.
