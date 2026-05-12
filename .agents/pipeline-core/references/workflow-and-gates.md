# Workflow And Gates

## What To Borrow

- Gate planning before implementation.
- Separate delegated approval from completed implementation.
- Record all gate changes in the execution log.
- Return to earlier steps when scope changes invalidate downstream artifacts.
- Make ambiguity measurable. Before planning, score unclear goal, boundary,
  constraints, and acceptance criteria; ask only about blocking gaps.
- Model tasks as a dependency graph. A slice can be ready only when upstream
  artifacts, prerequisites, and non-delegable checkpoints are satisfied.
- Treat implementation changes as scope events. If the code path diverges from
  the accepted design, update affected future slices before continuing.

## What To Reject

- Treating drafted artifacts as approved.
- Auto-approving implementation readiness.
- Continuing after security, business, or destructive-operation ambiguity.
- Using chat-only approval. Gate state must be present in `state.yaml` and the
  reason must be in `execution.md`.
- Promoting after a review that contains unresolved critical or high findings.

## Native Artifact Influence

`state.yaml.gates`, `state.yaml.stale`, `execution.md`, `scope-change.md`, and
`evidence/manifest.yaml`.

## Native Skill Influence

`nfp-06-readiness`, `nfp-07-worktree`, `nfp-08-tdd-implementation`,
`nfp-09-review`, and `nfp-10-verification`.

`nfp-00-intake` and `nfp-02-feature-contract` also inherit ambiguity gates:
they must stop when the feature would change money, data retention, security,
compliance, public APIs, or irreversible user data without explicit criteria.

## Validation Rule Implied

Implementation is blocked unless feature, architecture, tech design, and slicing
gates are approved or delegated. Red evidence must precede green evidence.
Native emulation must show all three states: initial ambiguity, improved prompt
constraints, and final pass with complete artifacts.
