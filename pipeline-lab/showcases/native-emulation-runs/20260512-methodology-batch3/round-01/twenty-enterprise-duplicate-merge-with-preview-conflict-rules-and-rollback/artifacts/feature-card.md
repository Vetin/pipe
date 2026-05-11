# Feature Card: Enterprise duplicate merge with preview, conflict rules, and rollback

- Source: Twenty
- Rank: 1
- Final behavior: Twenty already has duplicate/merge-related discussions and issues, making this a realistic testbed. ([GitHub][4]) Expected output: feature contract for duplicate detection and merge behavior, architecture for entity relationships, ADR for merge conflict resolution, tech design for rollback/audit model, slices for preview/merge/audit/rollback, review catching irreversible data-loss risks.
- Safety: permissions, audit, rollback, verification, and promotion memory are mandatory.
- Best next live step: run a local Codex implementation session from `prompt.md` in the target checkout.

## Manual Validation
- Planned for user-visible workflow after live implementation.

## Verification Debt
- Offline emulation does not execute target repository tests; live run must close this debt.

## Claim Provenance
- Feature behavior: `feature.md`
- Architecture and design: `architecture.md`, `tech-design.md`
- Task graph: `slices.yaml`
- Review and verification: `reviews/review.md`, `reviews/verification-review.md`, `evidence/manifest.yaml`

## Rollback Guidance
- Preserve before/after state, audit event ids, and compensating action notes for every destructive transition.

## Plan Drift
- None in offline emulation; live implementation must mark stale artifacts if code changes the plan.

## Source Revision
- Offline source map only; live implementation must record git commit or diff hash.
