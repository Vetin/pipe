# Feature Card: Guardrail Polish And Backlog Tracking

## Implementation

- Added `.github/workflows/pipeline-guardrails.yml` for wrapper help,
  compileall, artifact formatting tests, and public raw line-count checks.
- Added artifact tests that reject repeated blank-line YAML noise.
- Added top-level `additionalProperties: false` to `events.schema.json`.
- Added event sidecar validation for unexpected top-level fields.
- Changed generated `execution.md` event summaries to concise human prose.
- Split gate, slice, and worktree validators out of `validation.py`.
- Added `.ai/knowledge/pipeline-backlog.md`.

## Manual Validation

- `python -m pytest tests/feature_pipeline/test_artifact_formatting.py -q`
  passed.
- `python -m pytest tests/feature_pipeline/test_gates_and_evidence.py -q`
  passed.
- `python -m pytest tests/feature_pipeline/test_finish_promote.py
  tests/feature_pipeline/test_gates_and_evidence.py -q` passed.
- `python -m pytest tests/feature_pipeline -q` passed with 172 tests and
  383 subtests.

## Verification Debt

- Historical canonical execution journals were not globally migrated.
- Showcase/demo code remains in `pipelinebench_core/showcases.py`.
- Promotion event metadata expansion remains future work.
- These items are tracked centrally in `.ai/knowledge/pipeline-backlog.md`.

## Claim Provenance

- Public raw permanence is backed by `.github/workflows/pipeline-guardrails.yml`
  and `tests/feature_pipeline/test_artifact_formatting.py`.
- Event strictness is backed by `events.schema.json`,
  `featurectl_core/validators/events.py`, and gate/evidence tests.
- Narrative execution behavior is backed by `featurectl_core/events.py` and
  `tests/feature_pipeline/test_gates_and_evidence.py`.
- Validator modularity is backed by `featurectl_core/validators/gates.py`,
  `slices.py`, `worktree.py`, and artifact formatting tests.

## Rollback Guidance

Revert the slice commits in reverse order. CI workflow removal restores the
previous local-only public raw guardrail. Event schema top-level strictness can
be relaxed by removing the schema and validator checks. The validator split can
be reverted by moving helpers back into `validation.py`.

## Shared Knowledge Updates

- `.ai/knowledge/architecture-overview.md` should describe the permanent raw
  guardrail and narrative/event boundary.
- `.ai/knowledge/module-map.md` should list the new validator modules.
- `.ai/knowledge/integration-map.md` should mention the GitHub Actions
  guardrail.
- `.ai/knowledge/pipeline-backlog.md` now tracks accepted verification debt.

## Plan Drift

No scope expansion was required. The only deferred item is splitting
`pipelinebench_core/showcases.py`, which remains tracked as backlog.
