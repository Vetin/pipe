# Native Skill Protocol

Every production `nfp-*` skill follows the same operating contract:

1. Confirm the current checkout is the feature worktree, except intake before
   the worktree exists.
2. Read `apex.md`, `feature.yaml`, `state.yaml`, and `execution.md`.
3. Load the step docset with `featurectl.py load-docset`.
4. Read required docs first, including methodology extraction docs.
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
