# Native Implementation Showcase Runs

This report records the final state after running the Native Feature Pipeline against all ten cloned showcase repositories. Each clone now contains native repository code changes plus NFP artifacts under `.ai/feature-workspaces/...` and promoted artifacts under `.ai/features/...`.

The earlier materialized showcase-only outputs are still present in the harness history, but this report is for the native repo implementations on `nfp/*` branches.

## Final Inventory

| Repo | Branch | HEAD | Status | Native files | Diff check | Main validation result |
| --- | --- | --- | --- | ---: | --- | --- |
| `docmost` | `nfp/docmost-page-approval` | `8f61503` | clean | 10 | pass | server tests and builds passed |
| `formbricks` | `nfp/formbricks-signed-webhooks` | `94d85e9` | clean | 13 | pass | focused webhook tests, lint, Prisma validate, database build passed |
| `actual` | `nfp/actual-import-rule-preview-undo` | `4db4979` | clean | 5 | pass | focused core tests, typecheck, formatter check passed |
| `plane` | `nfp/plane-triage-automation` | `9851910` | clean | 16 | pass | compile checks and NFP gates passed; pytest unavailable |
| `nocodb` | `nfp/nocodb-schema-audit-log` | `c4af5df` | clean | 3 | pass | focused Jest and lint passed |
| `appsmith` | `nfp/appsmith-version-restore-diff` | `420914a` | clean | 7 | pass | focused Maven unit test passed; final rerun hit local disk exhaustion |
| `listmonk` | `nfp/listmonk-double-opt-in-segment` | `5898186` | clean | 19 | pass | focused tests and `go test ./...` passed |
| `medusa` | `nfp/medusa-first-order-promo-caps` | `217f3a55` | clean | 7 | pass | diff check passed; integration run blocked by sparse workspace artifacts |
| `excalidraw` | `nfp/excalidraw-layer-lock-history` | `2d7f2ad` | clean | 6 | pass | featurectl and diff check passed; vitest blocked by install/ENOSPC |
| `twenty` | `nfp/twenty-company-merge` | `6121576` | clean | 7 | pass | diff check and NFP gates passed; Jest blocked by missing workspaces |

Additional harness validation:

- `python -m unittest discover -s tests/feature_pipeline`: pass, 81 tests.
- Fresh `git diff --check HEAD` across all ten cloned repos: pass.
- Every cloned repo worktree is clean after final report commits.

## Per-Repository Results

### Docmost: Page Review Approval Workflow

Feature implemented: backend page review lifecycle for sensitive pages with `draft`, `review`, and `approved` states, reviewer comments, approval history, route integration, RBAC-oriented service checks, and persistence migration.

Artifacts:

- Workspace: `pipeline-lab/showcases/repos/docmost/.ai/feature-workspaces/pages/page-review-approval-workflow--run-20260511-y58m`
- Promoted feature: `pipeline-lab/showcases/repos/docmost/.ai/features/pages/page-review-approval-workflow`
- Final report: `pipeline-lab/showcases/repos/docmost/.codex-nfp-final.txt`

Native code changes:

- `apps/server/src/core/page/page-verification/dto/page-verification.dto.ts`
- `apps/server/src/core/page/page-verification/page-verification.service.ts`
- `apps/server/src/core/page/page-verification/page-verification.service.spec.ts`
- `apps/server/src/core/page/page-verification/page-verification.types.ts`
- `apps/server/src/core/page/page.controller.ts`
- `apps/server/src/core/page/page.module.ts`
- `apps/server/src/database/migrations/20260511T170000-page-verification-history.ts`
- `apps/server/src/database/types/db.d.ts`
- `apps/server/src/database/types/entity.types.ts`

Validation:

- Passed: `pnpm --filter ./apps/server test -- page-verification.service.spec.ts --runInBand`, 8 tests.
- Passed: `pnpm --filter @docmost/editor-ext build`.
- Passed: `pnpm --filter ./apps/server run build`.
- Known non-feature gap: copied constitution command references absent `tests/feature_pipeline`; adjacent pre-existing `page.service.spec.ts` alias issue remains documented in evidence.

### Formbricks: Signed Survey Response Webhooks

Feature implemented: signed webhook payload delivery with replay/idempotency fields, persisted delivery logs, bounded retry state, internal delivery processing route, management delivery-log route, database schema updates, and route/unit tests.

Artifacts:

