---
name: nfp-10-verification
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 10 Verification

Use this skill to run final verification.

Responsibilities:

- read verification commands from `.ai/constitution.md`
- run tests, lint, typecheck, build, and configured contract/security checks
- store raw outputs under `evidence/`
- write verification review

Workflow:

1. Confirm worktree status.
2. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace> --review
   ```

3. Stop if critical review findings block verification.
4. Run verification commands from `.ai/constitution.md`.
5. Store raw final output in `evidence/final-verification-output.log`.
6. Write `reviews/verification-review.md`.
7. Set the verification gate to `complete` only when verification passes.

Loop-aware verification:

- Record each verification attempt in `execution.md` or
  `verification-attempts.md` with command, result, failure class, decision, and
  next action.
- Classify failures as `implementation_bug`, `test_bug`, `design_gap`,
  `scope_change`, `environment_failure`, or `flaky`.
- Final verification must prove all completed slices still pass together, not
  only the last touched slice.
- Final verification must run after the last implementation or review iteration.
