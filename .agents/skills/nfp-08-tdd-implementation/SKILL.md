---
name: nfp-08-tdd-implementation
description: Implement slices through mandatory subagent flow with red-green evidence and review.
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 08 TDD Implementation

Use this skill to implement slices with mandatory Superpowers-style subagent
execution, red-green-refactor evidence, and two-stage review.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Apply `skills/native-feature-pipeline/references/upstream-pattern-map.md` as the behavioral synthesis of cloned upstream methodologies; cite patterns in `Docs Consulted:` when they influence a decision.
- Apply `.agents/pipeline-core/references/methodology-lenses.md` for the TDD
  law, evidence order, failure triage, claim provenance, and eval run metadata.
- Apply `skills/superpowers/subagent-driven-development/SKILL.md`,
  `skills/superpowers/subagent-driven-development/implementer-prompt.md`,
  `skills/superpowers/subagent-driven-development/spec-reviewer-prompt.md`, and
  `skills/superpowers/subagent-driven-development/code-quality-reviewer-prompt.md`
  as the mandatory controller/implementer/reviewer flow.
- Confirm the current directory is the feature worktree.
- Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`, and
  `slices.yaml`.
- Load the TDD implementation docset with
  `featurectl.py load-docset --step tdd-implementation`.
- Use `skills/native-feature-pipeline/references/review-and-verification.md`,
  `skills/native-feature-pipeline/references/evaluation-patterns.md`, and
  `.agents/pipeline-core/references/skill-power-validation-policy.md`.
- Record `Docs Consulted: TDD Implementation` in `execution.md`.

Responsibilities:

- act as the controller for implementation, not as the direct implementer
- dispatch one fresh implementer subagent per slice with the full slice text,
  current artifact context, constraints, evidence requirements, and exact
  acceptance criteria
- require every implementer subagent to return one of `DONE`,
  `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`
- run spec-compliance review subagents before code-quality review subagents
- loop reviewer findings back to the same implementer until both review stages
  approve the slice
- never dispatch implementation subagents in parallel and never move to the next
  slice while the current slice has open review issues
- record pre-red git state
- write failing test first
- do not write production code for a slice until its focused red test has
  failed for the expected reason
- triage wrong red failures before implementation
- store raw red, green, and verification outputs under `evidence/`
- record evidence through `featurectl.py record-evidence`
- complete slices only after evidence order is valid
- commit each completed slice or record a diff hash
- update future slices when implementation changes dependencies, ownership,
  conflict risk, or test strategy

Subagent Flow Is Mandatory:

- If the host agent supports subagents, use them for every implementation and
  review task. There is no local/direct implementation fallback.
- If subagents are unavailable, stop and record a blocker in `execution.md`
  instead of implementing the slice directly.
- The controller may inspect files, run status/validation commands, and update
  pipeline metadata, but production code and tests must be authored by the
  slice implementer subagent.
- Each implementer prompt must include the complete slice text from
  `slices.yaml`; do not tell an implementer to read the whole plan and infer its
  task.
- Reviewer prompts must include the relevant slice requirements, artifact paths,
  implementer report, changed files, and evidence paths.
- A slice is complete only after red, green, verification, spec review, code
  quality review, commit or diff hash, and `featurectl.py complete-slice`.

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

Per slice controller loop:

1. Extract the next pending slice from `slices.yaml` with its full text,
   dependencies, requirement links, file ownership, conflict risk, test
   strategy, TDD commands, expected failure, review focus, and current
   downstream assumptions.
2. Dispatch a fresh implementer subagent using
   `skills/superpowers/subagent-driven-development/implementer-prompt.md`.
   Include the slice text directly plus the feature workspace path, repo root,
   pipeline contract, docs consulted, and the requirement to commit or return a
   diff hash.
3. Require the implementer to record pre-red git state, write the failing test
   first, run the red command, verify the expected failure, store red evidence,
   implement the minimum code needed, run green, store green evidence, run
   independent verification, store verification evidence, self-review, and
   report changed files and evidence paths.
4. Handle implementer status:
   - `DONE`: continue to spec review.
   - `DONE_WITH_CONCERNS`: continue only if concerns are non-blocking and are
     recorded in `execution.md`; otherwise send the concerns back to the same
     implementer.
   - `NEEDS_CONTEXT`: provide the missing context if it is already in artifacts
     or repository docs, then resume the same implementer.
   - `BLOCKED`: record the blocker, mark affected artifacts stale if the plan is
     wrong, and stop rather than guessing.
5. Dispatch a spec-compliance reviewer subagent using
   `skills/superpowers/subagent-driven-development/spec-reviewer-prompt.md`.
   The reviewer checks only whether the implementation satisfies the slice,
   feature contract, architecture, tech design, acceptance criteria, evidence
   order, and scope boundaries.
6. If spec review finds issues, send those findings back to the same
   implementer, then re-run the same spec reviewer role until it approves.
7. Dispatch a code-quality reviewer subagent using
   `skills/superpowers/subagent-driven-development/code-quality-reviewer-prompt.md`.
   The reviewer checks maintainability, repo conventions, risk, tests, and
   integration quality after spec compliance has passed.
8. If code-quality review finds issues, send those findings back to the same
   implementer, then repeat spec compliance review followed by code-quality
   review until both approve.
9. Commit the slice or compute a diff hash, then run
   `featurectl.py complete-slice`.
10. Run `featurectl.py validate --workspace <workspace> --implementation`.
11. Update later slices if this slice changed dependencies, ownership, conflict
    risk, or test strategy.
12. Append a resume checkpoint to `execution.md` with implementer status,
    reviewer outcomes, changed files, evidence paths, commit or diff hash,
    failure classifications, and next action.

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

When all planned slices are complete:

1. Dispatch a final code-quality reviewer subagent across the complete feature
   branch, all changed files, all slice evidence, and the final verification
   command set.
2. Resolve all final reviewer findings through the same implementer/re-review
   loop.
3. Run `featurectl.py validate --workspace <workspace> --implementation`.
4. Hand off to `nfp-09-review`.
