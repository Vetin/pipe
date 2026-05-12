# Native Skill Protocol

Every production `nfp-*` skill follows the same operating contract:

1. Confirm the current checkout is the feature worktree, except intake before
   the worktree exists.
2. Read `apex.md`, `feature.yaml`, `state.yaml`, and `execution.md`.
3. Load the step docset with `featurectl.py load-docset`.
4. Read required docs first, including local runtime skill references and
   `.agents/pipeline-core/references/upstream-pattern-map.md`.
5. Record the docs actually used in `execution.md` under
   `Docs Consulted: <Step>`.
6. Update only artifacts owned by the current skill.
7. Mutate machine state only through `featurectl.py`.
8. Run `featurectl.py validate` before handoff.
9. Append completed work, decisions, blockers, and next step to
   `execution.md`.
10. Print the next skill if automatic handoff does not happen.

Skills must stop instead of guessing when ambiguity affects security,
business-critical behavior, destructive commands, credentials, production data,
or public contract compatibility.

Native invocation rule:

- A real user or reproducible E2E case should ask for the feature outcome in
  plain language and point at the repository. The agent may discover and follow
  the pipeline from `.agents` and `.ai/pipeline-docs`, but the outer prompt must
  not enumerate every internal `nfp-*` skill as a script.
- Direct skill names are valid inside skill docs, state, and evidence. They are
  not valid as the primary control plane for native showcase prompts.
- If a run installs pipeline tooling into another repository, it must copy
  `.agents`, `.ai/pipeline-docs`, and `skills` as context, then proceed through
  the normal repository workflow rather than asking the user to manually invoke
  each step.
