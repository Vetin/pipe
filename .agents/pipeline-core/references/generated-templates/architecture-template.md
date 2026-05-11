# Architecture: <Title>

## Change Delta
## System Context
## Component Interactions
## Feature Topology
```mermaid
flowchart LR
  Actor[Actor] --> Entry[Feature entrypoint]
  Entry --> Service[Domain service/module]
  Service --> Store[(State or persistence)]
  Service --> Event[Event/audit path]
```
## Diagrams
## Security Model
## Failure Modes
## Observability
## Rollback Strategy
## Migration Strategy
## Architecture Risks
## Alternatives Considered
## Shared Knowledge Impact
- `.ai/knowledge/features-overview.md`:
- `.ai/knowledge/architecture-overview.md`:
- `.ai/knowledge/module-map.md`:
- `.ai/knowledge/integration-map.md`:
## Completeness Correctness Coherence
## ADRs
