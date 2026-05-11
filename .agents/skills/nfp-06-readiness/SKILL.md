---
name: nfp-06-readiness
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 06 Readiness

Use this skill to validate planning readiness before implementation.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Confirm the current directory is the feature worktree.
- Read `apex.md`, `feature.yaml`, `state.yaml`, and `execution.md`.
- Load the readiness docset with `featurectl.py load-docset --step readiness`.
- Use `methodology/extracted/workflow-and-gates.md` and
  `.agents/pipeline-core/references/gate-policy.md`.
- Record `Docs Consulted: Readiness` in `execution.md`.

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
   python .agents/pipeline-core/scripts/featurectl.py load-docset --workspace <workspace> --step readiness
   ```

4. Append `Docs Consulted: Readiness` to `execution.md`.
5. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace> --readiness
   ```

6. If validation fails, summarize blockers and stop.
7. If validation passes, summarize assumptions and ask for implementation
   approval unless the user already explicitly delegated that gate.

Implementation may start only when `feature_contract`, `architecture`,
`tech_design`, and `slicing_readiness` are approved or delegated.

If approved or delegated, print:

```text
Next skill: nfp-07-worktree.
Continue with that skill.
```
