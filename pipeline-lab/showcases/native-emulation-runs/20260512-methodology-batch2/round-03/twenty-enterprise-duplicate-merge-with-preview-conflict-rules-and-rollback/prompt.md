I need you to implement this feature in the local Twenty checkout.

Repository: /pipeline-lab/showcases/repos/twenty
Feature: Enterprise duplicate merge with preview, conflict rules, and rollback
Expected result: Twenty already has duplicate/merge-related discussions and issues, making this a realistic testbed. ([GitHub][4]) Expected output: feature contract for duplicate detection and merge behavior, architecture for entity relationships, ADR for merge conflict resolution, tech design for rollback/audit model, slices for preview/merge/audit/rollback, review catching irreversible data-loss risks.

This is a normal user feature request. Work like this is going to production: discover the repository's native feature pipeline from local docs and tooling, work in place, preserve unrelated changes, create durable artifacts, implement with tests, review the result, verify it, and leave a concise final report.
Be explicit about contracts, permissions, audit events, rollback strategy, failure modes, and user-visible edge cases.
Before changing code, inspect the local modules and tests, create durable artifacts, implement through test-first slices, run adversarial review, record exact verification commands, and promote only verified feature memory.

Do not ask me to invoke individual internal skills by name; infer the workflow from the repository context and continue until the feature is handled end to end.

Round focus: Requires repo inspection, non-delegable gates, red/green evidence, review replay, and promotion memory.

Repository hints to inspect first:

- .github/workflows/cd-deploy-main.yaml
- .github/workflows/cd-deploy-tag.yaml
- .github/workflows/changed-files.yaml
- .github/workflows/ci-ai-catalog-sync.yaml
- .github/workflows/ci-breaking-changes.yaml
- .github/workflows/ci-create-app-e2e-hello-world.yaml
- .github/workflows/ci-create-app-e2e-minimal.yaml
- .github/workflows/ci-create-app-e2e-postcard.yaml
