# Review And Verification

## What To Borrow

- Split deterministic validation from agentic review.
- Use review tiers so small features do not pay enterprise review cost by
  default.
- Require reproduction, linked artifacts, and fix verification for findings.
- Re-review blocking issues after fixes.
- Review before and after implementation for high-risk features. The pre-code
  pass catches unsafe contracts/designs; the post-code pass checks behavior,
  tests, migrations, and rollback.
- Pass a focused review packet: requirements, changed files, risks, evidence,
  and known gaps. Do not rely on chat history.
- Validate replay, abuse, and irreversible-data scenarios explicitly for
  webhooks, audit logs, merge flows, approvals, payments, and promotions.

## What To Reject

- Clearing a critical finding by editing severity only.
- Running final verification while known critical issues remain.
- Treating environment failures as product success.
- Marking blocked verification as success. Environment failures must include
  the command, failure reason, and residual risk.
- Review findings that cannot be traced to a requirement, slice, file, or
  reproduction path.

## Native Artifact Influence

`reviews/*.yaml`, `reviews/*-review.md`, `reviews/verification-review.md`,
`evidence/`, and `verification-attempts.md` or equivalent `execution.md`
entries.
Native emulation reports compare review coverage side by side so weak prompt
iterations are visible.

Review artifact boundary:

- `reviews/*.yaml` are YAML findings and are the machine-readable source for
  severity, blocking state, linked requirements, linked slices, file
  references, reproduction or reasoning, fix verification, and re-review state.
- `reviews/*-review.md` are Markdown summaries for human/LLM narrative,
  reviewer assumptions, zero-finding explanations, and residual-risk context.
- Markdown summaries do not satisfy the review gate without YAML findings or a
  note-level YAML record.

## Native Skill Influence

`nfp-09-review`, `nfp-10-verification`, and `nfp-11-finish`.
`nfp-08-tdd-implementation` must keep implementation evidence small and
slice-bound so review can replay it. `nfp-12-promote` must refuse promotion if
blocking review state remains unresolved.

## Validation Rule Implied

Critical review findings must be blocking. Structured review files must link
requirements, slices, file references, reasoning, and a fix verification command.
Native emulation must prove later prompt iterations improve review strictness
and verification specificity.
