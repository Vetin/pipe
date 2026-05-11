# Feature Card: B2B quote-to-order approval workflow

- Source: Medusa
- Rank: 2
- Final behavior: Medusa’s B2B starter already includes company and merchant approval concepts. ([GitHub][6]) Showcase feature: buyer submits quote, company admin approves, merchant approves, pricing/promotions/tax/shipping are locked, quote converts to order. Expected result: architecture with multi-actor approval flow, ADRs for price locking and approval semantics, contracts for quote/order transitions, slices for permissions, approvals, expiry, conversion, and audit.
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

## Shared Knowledge Updates
- `.ai/knowledge/features-overview.md`: add or refresh the feature card entry after promotion.
- `.ai/knowledge/architecture-overview.md`: add high-level topology and affected boundaries after live implementation.
- `.ai/knowledge/module-map.md`: add final source/test ownership once exact files are selected.
- `.ai/knowledge/integration-map.md`: add integration, event, job, webhook, or audit communication paths.

## Plan Drift
- None in offline emulation; live implementation must mark stale artifacts if code changes the plan.

## Source Revision
- Offline source map only; live implementation must record git commit or diff hash.
