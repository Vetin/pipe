---
name: nfp-10-verification
description: Run final verification across tests, artifacts, evidence, and remaining delivery risks.
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 10 Verification

Use this skill to run final verification.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Apply `skills/native-feature-pipeline/references/upstream-pattern-map.md` as the behavioral synthesis of cloned upstream methodologies; cite patterns in `Docs Consulted:` when they influence a decision.
- Apply `.agents/pipeline-core/references/methodology-lenses.md` for evidence
  before claims, manual/UAT validation, verification debt, and fresh final
  verification.
- Confirm the current directory is the feature worktree.
- Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`,
  `feature.md`, `architecture.md`, `tech-design.md`, `slices.yaml`, and
  `reviews/*.yaml`.
- Load the verification docset with
  `featurectl.py load-docset --step verification`.
- Use `skills/native-feature-pipeline/references/review-and-verification.md`,
  `.agents/pipeline-core/references/quality-rubric.md`, and
  `.agents/pipeline-core/references/gate-policy.md`.
- Record `Docs Consulted: Verification` in `execution.md`.

Responsibilities:

- read verification commands from `.ai/constitution.md`
- run tests, lint, typecheck, build, and configured contract/security checks
- store raw outputs under `evidence/`
- write verification review
- record manual or UAT validation for user-visible workflows
- record verification debt when a command cannot run, with reason, risk, owner,
  and follow-up

Workflow:

1. Confirm worktree status.
2. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py load-docset --workspace <workspace> --step verification
   ```

3. Append `Docs Consulted: Verification` to `execution.md`.
4. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace> --review
   ```

5. Stop if critical review findings block verification.
6. Run verification commands from `.ai/constitution.md`.
7. Store raw final output in `evidence/final-verification-output.log`.
8. Run or document manual/UAT validation for relevant user workflows.
9. Write `reviews/verification-review.md` with `## Manual Validation` and
   `## Verification Debt` sections.
10. Set the verification gate to `complete` only when verification passes and
   verification debt is either absent or explicitly accepted as residual risk.
11. Run `featurectl.py validate --workspace <workspace>`.

Loop-aware verification:

- Record each verification attempt in `execution.md` or
  `verification-attempts.md` with command, result, failure class, decision, and
  next action.
- Classify failures as `implementation_bug`, `test_bug`, `design_gap`,
  `scope_change`, `environment_failure`, or `flaky`.
- Final verification must prove all completed slices still pass together, not
  only the last touched slice.
- Final verification must run after the last implementation or review iteration.

If verification passes, hand off to `nfp-11-finish`.
