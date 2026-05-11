---
name: nfp-07-worktree
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 07 Worktree

Use this skill to confirm implementation is running in the correct feature
worktree.

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
   python .agents/pipeline-core/scripts/featurectl.py worktree-status --workspace <workspace>
   ```

4. Stop immediately if it fails. Do not run tests, write implementation code, or
   record evidence until the command passes.
5. If it passes, hand off to `nfp-08-tdd-implementation`.
