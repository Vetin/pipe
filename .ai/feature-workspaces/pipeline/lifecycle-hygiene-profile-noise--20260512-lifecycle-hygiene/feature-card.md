# Feature Card: pipeline/lifecycle-hygiene-profile-noise

Lifecycle, execution, profile, and policy source-of-truth hardening for the Native Feature Pipeline.

## Manual Validation

- `python -m pytest tests/feature_pipeline` passed with 128 tests.
- `python pipeline-lab/showcases/scripts/validate_pipeline_goals.py --passes 3 --report /tmp/lifecycle-goals.md` passed with zero failures.
- `featurectl.py validate` passed for existing canonical pipeline features and promoted-readonly workspaces.

## Verification Debt

None for the implemented scope. Future maintainability work should split `featurectl.py` into modules and can use this feature as the lifecycle baseline.

## Claim Provenance

- Lifecycle claims map to `featurectl.py`, `test_finish_promote.py`, and migrated `.ai/feature-workspaces/pipeline/*/{feature.yaml,state.yaml}`.
- Execution hygiene claims map to `featurectl.py`, `test_gates_and_evidence.py`, `test_finish_promote.py`, and normalized `execution.md` artifacts.
- Profile split claims map to `featurectl.py`, `test_featurectl_core.py`, `.ai/knowledge/features-overview.md`, and `.ai/knowledge/discovered-signals.md`.
- Policy claims map to `AGENTS.md`, `project-init/SKILL.md`, `skills/native-feature-pipeline/references/README.md`, `.ai/constitution.md`, and `test_agents_policy.py`.

## Rollback Guidance

Revert the feature commits if the stricter lifecycle validation blocks an urgent unrelated change. If reverting only the profile split, restore `render_features_overview` and remove `discovered-signals.md`; if reverting only idempotency, remove the duplicate-complete guard and retry event logic.

## Shared Knowledge Updates

- `.ai/knowledge/features-overview.md`: canonical feature memory remains separate from detected signals.
- `.ai/knowledge/discovered-signals.md`: stores low-confidence discovered feature/catalog signals.
- `.ai/knowledge/architecture-overview.md`: reflects stricter feature topology and knowledge-update expectations from the regenerated profile.
- `.ai/knowledge/module-map.md`: reflects filtered source and test surfaces after generated showcase/run exclusions.
- `.ai/knowledge/integration-map.md`: reflects filtered integration/deployment examples after generated noise removal.
