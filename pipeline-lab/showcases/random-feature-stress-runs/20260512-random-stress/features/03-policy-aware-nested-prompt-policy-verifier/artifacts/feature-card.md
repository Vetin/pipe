# Feature Card: 03-policy-aware-nested-prompt-policy-verifier

## Intent
Add policy-aware nested prompt policy verifier to verify nested Codex prompts discover AGENTS.md and avoid direct internal skill invocation lists.

## Final Behavior
The final stress run documents `Policy-Aware Nested prompt policy verifier` with score `0.958`.

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
| `.ai/knowledge/features-overview.md` | update after promotion with `Policy-Aware Nested prompt policy verifier` as validated lab behavior | feature-card.md and summary.yaml | future agents can discover the feature pattern without reading every scorecard |
| `.ai/knowledge/architecture-overview.md` | update topology notes for `codex-e2e` when promoted | architecture.md Mermaid topology | future architecture work can reuse affected module communication |
| `.ai/knowledge/module-map.md` | update changed surfaces: prompt.md, run_codex_e2e_case.py, codex-output.log | repo-context.md and slices.yaml | future slicing can reuse ownership and conflict-risk hints |
| `.ai/knowledge/integration-map.md` | confirm unchanged unless external integration appears during live implementation | tech-design.md security and integration notes | future agents do not infer an external dependency from this lab output |

## Plan Drift
No final plan drift remains after the decision-table improvement.
