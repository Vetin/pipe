---
name: nfp-09-review
description: Run deterministic and adversarial review, record findings, and require fix verification.
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 09 Review

Use this skill to run deterministic and agentic review.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Apply `.agents/pipeline-core/references/upstream-pattern-map.md` as the behavioral synthesis of cloned upstream methodologies; cite patterns in `Docs Consulted:` when they influence a decision.
- Apply `.agents/pipeline-core/references/methodology-lenses.md` for
  adversarial review, hard/soft findings, zero-finding justification, and claim
  provenance.
- Confirm the current directory is the feature worktree.
- Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`,
  `feature.md`, `architecture.md`, `tech-design.md`, and `slices.yaml`.
- Load the review docset with `featurectl.py load-docset --step review`.
- Use `.agents/pipeline-core/references/review-and-verification.md`,
  `.agents/pipeline-core/references/evaluation-patterns.md`,
  `.agents/pipeline-core/references/subagent-review-policy.md`, and
  `.agents/pipeline-core/references/quality-rubric.md`.
- Record `Docs Consulted: Review` in `execution.md`.

Responsibilities:

- run deterministic validation through `featurectl.py validate --review`
- perform or delegate spec, code quality, security, architecture, contract, test,
  regression, and performance review according to the requested tier
- actively search for defects; do not treat review as confirmation
- separate hard findings that block verification from soft concerns that can be
  tracked as residual risk
- explain zero-finding reviews with inspected artifacts, commands, and risk
  lenses used
- write review files under `reviews/`
- write `reviews/*.yaml` for machine-readable findings and
  `reviews/*-review.md` Markdown summaries for human review narrative when a
  review lens needs explanation
- block verification for critical findings

Subagent Review Policy:

- If subagents are available, delegate strict or enterprise review lenses to
  review subagents with focused packets.
- If subagents are unavailable, use sequential main-agent fallback: run each
  review lens as a distinct pass, record `subagent_fallback_reason` in
  `execution.md`, and write the same structured review artifacts that a
  delegated reviewer would have produced.
- Fallback review must not rely on memory of implementation work. Re-read the
  relevant requirements, changed files, evidence, and verification commands
  before each pass.

Workflow:

1. Confirm worktree status.
2. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py load-docset --workspace <workspace> --step review
   ```

3. Append `Docs Consulted: Review` to `execution.md`.
4. Run:

   ```bash
   python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace>
   ```

5. Perform agentic review at one tier:
   - `basic_review`: spec compliance and code quality
   - `strict_review`: basic review plus security, contract, and test quality
   - `enterprise_review`: strict review plus performance, regression risk, and
     architecture compliance
6. Use at least these review lenses: requirement traceability, permission/RBAC,
   data loss or rollback, stale/replay/idempotency, test evidence, migration,
   observability, and plan drift.
7. Write structured findings as `reviews/*.yaml` using severity `critical`,
   `major`, `minor`, or `note`.
8. Write Markdown summaries as `reviews/*-review.md` when the review needs
   narrative context; `reviews/verification-review.md` remains required during
   verification.
9. Mark critical findings as `blocking: true`.
10. If no findings are written, create a note-level review record explaining why
   no blocking or soft findings remain and cite evidence.
11. Set the review gate to `blocked` if critical blocking findings exist;
   otherwise set it to `complete`.
12. Run `featurectl.py validate --workspace <workspace> --review`.

Critical findings block verification.

Structured finding requirements:

- `linked_requirement_ids`
- `linked_slice_ids`
- `file_refs`
- `reproduction_or_reasoning`
- `fix_verification_command`
- `re_review_required`

Review artifact boundary:

- `reviews/*.yaml` are required for machine-readable findings.
- `reviews/*-review.md` are Markdown summaries for human/LLM review narrative.
- Markdown summaries do not satisfy the review gate without YAML findings or a
  note-level YAML record.

Re-review loop:

- After fixes, update or add review evidence showing each blocking finding is
  resolved or explicitly deferred with user approval.
- Blocking findings must not be cleared only by editing severity; record the fix
  evidence and verification command.

If review passes, hand off to `nfp-10-verification`.

## Skill Contract

Inputs:
- `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`, `feature.md`,
  `architecture.md`, `tech-design.md`, `slices.yaml`, changed files, and
  `evidence/manifest.yaml`.

Owned artifacts:
- `reviews/*.yaml`, optional `reviews/*-review.md` Markdown summaries, review
  gate state, and review decisions in `execution.md`.

Forbidden actions:
- Do not clear critical findings by severity edits only, skip fix verification,
  create `approvals.yaml` or `handoff.md`, or mutate `state.yaml` manually.

Validation command:
- `python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace> --review`

Docs consulted requirement:
- Append `Docs Consulted: Review` to `execution.md` with explicit path bullets,
  `Used for`, and `Confidence` entries.

Next step fallback:
- Print `Next skill: nfp-10-verification` when automatic handoff does not
  happen.
