# Feature Card: pipeline/execution-safety-guardrails

## Implementation

- Added legal `step set` transitions and kept backward movement behind
  `scope-change`.
- Added ordered `gate set` dependency checks for downstream planning and
  execution gates.
- Added `featurectl.py new --allow-dirty` and blocked dirty base checkouts
  unless the dirt is generated pipeline bootstrap/profile output.
- Required `events.yaml` for active workspaces.
- Moved execution current-state consistency checks earlier for active runs.
- Split `worktree-status` from the new `implementation-ready` command.
- Strengthened Docs Consulted validation to require per-path use and confidence.
- Expanded opt-in real Codex e2e tests for under-specified and fully specified
  reset-password prompts.
- Labeled outcome-smoke runner outputs as partial pipeline fidelity.
- Added a CI job for the full deterministic feature-pipeline test suite.

## Manual Validation

- `python -m py_compile .agents/pipeline-core/scripts/featurectl_core/cli.py ...`
  passed.
- Focused guardrail suite passed with 59 tests.
- Full deterministic suite passed with 199 tests, 2 skipped, and 472 subtests.
- `git diff --check` passed.
- `python -m compileall .agents/pipeline-core/scripts` passed.
- `featurectl.py validate --planning-package --readiness` passed.
- `featurectl.py implementation-ready` passed in the feature worktree.
- `featurectl.py validate --evidence` passed.

## Verification Debt

- The real Codex behavioral e2e is still opt-in and was not executed in the
  deterministic local verification pass.
- Historical canonical execution journals were not globally migrated; active
  workspaces now get stricter validation.

## Claim Provenance

- Step/gate safety claims map to `featurectl_core/cli.py` and focused tests in
  `test_featurectl_core.py` and `test_gates_and_evidence.py`.
- Event, execution, and Docs Consulted validation claims map to
  `featurectl_core/validation.py`, `validators/execution_log.py`, and
  `test_planning_readiness.py`.
- Worktree/readiness claims map to `test_worktree_status.py` and
  `pipeline-lab/manual-check/preflight.sh`.
- Real e2e planning-only claims map to
  `tests/feature_pipeline/test_real_codex_conversation.py`.
- Runner fidelity claims map to
  `pipeline-lab/showcases/scripts/run_codex_e2e_case.py` and
  `test_codex_e2e_runner.py`.
- CI claims map to `.github/workflows/pipeline-guardrails.yml` and
  `test_artifact_formatting.py`.

## Rollback Guidance

If the transition or gate dependency enforcement blocks a legitimate workflow,
revert the specific helper check in `featurectl_core/cli.py` and keep the tests
that assert real e2e source-diff safety and active `events.yaml` presence.

If dirty-base detection is too strict in downstream repositories, adjust
`generated_pipeline_bootstrap_dirty()` before weakening the default dirty
checkout failure.

## Shared Knowledge Updates

- `.ai/knowledge/architecture-overview.md`: should record that state and gate
  ordering are command-enforced.
- `.ai/knowledge/testing-overview.md`: should record the opt-in real Codex e2e
  split and the deterministic CI full-suite job.
- `.ai/knowledge/module-map.md`: should record the new `implementation-ready`
  command and validator responsibilities.
- `.ai/knowledge/integration-map.md`: should record outcome-smoke partial
  fidelity labels for showcase reports.
