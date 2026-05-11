---
name: nfp-08-tdd-implementation
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 08 TDD Implementation

Use this skill to implement slices with red-green-refactor evidence.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Confirm the current directory is the feature worktree.
- Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`, and
  `slices.yaml`.
- Load the TDD implementation docset with
  `featurectl.py load-docset --step tdd-implementation`.
- Use `methodology/extracted/review-and-verification.md`,
  `methodology/extracted/evaluation-patterns.md`, and
  `.agents/pipeline-core/references/skill-power-validation-policy.md`.
- Record `Docs Consulted: TDD Implementation` in `execution.md`.

Responsibilities:

- record pre-red git state
- write failing test first
- store raw red, green, and verification outputs under `evidence/`
- record evidence through `featurectl.py record-evidence`
- complete slices only after evidence order is valid
- commit each completed slice or record a diff hash

Before implementation:

1. Change into the feature worktree root.
2. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py load-docset --workspace <workspace> --step tdd-implementation
   ```

3. Append `Docs Consulted: TDD Implementation` to `execution.md`.
4. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py worktree-status --workspace <workspace>
   ```

5. Stop immediately if it fails. Do not write tests, implementation code, or
   evidence until it passes.

Per slice:

1. Record pre-red git state.
2. Write the failing test first.
3. Run the slice red command.
4. Store raw red output with `featurectl.py record-evidence`.
5. Implement the minimum code needed for green.
6. Run the slice green command.
7. Store raw green output with `featurectl.py record-evidence`.
8. Run verification commands.
9. Store raw verification output with `featurectl.py record-evidence`.
10. Run review and store review evidence.
11. Commit the slice or compute a diff hash.
12. Run `featurectl.py complete-slice`.
13. Run `featurectl.py validate --workspace <workspace> --implementation`.

If implementation reveals the plan is wrong, stop, write `scope-change.md`, mark
affected artifacts stale, and return to the correct earlier skill.

Iteration Loop Protocol:

- Maintain durable `execution.md` entries for each implementation loop with
  `iteration_id`, slice ID, planned command, result, failure class, decision,
  files changed, evidence path, and next action.
- Support at least `I-001` through `I-010` without losing state.
- Every failed red, green, verification, or review step must be classified as
  one of `test_expected`, `implementation_bug`, `test_bug`, `design_gap`,
  `scope_change`, `environment_failure`, or `flaky`.
- Allowed decisions are: continue same slice, split slice, mark downstream
  artifacts stale, mark affected artifacts stale, return to design, return to
  slicing, stop for user approval, or complete slice.
- Add a resume checkpoint after each iteration so another agent can continue
  from `execution.md`, `state.yaml`, `slices.yaml`, and `evidence/` without the
  chat transcript.
- If an iteration changes behavior, architecture, technical design, or slice
  boundaries, stop implementation and use the scope-change mechanism before
  continuing.

When all planned slices are complete, hand off to `nfp-09-review`.
