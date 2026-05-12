# Repository Agent Instructions

Use the Native Feature Pipeline for substantial feature-building work in this
repository. A Codex session should automatically enter or resume the pipeline
when the request affects product behavior, architecture, security, public
contracts, validation flow, or generated pipeline artifacts.

## Automatic Pipeline Trigger

Treat the request as full pipeline work when it involves any of these:

- new product or platform features
- cross-module behavior changes
- security-sensitive behavior
- public API, schema, event, contract, migration, or integration changes
- architecture-affecting documentation or implementation
- behavior-linked refactors, even when framed as cleanup or improvement

Use the pipeline for pipeline self-modification when the change affects behavior, architecture, validation, generated artifacts, or user-facing workflow.
Use our own technology while changing it.

Use lightweight repair mode for narrow, low-risk work such as:

- one-file script bugfixes
- test-only fixes
- formatting
- typo fixes
- comment-only cleanup
- small fixture updates

Lightweight repair mode should still inspect relevant files, run focused tests,
and avoid touching unrelated artifacts. Escalate to the full pipeline if the
repair grows into behavior, architecture, contract, security, or generated
knowledge changes.

## Required Start Or Resume Sequence

For every pipeline-triggering request:

1. Run `featurectl.py init --profile-project` only when `.ai/knowledge` is missing, stale, or explicitly requested.
2. Inspect `.ai/knowledge/project-index.yaml`,
   `.ai/knowledge/features-overview.md`, `.ai/knowledge/discovered-signals.md`,
   `.ai/knowledge/module-map.md`, `.ai/knowledge/architecture-overview.md`,
   `.ai/knowledge/testing-overview.md`,
   `.ai/knowledge/contracts-overview.md`, and
   `.ai/knowledge/integration-map.md` before planning.
3. If a matching active feature workspace exists, continue it from
   `apex.md`, `feature.yaml`, `state.yaml`, and `execution.md`.
4. If no matching workspace exists, create one with `featurectl.py new` and a
   dedicated feature worktree before writing feature code or behavior-changing
   docs.
5. Move through the Native Feature Pipeline from `nfp-00-intake` to
   `nfp-12-promote`. Do not skip gates silently.
6. Load the matching docset for each step with `featurectl.py load-docset`.
7. Mutate machine state only through `featurectl.py`; record narrative work in
   `execution.md`.
8. Run `featurectl.py validate --workspace <workspace>` after each checkpoint.
9. For implementation slices, use the subagent-first flow described in
   `nfp-08-tdd-implementation`; if subagents are unavailable, record the
   fallback reason in `execution.md`.
10. Finish with fresh verification, `feature-card.md`, shared knowledge
    updates, promotion or archived-variant promotion, and a commit.

## Guardrails

- Do not write implementation code until feature contract, architecture,
  technical design, and slicing readiness gates are approved or explicitly
  delegated in `state.yaml`.
- If `featurectl.py` or required pipeline files are broken, repair only the
  minimum needed to run `init`, `new`, and `validate`, then re-enter the
  pipeline and record the repair in `execution.md`.
- If the current checkout is already dirty, inspect the diff before continuing
  and do not overwrite unrelated user changes.
- Do not create `approvals.yaml` or `handoff.md`; approval history belongs in
  `execution.md`, and machine gate state belongs in `state.yaml`.

## Native Prompt Rule

External or nested Codex prompts should describe the desired feature outcome in
plain language and point at the repository. They should not ask the user to
manually invoke each internal `nfp-*` skill. The agent discovers and follows the
pipeline from this file, `.agents`, `.ai/pipeline-docs`, and `skills`.
