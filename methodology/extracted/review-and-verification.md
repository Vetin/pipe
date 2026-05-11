# Review And Verification

## What To Borrow

- Split deterministic validation from agentic review.
- Use review tiers so small features do not pay enterprise review cost by
  default.
- Require reproduction, linked artifacts, and fix verification for findings.
- Re-review blocking issues after fixes.

## What To Reject

- Clearing a critical finding by editing severity only.
- Running final verification while known critical issues remain.
- Treating environment failures as product success.

## Native Artifact Influence

`reviews/*.yaml`, `reviews/verification-review.md`, `evidence/`, and
`verification-attempts.md` or equivalent `execution.md` entries.

## Native Skill Influence

`nfp-09-review`, `nfp-10-verification`, and `nfp-11-finish`.

## Validation Rule Implied

Critical review findings must be blocking. Structured review files must link
requirements, slices, file references, reasoning, and a fix verification command.
