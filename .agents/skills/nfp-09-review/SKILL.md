---
name: nfp-09-review
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 09 Review

Use this skill to run deterministic and agentic review.

Methodology:

- Read `.agents/pipeline-core/references/native-skill-protocol.md`.
- Apply `methodology/extracted/upstream-pattern-map.md` as the behavioral synthesis of cloned upstream methodologies; cite patterns in `Docs Consulted:` when they influence a decision.
- Confirm the current directory is the feature worktree.
- Read `apex.md`, `feature.yaml`, `state.yaml`, `execution.md`,
  `feature.md`, `architecture.md`, `tech-design.md`, and `slices.yaml`.
- Load the review docset with `featurectl.py load-docset --step review`.
- Use `methodology/extracted/review-and-verification.md`,
  `methodology/extracted/evaluation-patterns.md`,
  `.agents/pipeline-core/references/subagent-review-policy.md`, and
  `.agents/pipeline-core/references/quality-rubric.md`.
- Record `Docs Consulted: Review` in `execution.md`.

Responsibilities:

- run deterministic validation through `featurectl.py validate --review`
- perform or delegate spec, code quality, security, architecture, contract, test,
  regression, and performance review according to the requested tier
- write review files under `reviews/`
- block verification for critical findings

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
6. Write structured findings as `reviews/*.yaml` using severity `critical`,
   `major`, `minor`, or `note`.
7. Mark critical findings as `blocking: true`.
8. Set the review gate to `blocked` if critical blocking findings exist;
   otherwise set it to `complete`.
9. Run `featurectl.py validate --workspace <workspace> --review`.

Critical findings block verification.

Structured finding requirements:

- `linked_requirement_ids`
- `linked_slice_ids`
- `file_refs`
- `reproduction_or_reasoning`
- `fix_verification_command`
- `re_review_required`

Re-review loop:

- After fixes, update or add review evidence showing each blocking finding is
  resolved or explicitly deferred with user approval.
- Blocking findings must not be cleared only by editing severity; record the fix
  evidence and verification command.

If review passes, hand off to `nfp-10-verification`.
