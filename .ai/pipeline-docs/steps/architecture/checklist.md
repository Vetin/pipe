# Architecture Checklist

- Load the architecture docset.
- Reuse known module boundaries and existing ADRs when applicable.
- Document change delta: new, modified, removed, and unchanged behavior.
- Document system context and component interactions.
- Document security model, failure modes, observability, rollback, and risks.
- Document migration strategy when data, schema, contract, or deployment order
  changes.
- Document alternatives considered and why they were rejected.
- Run a completeness/correctness/coherence check against `feature.md`.
- Create ADRs only for significant decisions.
- Record `Docs Consulted: Architecture` in `execution.md`.
