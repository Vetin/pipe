# Repository Context: Medusa

## Candidate Files And Modules
- `integration-tests/api/__tests__/admin/draft-order/draft-order.js.txt`
- `integration-tests/api/__tests__/admin/draft-order/ff-tax-inclusive-draft-order.js.txt`
- `integration-tests/api/__tests__/admin/order-edit/ff-tax-inclusive-pricing.js.txt`
- `integration-tests/api/__tests__/admin/order-edit/order-edit.js.txt`
- `integration-tests/api/__tests__/admin/order/__snapshots__/order.js.snap`
- `integration-tests/api/__tests__/admin/order/ff-tax-inclusive-pricing.js.txt`
- `integration-tests/api/__tests__/admin/order/order.js.txt`
- `integration-tests/api/__tests__/batch-jobs/order/export.js.txt`
- `integration-tests/api/__tests__/store/cart/__snapshots__/cart.js.snap`
- `integration-tests/api/__tests__/store/cart/cart.js.txt`
- `integration-tests/api/__tests__/store/cart/ff-sales-channels.js.txt`
- `integration-tests/api/__tests__/store/cart/ff-tax-inclusive-pricing.js.txt`
- `integration-tests/api/__tests__/store/cart/gift-cards/tax-calculation-ff-tax-inclusive.js.txt`
- `integration-tests/api/__tests__/store/cart/gift-cards/tax-calculation.js.txt`
- `integration-tests/api/__tests__/store/draft-order.js.txt`
- `integration-tests/api/__tests__/store/order-edit.js.txt`
- `integration-tests/api/__tests__/store/orders.js.txt`
- `integration-tests/api/__tests__/store/payment-collection.js.txt`

## Existing-Solution Reuse Map
- Inspect and prefer `integration-tests/api/__tests__/admin/draft-order/draft-order.js.txt` before adding a parallel implementation.
- Inspect and prefer `integration-tests/api/__tests__/admin/draft-order/ff-tax-inclusive-draft-order.js.txt` before adding a parallel implementation.
- Inspect and prefer `integration-tests/api/__tests__/admin/order-edit/ff-tax-inclusive-pricing.js.txt` before adding a parallel implementation.
- Inspect and prefer `integration-tests/api/__tests__/admin/order-edit/order-edit.js.txt` before adding a parallel implementation.

## Source-Backed Facts
- Candidate paths come from `git ls-files` in the local checkout when present.
- Generated context is a source map only; final claims require opening cited files.

## Hypotheses To Verify
- The requested feature should extend an existing domain service before adding a new subsystem.
- Audit/event persistence should reuse the nearest existing event or activity model when available.
- Tests should be placed beside the module that owns the domain invariant.

## Context Rule
Round 3 requires live Codex implementation to inspect these paths before final architecture, code, or tests are accepted.
