# Feature Card: pipeline/random-feature-stress-lab

## Intent

Create a deterministic stress lab that generates ten varied harness-pipeline
feature requests, rebuilds them across ten iterations, compares shared
knowledge documentation, applies skill improvements, and proves no final
improvements remain.

## Requirements

- FR-001: Generate ten deterministic random feature requests.
- FR-002: Rebuild and score all ten generated features for at least ten iterations.
- FR-003: Validate artifacts, topology, feature cards, rollback notes, and mistakes.
- FR-004: Apply discovered pipeline skill improvement and prove final clean state.
- FR-005: Produce side-by-side, improvement, rollback, and summary artifacts.
- FR-006: Report zero final open improvements.

## Architecture

The lab adds `run_random_feature_stress.py`, which writes final feature artifacts
and 100 scorecards under `pipeline-lab/showcases/random-feature-stress-runs`.
Architecture and finish skills/templates now require explicit shared knowledge
decision tables.

## Contracts

The primary machine contract is
`pipeline-lab/showcases/random-feature-stress-runs/20260512-random-stress/summary.yaml`.

## Slices

- S-001: Deterministic ten-feature stress runner.
- S-002: Shared knowledge decision table skill improvement.
- S-003: Validation report, final run, and project knowledge refresh.

## Tests And Evidence

- `python -m unittest tests.feature_pipeline.test_random_feature_stress`
- `python -m unittest tests.feature_pipeline.test_random_feature_stress tests.feature_pipeline.test_pipeline_goal_validation tests.feature_pipeline.test_methodology_contract`
- `python pipeline-lab/showcases/scripts/validate_pipeline_goals.py --passes 3`
- `python -m unittest discover tests/feature_pipeline`

## Manual Validation

Inspected the generated feature list, side-by-side report, improvement plan,
rollback plan, and representative generated architecture/feature-card artifacts.

## Reviews

`reviews/random-stress-review.yaml` records a non-blocking adversarial review
with verification command and file references.

## Verification Debt

None for deterministic local validation. Live Codex CLI replay against cloned
repositories remains a future extension.

## Claim Provenance

- Ten generated features: `feature-list.yaml`.
- 100 scorecards: `iterations/iteration-*/scorecards/*.yaml`.
- Shared knowledge comparison: `side-by-side.md`.
- Improvement result: `improvement-plan.md`.
- Rollback scope: `rollback-plan.md`.

## Rollback Guidance

No target repositories were mutated. Remove the generated run directory and
revert the runner, tests, and skill/template wording to roll back this feature.

## Shared Knowledge Updates

### Shared Knowledge Decision Table

| Knowledge file | Decision | Evidence | Future reuse |
| --- | --- | --- | --- |
| `.ai/knowledge/features-overview.md` | confirm unchanged before final main-branch `/init`; stress outputs remain lab artifacts, not product feature memory | final stress summary and this feature card | future agents find generated cases through showcase reports |
| `.ai/knowledge/architecture-overview.md` | refresh with `/init` after merge to account for the new runner and skill/template source changes | `featurectl.py init --profile-project` | future architecture work sees stress lab boundaries |
| `.ai/knowledge/module-map.md` | refresh with `/init` after merge to account for new script and test files | `featurectl.py init --profile-project` | future slicing sees `pipeline-lab` and `tests` ownership |
| `.ai/knowledge/integration-map.md` | confirm unchanged; no external integration or target repo mutation was added | rollback plan and tech design | future agents do not infer network or cloned-repo changes |

## Plan Drift

The implementation remained in scope. The only discovered improvement was the
shared knowledge decision-table requirement, applied to architecture and finish
skills/templates before the final stress run.

## Known Risks

The lab is deterministic and offline; it complements but does not replace live
Codex CLI implementation in cloned repositories.

## Future Modification Notes

Add a later mode that uses the same generated feature list to launch local Codex
CLI sessions against cloned showcase repositories, then compare live outputs
with this deterministic baseline.
