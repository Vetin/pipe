# Artifact Model

## What To Borrow

- Spec-first requirements and acceptance criteria.
- Change-scoped architecture and technical design artifacts.
- ADRs for significant decisions only.
- Canonical feature memory after finish and promotion.

## What To Reject

- One giant specification file that becomes stale immediately.
- Machine state embedded in Markdown prose.
- Narrative artifacts written by deterministic scripts.

## Native Artifact Influence

- `feature.yaml`: identity, run id, branch, canonical path.
- `state.yaml`: minimal machine state, gates, stale flags, active slice.
- `execution.md`: run plan, questions, assumptions, docs consulted, decisions,
  scope changes, iteration ledger, next step.
- `feature-card.md`: compact retrieval memory for future agents.

## Native Skill Influence

`nfp-00` creates routing and state. `nfp-02` through `nfp-05` write planning.
`nfp-08` writes evidence. `nfp-11` writes feature memory. `nfp-12` promotes.

## Validation Rule Implied

Schemas must exist for machine-readable artifacts, and every completed feature
must include motivation, architecture, contracts, implementation slices, tests,
reviews, and evidence.
