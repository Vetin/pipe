# Architecture: Guided Scenario score drift detector

## System Context
This feature targets `pipelinebench` with complexity `6`.

## Component Interactions
- CLI/user request enters the harness runner or skill.
- Domain logic updates the target module.
- Validation records evidence and shared-knowledge decisions.

## Feature Topology
```mermaid
flowchart LR
  User[Maintainer] --> Entry[pipelinebench entrypoint]
  Entry --> Logic[Feature logic]
  Logic --> Tests[Focused tests]
  Logic --> Reports[Artifacts and scorecards]
  Reports --> Knowledge[Shared knowledge decision table]
```

## Shared Knowledge Decision Table
| Knowledge file | Decision | Evidence | Future reuse |
| --- | --- | --- | --- |
| `.ai/knowledge/features-overview.md` | update after promotion with `Guided Scenario score drift detector` as validated lab behavior | feature-card.md and summary.yaml | future agents can discover the feature pattern without reading every scorecard |
| `.ai/knowledge/architecture-overview.md` | update topology notes for `pipelinebench` when promoted | architecture.md Mermaid topology | future architecture work can reuse affected module communication |
| `.ai/knowledge/module-map.md` | update changed surfaces: scorecards, showcase-summary.yaml, showcase-report.md | repo-context.md and slices.yaml | future slicing can reuse ownership and conflict-risk hints |
| `.ai/knowledge/integration-map.md` | confirm unchanged unless external integration appears during live implementation | tech-design.md security and integration notes | future agents do not infer an external dependency from this lab output |

## Security Model
No secrets, network calls, or external repository mutation are required.

## Failure Modes
- false positive drift
- unstable baselines

## Rollback Strategy
Remove generated artifacts for `08-guided-scenario-score-drift-detector` and revert source changes for `pipelinebench`.
