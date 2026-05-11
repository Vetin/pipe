---
name: nfp-00-intake
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 00 Intake

Use this skill to start a new Native Feature Pipeline run.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Apply `skills/native-feature-pipeline/references/upstream-pattern-map.md` as the behavioral synthesis of cloned upstream methodologies; cite patterns in `Docs Consulted:` when they influence a decision.
- Apply `.agents/pipeline-core/references/methodology-lenses.md` for adaptive
  rigor, ambiguity scoring, bounded clarification, and eval-style state.
- Load the intake docset with `featurectl.py load-docset --step intake` after
  the workspace exists.
- Use `skills/native-feature-pipeline/references/methodology-summary.md`,
  `skills/native-feature-pipeline/references/workflow-and-gates.md`, and
  `.agents/pipeline-core/references/feature-identity-policy.md` to decide
  whether the request is safe to start.
- Record `Docs Consulted: Intake` in `execution.md`.

Responsibilities:

- parse the user feature request
- infer or ask for the semantic feature key
- classify rigor as minimal, standard, or comprehensive
- estimate ambiguity across functional scope, data model, UX, integrations,
  security/RBAC, edge cases, non-functional constraints, and completion signals
- ask at most five blocking clarification questions before creating downstream
  planning commitments
- run `featurectl.py new`
- confirm the feature worktree and workspace exist
- record the run plan and non-delegable checkpoints in `execution.md`
- set the next step to context
- stop if the domain is unclear, the intent is too ambiguous, or the user asks
  for full automation without delegation boundaries

Workflow:

1. Extract `domain`, `title`, and optional aliases from the request.
2. Classify rigor:
   - minimal for local low-risk changes with obvious tests
   - standard for normal cross-module product features
   - comprehensive for security, data loss, public API, compliance, billing,
     auth, migrations, irreversible changes, or unclear business rules
3. Estimate ambiguity from `methodology-lenses.md`. Stop and ask if ambiguity is
   above `0.40`, or if any security, destructive, public-contract, compliance,
   or data-ownership question is unresolved.
4. Ask only if `domain` or feature intent cannot be inferred safely. Keep
   clarification to the highest-impact blocking questions and record unanswered
   items as assumptions or blockers.
5. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py new --domain <domain> --title "<title>"
   ```

6. Change into the created feature worktree for all later feature work.
7. Read the workspace `apex.md`, `feature.yaml`, `state.yaml`, and
   `execution.md`.
8. Load the intake docset:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py load-docset --workspace <workspace> --step intake
   ```

9. Append docs consulted, rigor level, ambiguity score, clarification ledger,
   checkpoints, assumptions, stop condition, and the next step to
   `execution.md`.
10. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace>
   ```

Do not write feature prose, architecture, technical design, slices, or
implementation code in this step. If automatic handoff does not happen, print:

```text
Next skill: nfp-01-context.
Continue with that skill.
```
