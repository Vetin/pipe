# Showcase Lab

This lab validates the Native Feature Pipeline against 10 diverse, open-source
inspired codebase scenarios. The scenarios are not vendored projects; they are
feature-delivery test cases that stress the pipeline shape across security,
frontend, billing, access control, compliance, search, tenancy, notifications,
and operations work.

## Scenarios

| ID | Codebase Style | Feature |
| --- | --- | --- |
| `01-auth-reset-password` | Django-style monolith | Secure email password reset |
| `02-webhook-integration` | Express-style API | Signed payment webhook intake |
| `03-frontend-account-settings` | React-admin style SPA | Account settings UI |
| `04-billing-plan-upgrade` | Saleor-style commerce | Paid plan upgrade |
| `05-rbac-admin` | FastAPI-style API | Role-based access control |
| `06-audit-log-export` | Superset-style analytics | Audit log export |
| `07-search-ranking` | Meilisearch-style service | Ranking relevance tuning |
| `08-tenant-isolation` | Discourse-style app | Tenant data isolation |
| `09-notification-preferences` | Mastodon-style platform | Notification preferences |
| `10-job-retry-dashboard` | Sidekiq-style system | Job retry dashboard |

## Validation

Run:

```bash
python .agents/pipeline-core/scripts/pipelinebench.py run-showcases \
  --output-dir pipeline-lab/showcases/results \
  --iterations 10
```

The command writes:

- `pipeline-lab/showcases/results/showcase-summary.yaml`
- `pipeline-lab/showcases/results/showcase-report.md`

`tests/feature_pipeline/test_showcases.py` also validates that `featurectl.py new`
can initialize a worktree and feature workspace for all 10 scenarios.

## Codex E2E Reproduction Cases

`codex-e2e-cases.yaml` contains stable real-repo cases with an original codebase
path, base ref, target branch, feature request, and expected result. The E2E
runner turns one case into a local `codex exec` session and records the prompt,
command, output, final response, manifest, and report:

```bash
python pipeline-lab/showcases/scripts/run_codex_e2e_case.py \
  --case formbricks-signed-webhooks \
  --run-id local-formbricks-001
```

The runner works in the current repository checkout and tells Codex not to
create a git worktree. It requires a clean target repo by default; use
`--dry-run` to review the generated prompt and command without invoking Codex.

## Improvement Loop

Initial showcase scoring exposed `nfp-08-tdd-implementation` as the weakest step
because it did not define a durable 10-iteration implementation ledger. The
skill suite was improved with:

- loop-ready slicing fields
- implementation iteration ledger protocol
- review re-review requirements
- loop-aware verification attempts
- finish-stage plan drift and iteration history requirements

After the improvement pass, all step scores are `1.000` in the showcase rubric.
