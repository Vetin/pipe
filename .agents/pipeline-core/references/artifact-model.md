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
- `state.yaml`: minimal machine state, gates, stale flags, current step,
  lifecycle, active slice, and worktree identity.
- `events.yaml`: machine-readable event history and append-only replay source
  for gate changes, step transitions, scope changes, slice completion, review,
  verification, promotion, and public raw guardrails.
- `execution.md`: human-readable run journal for run plan, questions,
  assumptions, docs consulted, decisions, narrative event summaries,
  scope-change rationale, iteration ledger, and next action.
- `scope-change.md`: durable scope-change history when implementation or review
  discovers that earlier planning artifacts must be revisited.
- `feature-card.md`: compact retrieval memory for future agents.
- `architecture.md` and `tech-design.md`: the domain/logical design split, with
  invariants and state transitions separated from implementation interfaces,
  migrations, queues/jobs, feature flags, and verification surfaces.
- `slices.yaml`: dependency-aware task graph that links requirements to owned
  files, tests, red/green evidence, rollback notes, and status.

`events.yaml` is authoritative for machine-readable event replay.
`execution.md` remains the human-readable run journal. Validators may require
both, but agents should not maintain two competing machine logs.

`events.yaml` is required for active workspaces. Legacy canonical features that
do not yet have an event sidecar may remain read-only historical memory, but
they must be migrated before being reopened for active work. A future
`featurectl.py migrate-artifacts` command should handle historical conversion
without asking agents to hand-edit machine event history.

Review artifacts have two forms:

- `reviews/*.yaml` are machine-readable findings.
- `reviews/*-review.md` are Markdown summaries for human/LLM narrative.

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
