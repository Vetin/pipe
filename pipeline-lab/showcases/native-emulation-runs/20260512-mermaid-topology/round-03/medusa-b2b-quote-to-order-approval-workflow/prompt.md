I need you to implement this feature in the local Medusa checkout.

Repository: /pipeline-lab/showcases/repos/medusa
Feature: B2B quote-to-order approval workflow
Expected result: Medusa’s B2B starter already includes company and merchant approval concepts. ([GitHub][6]) Showcase feature: buyer submits quote, company admin approves, merchant approves, pricing/promotions/tax/shipping are locked, quote converts to order. Expected result: architecture with multi-actor approval flow, ADRs for price locking and approval semantics, contracts for quote/order transitions, slices for permissions, approvals, expiry, conversion, and audit.

This is a normal user feature request. Work like this is going to production: discover the repository's native feature pipeline from local docs and tooling, work in place, preserve unrelated changes, create durable artifacts, implement with tests, review the result, verify it, and leave a concise final report.
Be explicit about contracts, permissions, audit events, rollback strategy, failure modes, and user-visible edge cases.
Before changing code, inspect the local modules and tests, create durable artifacts, implement through test-first slices, run adversarial review, record exact verification commands, and promote only verified feature memory.

Do not ask me to invoke individual internal skills by name; infer the workflow from the repository context and continue until the feature is handled end to end.

Round focus: Requires repo inspection, non-delegable gates, red/green evidence, review replay, and promotion memory.

Repository hints to inspect first:

- integration-tests/api/**tests**/admin/draft-order/draft-order.js.txt
- integration-tests/api/**tests**/admin/draft-order/ff-tax-inclusive-draft-order.js.txt
- integration-tests/api/**tests**/admin/order-edit/ff-tax-inclusive-pricing.js.txt
- integration-tests/api/**tests**/admin/order-edit/order-edit.js.txt
- integration-tests/api/**tests**/admin/order/**snapshots**/order.js.snap
- integration-tests/api/**tests**/admin/order/ff-tax-inclusive-pricing.js.txt
- integration-tests/api/**tests**/admin/order/order.js.txt
- integration-tests/api/**tests**/batch-jobs/order/export.js.txt
