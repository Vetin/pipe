# Feature: B2B quote-to-order approval workflow

## Intent
Implement B2B quote-to-order approval workflow in Medusa with production-grade contracts, tests, review, and promotion memory.

## Motivation
Medusa’s B2B starter already includes company and merchant approval concepts. ([GitHub][6]) Showcase feature: buyer submits quote, company admin approves, merchant approves, pricing/promotions/tax/shipping are locked, quote converts to order. Expected result: architecture with multi-actor approval flow, ADRs for price locking and approval semantics, contracts for quote/order transitions, slices for permissions, approvals, expiry, conversion, and audit.

## Actors
- Primary user for the feature workflow
- Administrator or reviewer who approves destructive or sensitive changes
- Background worker or integration process that records durable events

## Goals
- `FR-001` Allow a buyer to submit a quote request with lines, company, expiry, and requested terms.
- `FR-002` Require company-admin and merchant approval before quote conversion.
- `FR-003` Lock pricing, promotions, tax, and shipping decisions at approval time.
- `FR-004` Convert an approved quote to an order with auditable state transitions and expiry handling.

## Non-Goals
- Do not bypass existing permission boundaries.
- Do not silently mutate irreversible data.
- Do not promote artifacts without verification evidence.

## Related Existing Features
Round 3 requires source-backed reuse before new code is accepted.
The live implementation must inspect the repository context and either reuse the
closest existing module or record a no-existing-solution finding.

## Acceptance Criteria
- `AC-001` Given allow a buyer to submit a quote request with lines, company, expiry, and requested terms., verification proves the behavior with a focused test and recorded evidence.
- `AC-002` Given require company-admin and merchant approval before quote conversion., verification proves the behavior with a focused test and recorded evidence.
- `AC-003` Given lock pricing, promotions, tax, and shipping decisions at approval time., verification proves the behavior with a focused test and recorded evidence.
- `AC-004` Given convert an approved quote to an order with auditable state transitions and expiry handling., verification proves the behavior with a focused test and recorded evidence.

## Non-Functional Requirements
- `NFR-001` Mutating operations are auditable, observable, and rollback-aware.
- `NFR-002` External or asynchronous paths are idempotent and reject stale or replayed input.
- `NFR-003` Verification evidence must include exact commands, outputs, and artifact paths.

## Product Risks
- Price drift between quote approval and order conversion.
- Incorrect actor authorization across buyer, company admin, and merchant roles.
- Expired quote converted after inventory, tax, or shipping assumptions changed.

## Ambiguity Score
- Score: `0.18`
- Status: safe to proceed with recorded assumptions
- Blocking dimensions: functional scope, permissions, rollback, stale/replay behavior, and completion signals.

## Clarification Ledger
- Answered: core actor, target workflow, and audit requirement are known from the feature request.
- Assumed: exact repository module names are resolved during context inspection.
- Deferred: visual/UI copy and migration mechanics are decided after source inspection.
- Blocking: none remain in round 3 once repository context is inspected.

## Source-Backed Reuse Map
- Inspect and prefer `integration-tests/api/__tests__/admin/draft-order/draft-order.js.txt` before adding a parallel implementation.
- Inspect and prefer `integration-tests/api/__tests__/admin/draft-order/ff-tax-inclusive-draft-order.js.txt` before adding a parallel implementation.
- Inspect and prefer `integration-tests/api/__tests__/admin/order-edit/ff-tax-inclusive-pricing.js.txt` before adding a parallel implementation.
- Inspect and prefer `integration-tests/api/__tests__/admin/order-edit/order-edit.js.txt` before adding a parallel implementation.

## Open Questions
- Confirm exact repository module names during live implementation.
- Confirm whether existing audit/event tables can be reused or require migration.
