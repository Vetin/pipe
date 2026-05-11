# Showcase Iteration Log

Date: 2026-05-11

The showcase lab was run with 10 scenario iterations. The initial side-by-side
comparison found the weakest production skill was `nfp-08-tdd-implementation`
with a score of `0.750`, caused by a missing durable iteration ledger requirement
for messy implementation loops.

The improvement pass updated:

- `nfp-05-slicing`: added loop-ready slice metadata.
- `nfp-08-tdd-implementation`: added an `I-001` through `I-010` iteration ledger,
  failure triage classes, allowed decisions, and resume checkpoints.
- `nfp-09-review`: added linked findings and re-review requirements.
- `nfp-10-verification`: added loop-aware verification attempts.
- `nfp-11-finish`: added iteration count, failed attempts, residual risks, final
  proof commands, and plan drift summary requirements.

## Iterations

| Iteration | Scenario | Main Stress | Result |
| ---: | --- | --- | --- |
| 1 | `01-auth-reset-password` | token security and account enumeration | validated after `nfp-08` loop protocol |
| 2 | `02-webhook-integration` | signature replay and idempotency | validated after `nfp-08` loop protocol |
| 3 | `03-frontend-account-settings` | frontend/API slice boundaries | validated after `nfp-08` loop protocol |
| 4 | `04-billing-plan-upgrade` | paid-service approval and rollback | validated after `nfp-08` loop protocol |
| 5 | `05-rbac-admin` | authorization and review quality | validated after `nfp-08` loop protocol |
| 6 | `06-audit-log-export` | privacy and large export handling | validated after `nfp-08` loop protocol |
| 7 | `07-search-ranking` | measurable regression criteria | validated after `nfp-08` loop protocol |
| 8 | `08-tenant-isolation` | cross-tenant safety and cache risk | validated after `nfp-08` loop protocol |
| 9 | `09-notification-preferences` | unsubscribe semantics and schema drift | validated after `nfp-08` loop protocol |
| 10 | `10-job-retry-dashboard` | operational actions and observability | validated after `nfp-08` loop protocol |

Final showcase result:

```text
iterations: 10
scenario_count: 10
all step scores: 1.000
all side-by-side focus scores: 1.000
```
