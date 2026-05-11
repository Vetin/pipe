# Artifact Model

## What To Borrow

- Spec-first requirements and acceptance criteria.
- Change-scoped architecture and technical design artifacts.
- ADRs for significant decisions only.
- Canonical feature memory after finish and promotion.
- Treat artifacts as contracts between phases, not prose dumps. Each artifact
  must expose the IDs, decisions, dependencies, risks, tests, and evidence the
  next phase needs.
- Make rollback and safety visible wherever an artifact can authorize data
  mutation, public contract changes, destructive automation, or irreversible
  promotion.

## What To Reject

- One giant specification file that becomes stale immediately.
- Machine state embedded in Markdown prose.
- Narrative artifacts written by deterministic scripts.
- Architecture or design documents generic enough to fit any codebase. They
  must name inspected modules, files, interfaces, and persistence surfaces.
- Slice lists without dependency and verification metadata.

## Native Artifact Influence

- `feature.yaml`: identity, run id, branch, canonical path.
- `state.yaml`: minimal machine state, gates, stale flags, active slice.
- `execution.md`: run plan, questions, assumptions, docs consulted, decisions,
  scope changes, iteration ledger, next step.
- `feature-card.md`: compact retrieval memory for future agents.
- `architecture.md` and `tech-design.md`: the domain/logical design split, with
  invariants and state transitions separated from implementation interfaces,
  migrations, queues/jobs, feature flags, and verification surfaces.
- `slices.yaml`: dependency-aware task graph that links requirements to owned
  files, tests, red/green evidence, rollback notes, and status.

## Native Skill Influence

`nfp-00` creates routing and state. `nfp-02` through `nfp-05` write planning.
`nfp-08` writes evidence. `nfp-11` writes feature memory. `nfp-12` promotes.
`nfp-03` and `nfp-04` preserve the domain/logical design split, while
`nfp-05` converts it into executable task graph slices.

## Validation Rule Implied

Schemas must exist for machine-readable artifacts, and every completed feature
must include motivation, architecture, contracts, implementation slices, tests,
reviews, and evidence.
Promoted memory must be reproducible from committed artifacts; chat-only
decisions do not count.
