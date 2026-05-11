---
name: nfp-09-review
version: '0.1.0'
pipeline_contract_version: '0.1.0'
---

# NFP 09 Review

Use this skill to run deterministic and agentic review.

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
   python .agents/pipeline-core/scripts/featurectl.py validate --workspace <workspace> --review
   ```

3. Perform agentic review at one tier:
   - `basic_review`: spec compliance and code quality
   - `strict_review`: basic review plus security, contract, and test quality
   - `enterprise_review`: strict review plus performance, regression risk, and
     architecture compliance
4. Write structured findings as `reviews/*.yaml` using severity `critical`,
   `major`, `minor`, or `note`.
5. Mark critical findings as `blocking: true`.
6. Set the review gate to `blocked` if critical blocking findings exist;
   otherwise set it to `complete`.

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
