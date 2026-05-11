---
name: nfp-00-intake
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 00 Intake

Use this skill to start a new Native Feature Pipeline run.

Responsibilities:

- parse the user feature request
- infer or ask for the semantic feature key
- run `featurectl.py new`
- confirm the feature worktree and workspace exist
- record the run plan and non-delegable checkpoints in `execution.md`
- set the next step to context

Do not write implementation code in this step.
