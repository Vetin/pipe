# Architecture Checklist

- Load the architecture docset.
- Reuse known module boundaries and existing ADRs when applicable.
- Document change delta: new, modified, removed, and unchanged behavior.
- Document system context and component interactions.
- Add `## Feature Topology` with a Mermaid flowchart/graph showing the
  high-level actor, entrypoint, services/modules, persistence, events, and
  external integration communication.
- Document security model, failure modes, observability, rollback, and risks.
- Document migration strategy when data, schema, contract, or deployment order
  changes.
- Document alternatives considered and why they were rejected.
- Document `## Shared Knowledge Impact` with `.ai/knowledge` paths that finish
  should update or explicitly preserve.
- Run a completeness/correctness/coherence check against `feature.md`.
- Create ADRs only for significant decisions.
- Record `Docs Consulted: Architecture` in `execution.md`.
