---
name: nfp-06-readiness
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 06 Readiness

Use this skill to validate planning readiness before implementation.

Responsibilities:

- run `featurectl.py validate --readiness`
- summarize blockers, assumptions, stale artifacts, and missing gates
- ask for implementation approval or stop at the requested point

Keep readiness logic in deterministic validation where practical.

Workflow:

1. Confirm the current directory is the feature worktree.
2. Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`, `feature.md`,
   `architecture.md`, `tech-design.md`, and `slices.yaml`.
3. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace> --readiness
   ```

4. If validation fails, summarize blockers and stop.
5. If validation passes, summarize assumptions and ask for implementation
   approval unless the user already explicitly delegated that gate.

Implementation may start only when `feature_contract`, `architecture`,
`tech_design`, and `slicing_readiness` are approved or delegated.
