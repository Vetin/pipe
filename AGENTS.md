# Repository Agent Instructions

The Native Feature Pipeline is mandatory for feature-building work in this
repository. A Codex session must automatically enter or resume the pipeline when
the user asks to build, implement, add, change, or improve behavior.

## Automatic Pipeline Trigger

Treat the request as pipeline work when it involves any of these:

- new product or platform features
- changes to `.agents`, `.ai/pipeline-docs`, `skills`, `featurectl.py`,
  `pipelinebench.py`, showcase runners, validators, or pipeline tests
- cross-module behavior changes
- security-sensitive behavior
- public API, schema, event, contract, migration, or integration changes
- architecture-affecting documentation or implementation
- behavior-linked refactors, even when framed as "cleanup" or "improvement"

The pipeline is also required when this repository is improving the pipeline
itself. Use our own technology while changing it.

Skip the full pipeline only for truly trivial non-behavioral edits such as
typos, formatting, comment-only cleanup, or a one-line local test fixture fix.
If there is doubt, use the pipeline.

## Required Start Or Resume Sequence

For every pipeline-triggering request:

1. Refresh project knowledge first:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py init --profile-project
   ```

2. Inspect `.ai/knowledge/project-index.yaml`,
   `.ai/knowledge/features-overview.md`, `.ai/knowledge/module-map.md`,
   `.ai/knowledge/architecture-overview.md`, `.ai/knowledge/testing-overview.md`,
   `.ai/knowledge/contracts-overview.md`, and `.ai/knowledge/integration-map.md`
   before planning.
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
9. For implementation slices, use the mandatory subagent flow described in
   `nfp-08-tdd-implementation`.
10. Finish with fresh verification, `feature-card.md`, shared knowledge updates,
    promotion or archived-variant promotion, and a commit.

## Guardrails

- Do not write implementation code until feature contract, architecture,
  technical design, and slicing readiness gates are approved or explicitly
  delegated in `state.yaml`.
- Do not bypass the pipeline because a change is "internal" or "just pipeline
  tooling"; internal pipeline changes are first-class feature work here.
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
