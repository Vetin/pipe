# Feature Card: GitHub sync conflict resolution and audit trail

- Source: Plane
- Rank: 3
- Final behavior: Plane already has GitHub issue sync concepts. ([Plane Docs][2]) Showcase feature: when a Plane issue and GitHub issue diverge, show conflict preview, choose source of truth, apply resolution, and log audit events. Expected pipeline output: feature contract with sync rules, ADR for conflict strategy, tech design for sync-state model, contract docs for GitHub webhook/API handling, TDD slices for conflict detection/resolution/audit.
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
