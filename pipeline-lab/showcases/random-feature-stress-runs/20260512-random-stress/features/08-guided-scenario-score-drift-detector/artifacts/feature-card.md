# Feature Card: 08-guided-scenario-score-drift-detector

## Intent
Add guided scenario score drift detector to compare repeated benchmark runs and flag score drift by skill and scenario.

## Final Behavior
The final stress run documents `Guided Scenario score drift detector` with score `0.958`.

## Manual Validation
Review `summary.yaml`, scorecards, and generated artifacts.

## Verification Debt
None for the deterministic lab output.

## Claim Provenance
- Feature contract: `feature.md`
- Architecture: `architecture.md`
- Evidence: `evidence/manifest.yaml`

## Rollback Guidance
No target repositories were mutated. Remove the run directory to roll back generated artifacts.

## Shared Knowledge Updates

### Shared Knowledge Decision Table
| Knowledge file | Decision | Evidence | Future reuse |
| --- | --- | --- | --- |
| `.ai/knowledge/features-overview.md` | update after promotion with `Guided Scenario score drift detector` as validated lab behavior | feature-card.md and summary.yaml | future agents can discover the feature pattern without reading every scorecard |
| `.ai/knowledge/architecture-overview.md` | update topology notes for `pipelinebench` when promoted | architecture.md Mermaid topology | future architecture work can reuse affected module communication |
| `.ai/knowledge/module-map.md` | update changed surfaces: scorecards, showcase-summary.yaml, showcase-report.md | repo-context.md and slices.yaml | future slicing can reuse ownership and conflict-risk hints |
| `.ai/knowledge/integration-map.md` | confirm unchanged unless external integration appears during live implementation | tech-design.md security and integration notes | future agents do not infer an external dependency from this lab output |

## Plan Drift
No final plan drift remains after the decision-table improvement.
