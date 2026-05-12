# Architecture: Auditable Mermaid topology coverage report

## System Context
This feature targets `architecture` with complexity `7`.

## Component Interactions
- CLI/user request enters the harness runner or skill.
- Domain logic updates the target module.
- Validation records evidence and shared-knowledge decisions.

## Feature Topology
```mermaid
flowchart LR
  User[Maintainer] --> Entry[architecture entrypoint]
  Entry --> Logic[Feature logic]
  Logic --> Tests[Focused tests]
  Logic --> Reports[Artifacts and scorecards]
  Reports --> Knowledge[Shared knowledge decision table]
```

## Shared Knowledge Decision Table
| Knowledge file | Decision | Evidence | Future reuse |
| --- | --- | --- | --- |
| `.ai/knowledge/features-overview.md` | update after promotion with `Auditable Mermaid topology coverage report` as validated lab behavior | feature-card.md and summary.yaml | future agents can discover the feature pattern without reading every scorecard |
| `.ai/knowledge/architecture-overview.md` | update topology notes for `architecture` when promoted | architecture.md Mermaid topology | future architecture work can reuse affected module communication |
| `.ai/knowledge/module-map.md` | update changed surfaces: validation reports, architecture.md, diagrams/ | repo-context.md and slices.yaml | future slicing can reuse ownership and conflict-risk hints |
| `.ai/knowledge/integration-map.md` | confirm unchanged unless external integration appears during live implementation | tech-design.md security and integration notes | future agents do not infer an external dependency from this lab output |

## Security Model
No secrets, network calls, or external repository mutation are required.

## Failure Modes
- blank diagram
- generic service boxes

## Rollback Strategy
Remove generated artifacts for `05-auditable-mermaid-topology-coverage-report` and revert source changes for `architecture`.
