---
name: nfp-00-intake
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 00 Intake

Use this skill to start a new Native Feature Pipeline run.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Apply `methodology/extracted/upstream-pattern-map.md` as the behavioral synthesis of cloned upstream methodologies; cite patterns in `Docs Consulted:` when they influence a decision.
- Load the intake docset with `featurectl.py load-docset --step intake` after
  the workspace exists.
- Use `methodology/extracted/methodology-summary.md`,
  `methodology/extracted/workflow-and-gates.md`, and
  `.agents/pipeline-core/references/feature-identity-policy.md` to decide
  whether the request is safe to start.
- Record `Docs Consulted: Intake` in `execution.md`.

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
6. Load the intake docset:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py load-docset --workspace <workspace> --step intake
   ```

7. Append docs consulted, checkpoints, assumptions, and the next step to
   `execution.md`.
8. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace>
   ```

Do not write feature prose, architecture, technical design, slices, or
implementation code in this step. If automatic handoff does not happen, print:

```text
Next skill: nfp-01-context.
Continue with that skill.
```