- Workspace: `pipeline-lab/showcases/repos/formbricks/.ai/feature-workspaces/webhooks/signed-survey-response-webhooks--run-20260511-owned`
- Promoted feature: `pipeline-lab/showcases/repos/formbricks/.ai/features/webhooks/signed-survey-response-webhooks`
- Final report: `pipeline-lab/showcases/repos/formbricks/.codex-nfp-final.txt`

Native code changes:

- `apps/web/app/api/(internal)/pipeline/route.ts`
- `apps/web/app/api/(internal)/webhook-deliveries/route.ts`
- `apps/web/app/api/v2/management/webhooks/[webhookId]/deliveries/route.ts`
- `apps/web/modules/api/v2/management/webhooks/[webhookId]/deliveries/route.ts`
- `apps/web/modules/api/v2/management/webhooks/[webhookId]/deliveries/route.test.ts`
- `apps/web/modules/integrations/webhooks/lib/delivery.ts`
- `apps/web/modules/integrations/webhooks/lib/delivery.test.ts`
- `packages/database/migration/20260511163000_add_webhook_deliveries/migration.sql`
- `packages/database/migration/20260511170500_add_webhook_deliveries/migration.sql`
- `packages/database/schema.prisma`
- `packages/database/zod/webhooks.ts`

Validation:

- Passed: focused webhook delivery Vitest tests.
- Passed: focused ESLint on touched webhook files.
- Passed: `prisma validate` for the database schema.
- Passed: `pnpm --filter @formbricks/database build`.
- Known non-feature gap: broad web `tsc --noEmit` still fails on existing repo-wide type/package/asset declaration issues recorded in evidence.

### Actual Budget: Rule Preview And Undo

Feature implemented: import rule-effect preview metadata for transaction import and API support for rollback of rule-applied import effects.

Artifacts:

- Workspace: `pipeline-lab/showcases/repos/actual/.ai/feature-workspaces/actual/import-rule-preview-undo--run-20260511-kn58`
- Promoted feature: `pipeline-lab/showcases/repos/actual/.ai/features/actual/import-rule-preview-undo`
- Final report: `pipeline-lab/showcases/repos/actual/.codex-nfp-final.txt`

Native code changes:

- `packages/loot-core/src/server/accounts/app.ts`
- `packages/loot-core/src/server/accounts/sync.ts`
- `packages/loot-core/src/server/accounts/sync.test.ts`
- `packages/loot-core/src/types/api-handlers.ts`

Validation:

- Passed: `yarn workspace @actual-app/core test:node src/server/accounts/sync.test.ts`.
- Passed: `yarn workspace @actual-app/core typecheck`.
- Passed: `yarn exec oxfmt --check` on touched files.
- Known gap: desktop UI does not yet expose preview/rollback controls; implementation is core/API level.

### Plane: Triage Automation Rules

Feature implemented: backend triage automation model, serializers, API views, rule engine, audit logging, issue creation hook, migration, and tests for matching/conflict behavior.

Artifacts:

- Workspace: `pipeline-lab/showcases/repos/plane/.ai/feature-workspaces/plane/plane-triage-automation--run-20260511-root`
- Promoted feature: `pipeline-lab/showcases/repos/plane/.ai/features/plane/plane-triage-automation`
- Final report: `pipeline-lab/showcases/repos/plane/.codex-nfp-final.txt`

Native code changes:

- `apps/api/plane/app/serializers/triage.py`
- `apps/api/plane/app/urls/project.py`
- `apps/api/plane/app/views/issue/base.py`
- `apps/api/plane/app/views/triage/automation.py`
- `apps/api/plane/db/migrations/0122_triage_automation_rules.py`
- `apps/api/plane/db/models/triage.py`
- `apps/api/plane/tests/contract/app/test_triage_automation.py`
- `apps/api/plane/tests/unit/triage/test_automation.py`
- `apps/api/plane/triage/automation.py`
- `apps/api/plane/triage/rules.py`

Validation:

- Passed: Python compile checks on touched backend modules.
- Passed: NFP readiness, evidence, review, finish, and promote gates.
- Blocked: targeted pytest run could not execute because the local checkout lacks `pytest`/Django runtime dependencies.
- Known gap: backend API only; no web rule-authoring UI was added.

### NocoDB: Schema Change Audit Log

Feature implemented: schema/table/view hook audit capture using existing audit persistence with old/new values and rollback-hint metadata.

Artifacts:

- Workspace: `pipeline-lab/showcases/repos/nocodb/.ai/feature-workspaces/nocodb/schema-audit-log--run-20260511-wsee`
- Promoted feature: `pipeline-lab/showcases/repos/nocodb/.ai/features/nocodb/schema-audit-log`
- Final report: `pipeline-lab/showcases/repos/nocodb/.codex-nfp-final.txt`

