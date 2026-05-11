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
