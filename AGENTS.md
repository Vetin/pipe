# Repository Agent Instructions

Use the Native Feature Pipeline for substantial feature work.

Use the pipeline for:

- new product features
- cross-module behavior changes
- security-sensitive behavior
- public API or contract changes
- architecture-affecting feature work
- large behavior-linked refactors

Do not require the full pipeline for trivial non-behavioral edits such as typo fixes,
formatting, tiny test cleanup, or one-line local bug fixes.

For feature work:

- start with `nfp-00-intake`
- create a dedicated git worktree for the feature
- keep feature artifacts and code changes inside that worktree
- use `apex.md`, `feature.yaml`, `state.yaml`, and `execution.md` to navigate
- use `.agents/pipeline-core/scripts/featurectl.py` for deterministic scaffolding,
  validation, gate state, staleness, evidence, and promotion
- do not write implementation code until feature contract, architecture, technical
  design, and slicing readiness gates are approved or explicitly delegated
- record clarifying questions, assumptions, docs consulted, approvals, scope
  changes, and next steps in `execution.md`

Do not create `approvals.yaml` or `handoff.md`; approval history belongs in
`execution.md`, and machine gate state belongs in `state.yaml`.