Native code changes:

- `packages/nocodb/src/services/app-hooks-listener.service.ts`
- `packages/nocodb/src/services/app-hooks-listener.service.spec.ts`

Validation:

- Passed red/green/final focused Jest run with explicit `--testRegex`, 4 tests.
- Passed focused ESLint with the repo-default ignored-spec warning.
- Design note: no DB migration was needed because existing `nc_audit.details` and `Audit.insert` satisfy the persistence contract.

### Appsmith: App Version Restore Diff Preview

Feature implemented: backend snapshot diff DTO, service contract, safe restore preview support, controller surface, and focused unit tests for diff/restore behavior.

Artifacts:

- Workspace: `pipeline-lab/showcases/repos/appsmith/.ai/feature-workspaces/applications/app-version-restore-diff-preview--run-20260511-f8zd`
- Promoted feature: `pipeline-lab/showcases/repos/appsmith/.ai/features/applications/app-version-restore-diff-preview`
- Final report: `pipeline-lab/showcases/repos/appsmith/.codex-nfp-final.txt`

Native code changes:

- `app/server/appsmith-server/src/main/java/com/appsmith/server/controllers/ce/ApplicationControllerCE.java`
- `app/server/appsmith-server/src/main/java/com/appsmith/server/dtos/ApplicationSnapshotDiffDTO.java`
- `app/server/appsmith-server/src/main/java/com/appsmith/server/services/ce/ApplicationSnapshotServiceCE.java`
- `app/server/appsmith-server/src/main/java/com/appsmith/server/services/ce/ApplicationSnapshotServiceCEImpl.java`
- `app/server/appsmith-server/src/test/java/com/appsmith/server/services/ApplicationSnapshotServiceTest.java`
- `app/server/appsmith-server/src/test/java/com/appsmith/server/services/ce/ApplicationSnapshotServiceUnitTest.java`

Validation:

- Passed: `git diff --check`.
- Passed: `featurectl validate --workspace ... --evidence --review`.
- Passed: focused Maven unit test for `ApplicationSnapshotServiceUnitTest` with local Java 24 override.
- Blocked: final root rerun hit host disk exhaustion while compiling reactor dependencies.
- Known gap: backend contract/service only; frontend diff UI wiring remains follow-up work.

### listmonk: Double Opt-In Segment Onboarding

Feature implemented: import options for pending segment onboarding, confirmation token service, email template, subscriber confirmation route integration, migration/schema/query changes, and import/service tests.

Artifacts:

- Workspace: `pipeline-lab/showcases/repos/listmonk/.ai/feature-workspaces/subscribers/double-opt-in-segment--run-20260511`
- Promoted feature: `pipeline-lab/showcases/repos/listmonk/.ai/features/subscribers/double-opt-in-segment`
- Final report: `pipeline-lab/showcases/repos/listmonk/.codex-nfp-final.txt`

Native code changes:

- `cmd/handlers.go`
- `cmd/import.go`
- `cmd/init.go`
- `cmd/main.go`
- `cmd/public.go`
- `cmd/subscribers.go`
- `cmd/upgrade.go`
- `internal/migrations/v6.3.0.go`
- `internal/notifs/notifs.go`
- `internal/subimporter/importer.go`
- `internal/subimporter/importer_doubleoptin_test.go`
- `internal/subscribers/doubleoptin/service.go`
- `internal/subscribers/doubleoptin/service_test.go`
- `models/queries.go`
- `queries/subscribers.sql`
- `schema.sql`
- `static/email-templates/double-optin-segment.html`

Validation:

- Passed: `go test ./internal/subscribers/doubleoptin -count=1`.
- Passed: `go test ./internal/subimporter -count=1`.
- Passed: `go test ./cmd -run TestDoubleOptinSegmentConfirmRoute -count=1`.
- Passed: `go test ./...`.
- Known gap: frontend import UI controls were intentionally not added; API import options can drive the feature.

### Medusa: First-Order Promotion With Usage Caps

Feature implemented: cart promotion flow first-order context, customer completed-order detection inputs, fail-closed handling for missing customer IDs, and focused integration spec for first-order/global/per-customer cap behavior.

Artifacts:

- Workspace: `pipeline-lab/showcases/repos/medusa/.ai/feature-workspaces/promotions/first-order-promotion-with-usage-caps--run-20260511-jvfz`
- Promoted feature: `pipeline-lab/showcases/repos/medusa/.ai/features/promotions/first-order-promotion-with-usage-caps`
- Final report: `pipeline-lab/showcases/repos/medusa/.codex-nfp-final.txt`

