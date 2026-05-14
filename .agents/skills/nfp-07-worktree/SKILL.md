---
name: nfp-07-worktree
description: Verify feature worktree isolation, branch state, locks, and implementation safety.
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 07 Worktree

Use this skill to confirm implementation is running in the correct feature
worktree.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Apply `.agents/pipeline-core/references/upstream-pattern-map.md` as the behavioral synthesis of cloned upstream methodologies; cite patterns in `Docs Consulted:` when they influence a decision.
- Confirm the current directory is the feature worktree from
  `state.yaml.worktree.path`.
- Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`, and
  `slices.yaml`.
- Load the worktree docset with `featurectl.py load-docset --step worktree`.
- Use `.agents/pipeline-core/references/workflow-and-gates.md` and
  `.agents/pipeline-core/references/gate-policy.md`.
- Record `Docs Consulted: Worktree` in `execution.md`.

Responsibilities:

- verify current directory, branch, workspace path, and gate readiness
- block implementation when required planning gates are not approved or delegated
- run `featurectl.py worktree-status`

Workflow:

1. Change into the feature worktree root from `state.yaml.worktree.path`.
2. Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`, and
   `slices.yaml`.
3. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py load-docset --workspace <workspace> --step worktree
   ```

4. Append `Docs Consulted: Worktree` and checkpoint notes to `execution.md`.
5. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py worktree-status --workspace <workspace>
   ```

6. Stop immediately if it fails. Do not run tests, write implementation code, or
   record evidence until the command passes.
7. Run `featurectl.py validate --workspace <workspace> --implementation`.
8. If it passes, hand off to `nfp-08-tdd-implementation`.

If automatic handoff does not happen, print:

```text
Next skill: nfp-08-tdd-implementation.
Continue with that skill.
```

## Skill Contract

Inputs:
- `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`, approved planning
  gates, branch state, and current git status.

Owned artifacts:
- Worktree safety checkpoint notes in `execution.md`.

Forbidden actions:
- Do not implement code, create `approvals.yaml` or `handoff.md`, bypass dirty
  worktree blockers, or mutate `state.yaml` manually.

Validation command:
- `python .agents/pipeline-core/scripts/featurectl.py worktree-status --workspace <workspace>`

Docs consulted requirement:
- Append `Docs Consulted: Worktree` to `execution.md` with explicit path
  bullets, `Used for`, and `Confidence` entries.

Next step fallback:
- Print `Next skill: nfp-08-tdd-implementation` when automatic handoff does
  not happen.
