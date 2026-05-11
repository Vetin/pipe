# Feature Card: B2B quote-to-order approval workflow

- Source: Medusa
- Rank: 2
- Final behavior: Medusa’s B2B starter already includes company and merchant approval concepts. ([GitHub][6]) Showcase feature: buyer submits quote, company admin approves, merchant approves, pricing/promotions/tax/shipping are locked, quote converts to order. Expected result: architecture with multi-actor approval flow, ADRs for price locking and approval semantics, contracts for quote/order transitions, slices for permissions, approvals, expiry, conversion, and audit.
- Safety: permissions, audit, rollback, verification, and promotion memory are mandatory.
- Best next live step: run a local Codex implementation session from `prompt.md` in the target checkout.