Native code changes:

- `integration-tests/modules/__tests__/cart/store/first-order-promotion.spec.ts`
- `packages/core/core-flows/src/cart/steps/get-actions-to-compute-from-promotions.ts`
- `packages/core/core-flows/src/cart/steps/get-first-order-promotion-context.ts`
- `packages/core/core-flows/src/cart/steps/index.ts`
- `packages/core/core-flows/src/cart/utils/fields.ts`
- `packages/core/core-flows/src/cart/workflows/update-cart-promotions.ts`

Validation:

- Passed: `git diff --check`.
- Blocked: focused integration test and `@medusajs/core-flows` build could not complete because sparse checkout workspace artifacts such as `@medusajs/framework/types` and Yarn release/plugin files were unavailable.
- Risk: code is implemented and covered by a focused spec, but it needs a full Medusa workspace/dependency install for executable verification.

### Excalidraw: Layer Lock History-Safe Editing

Feature implemented: locked element edit guards in scene/mutation/app paths plus tests for locked-object edit prevention and reconciliation behavior.

Artifacts:

- Workspace: `pipeline-lab/showcases/repos/excalidraw/.ai/feature-workspaces/excalidraw/layer-lock-history--run-20260511-7q1m`
- Promoted feature: `pipeline-lab/showcases/repos/excalidraw/.ai/features/excalidraw/layer-lock-history`
- Final report: `pipeline-lab/showcases/repos/excalidraw/.codex-nfp-final.txt`

Native code changes:

- `packages/element/src/Scene.ts`
- `packages/element/src/mutateElement.ts`
- `packages/excalidraw/components/App.tsx`
- `packages/excalidraw/tests/data/reconcile.test.ts`
- `packages/excalidraw/tests/elementLocking.test.tsx`

Validation:

- Passed: `featurectl validate --review --evidence`.
- Passed: `featurectl validate`.
- Passed: `git diff --check`.
- Blocked: Vitest could not run because `yarn install --frozen-lockfile` failed with `ENOSPC`, leaving test dependencies unavailable.

### Twenty: Duplicate Company Merge With Audit Trail

Feature implemented: merge preview metadata, caller field-choice handling, audit context parsing, reversible rollback payload model, REST merge parsing, OpenAPI response/request updates, and service tests.

Artifacts:

- Workspace: `pipeline-lab/showcases/repos/twenty/.ai/feature-workspaces/company/duplicate-company-merge-with-audit-trail--20260511-local`
- Promoted feature: `pipeline-lab/showcases/repos/twenty/.ai/features/company/duplicate-company-merge-with-audit-trail`
- Final report: `pipeline-lab/showcases/repos/twenty/.codex-nfp-final.txt`

Native code changes:

- `packages/twenty-server/src/engine/api/common/common-query-runners/__tests__/common-merge-many-query-runner.service.spec.ts`
- `packages/twenty-server/src/engine/api/common/common-query-runners/common-merge-many-query-runner.service.ts`
- `packages/twenty-server/src/engine/api/common/types/common-query-args.type.ts`
- `packages/twenty-server/src/engine/api/rest/core/handlers/rest-api-merge-many.handler.ts`
- `packages/twenty-server/src/engine/core-modules/open-api/utils/request-body.utils.ts`
- `packages/twenty-server/src/engine/core-modules/open-api/utils/responses.utils.ts`

Validation:

- Passed: `git diff --check`.
- Passed: NFP readiness, worktree, evidence, review, and promote gates in the feature workspace.
- Blocked: focused Jest red/green commands could not execute because this checkout is missing declared Yarn workspaces and cannot build a valid `node_modules` state.

## Pipeline Integration Findings

- The pipeline did integrate into all ten existing repositories and produced both native code and artifacts.
- The strongest end-to-end executable showcases are `listmonk`, `docmost`, `formbricks`, `actual`, and `nocodb`; each has focused tests passing inside the clone.
- `plane`, `medusa`, `excalidraw`, and `twenty` show the common integration pain point for large cloned repos: sparse or dependency-incomplete local checkouts can block executable tests even when artifacts, code, and diff checks are valid.
- `appsmith` shows a second operational limit: full Java/Maven verification is sensitive to local disk capacity; a focused unit test passed before the final rerun ran out of space.
- Several implementations are backend/API focused rather than complete product UI integrations. Those are explicitly marked above so the showcase does not pretend to be production-complete where UI wiring remains.
