# Workflow And Gates

## What To Borrow

- Gate planning before implementation.
- Separate delegated approval from completed implementation.
- Record all gate changes in the execution log.
- Return to earlier steps when scope changes invalidate downstream artifacts.

## What To Reject

- Treating drafted artifacts as approved.
- Auto-approving implementation readiness.
- Continuing after security, business, or destructive-operation ambiguity.

## Native Artifact Influence

`state.yaml.gates`, `state.yaml.stale`, `execution.md`, `scope-change.md`, and
`evidence/manifest.yaml`.

## Native Skill Influence

`nfp-06-readiness`, `nfp-07-worktree`, `nfp-08-tdd-implementation`,
`nfp-09-review`, and `nfp-10-verification`.

## Validation Rule Implied

Implementation is blocked unless feature, architecture, tech design, and slicing
gates are approved or delegated. Red evidence must precede green evidence.
