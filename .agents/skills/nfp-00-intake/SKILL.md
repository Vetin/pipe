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
- stop if the domain is unclear, the intent is too ambiguous, or the user asks
  for full automation without delegation boundaries

Workflow:

1. Extract `domain`, `title`, and optional aliases from the request.
2. Ask only if `domain` or feature intent cannot be inferred safely.
3. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py new --domain <domain> --title "<title>"
   ```

4. Change into the created feature worktree for all later feature work.
5. Read the workspace `apex.md`, `feature.yaml`, `state.yaml`, and
   `execution.md`.
6. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace>
   ```

Do not write implementation code in this step.
