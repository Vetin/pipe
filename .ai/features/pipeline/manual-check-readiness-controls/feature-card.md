# Feature Card: pipeline/manual-check-readiness-controls

## Intent

Make the Native Feature Pipeline ready for meaningful manual checking by adding
real behavioral e2e scaffolding, explicit state-transition commands,
planning-only validation, stronger Docs Consulted proof, scope-change handling,
and uniform skill/artifact contracts.

## Implementation

- Added `featurectl.py step set` for controlled `state.yaml.current_step`
  transitions with `step_changed` events.
- Added `featurectl.py scope-change` to create `scope-change.md`, mark stale
  artifacts, return to an earlier step, and block implementation until resolved.
- Split planning validation into `--planning-package` and `--implementation`.
- Strengthened Docs Consulted validation to require explicit existing path
  bullets and non-empty `Used for` entries.
- Added manual preflight docs/script and an opt-in real Codex behavioral e2e
  test guarded by `RUN_REAL_CODEX_E2E=1`.
- Added uniform `## Skill Contract` sections across all `nfp-*` skills.
- Documented `events.yaml`, scope changes, readiness modes, and review
  YAML/Markdown boundaries in pipeline references.

## Manual Validation

Not run against a real Codex binary in this automated pass. The opt-in command
is documented:

```bash
RUN_REAL_CODEX_E2E=1 CODEX_BIN=codex \
  python -m pytest tests/feature_pipeline/test_real_codex_conversation.py -q
```

## Verification Debt

- Real Codex behavioral e2e remains opt-in because it depends on the local
  Codex CLI and can be slow or environment-sensitive.
- Human manual checking should run
  `pipeline-lab/manual-check/preflight.sh <workspace>` on representative
  workspaces before declaring the pipeline ready for broad manual rollout.

## Claim Provenance

- Step transition behavior: `tests/feature_pipeline/test_featurectl_core.py`.
- Planning readiness and scope-change behavior:
  `tests/feature_pipeline/test_planning_readiness.py`.
- Manual preflight and real Codex scaffold:
  `tests/feature_pipeline/test_manual_check_preflight.py` and
  `tests/feature_pipeline/test_real_codex_conversation.py`.
- Skill/artifact contract behavior:
  `tests/feature_pipeline/test_skill_contracts.py`.
- Final verification: `evidence/final-verification-output.log`.

## Rollback Guidance

Revert this feature branch or remove the new commands/tests/docs together. If
only the stricter Docs Consulted validation causes compatibility issues, revert
that validator change and keep the manual preflight and skill-contract docs.

## Shared Knowledge Updates

- `.ai/knowledge/architecture-overview.md`
  - Decision: updated control-plane architecture with manual-check readiness controls.
  - Evidence: this feature card and full test output.
  - Future reuse: future agents can find the official step, scope, and readiness boundary.
- `.ai/knowledge/pipeline-backlog.md`
  - Decision: added durable debt for regularizing real Codex behavioral runs.
  - Evidence: `test_real_codex_conversation.py` is opt-in.
  - Future reuse: manual rollout can distinguish deterministic confidence from
    real conversational confidence.
- `.agents/pipeline-core/references/artifact-model.md`
  - Decision: formalized `events.yaml`, `scope-change.md`, and review artifact boundaries.
  - Evidence: `test_skill_contracts.py`.
  - Future reuse: future skills can use one source-of-truth model.

## Plan Drift

The original plan expected these changes to be ready before manual checking.
Implementation added one extra compatibility fix: legacy fixtures now use
self-contained Docs Consulted paths so canonical promotion validation passes.
