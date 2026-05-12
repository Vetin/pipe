# Architecture: Traceable Evidence timeline export

## System Context
This feature targets `evidence` with complexity `10`.

## Component Interactions
- CLI/user request enters the harness runner or skill.
- Domain logic updates the target module.
- Validation records evidence and shared-knowledge decisions.

## Feature Topology
```mermaid
flowchart LR
  User[Maintainer] --> Entry[evidence entrypoint]
  Entry --> Logic[Feature logic]
  Logic --> Tests[Focused tests]
  Logic --> Reports[Artifacts and scorecards]
  Reports --> Knowledge[Shared knowledge decision table]
```

## Shared Knowledge Decision Table
| Knowledge file | Decision | Evidence | Future reuse |
| --- | --- | --- | --- |
| `.ai/knowledge/features-overview.md` | update after promotion with `Traceable Evidence timeline export` as validated lab behavior | feature-card.md and summary.yaml | future agents can discover the feature pattern without reading every scorecard |
| `.ai/knowledge/architecture-overview.md` | update topology notes for `evidence` when promoted | architecture.md Mermaid topology | future architecture work can reuse affected module communication |
| `.ai/knowledge/module-map.md` | update changed surfaces: execution.md, reviews/, evidence/manifest.yaml | repo-context.md and slices.yaml | future slicing can reuse ownership and conflict-risk hints |
| `.ai/knowledge/integration-map.md` | confirm unchanged unless external integration appears during live implementation | tech-design.md security and integration notes | future agents do not infer an external dependency from this lab output |

## Security Model
No secrets, network calls, or external repository mutation are required.

## Failure Modes
- missing failed attempt
- unlinked command output

## Rollback Strategy
Remove generated artifacts for `04-traceable-evidence-timeline-export` and revert source changes for `evidence`.
