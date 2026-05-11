# Showcase Comparison

Iterations: 10
Scenarios: 10

## Step Solidity

| Step | Skill | Score | Checks |
| --- | --- | ---: | ---: |
| nfp-00-intake | `.agents/skills/nfp-00-intake/SKILL.md` | 1.000 | 3/3 |
| nfp-01-context | `.agents/skills/nfp-01-context/SKILL.md` | 1.000 | 3/3 |
| nfp-02-feature-contract | `.agents/skills/nfp-02-feature-contract/SKILL.md` | 1.000 | 3/3 |
| nfp-03-architecture | `.agents/skills/nfp-03-architecture/SKILL.md` | 1.000 | 3/3 |
| nfp-04-tech-design | `.agents/skills/nfp-04-tech-design/SKILL.md` | 1.000 | 3/3 |
| nfp-05-slicing | `.agents/skills/nfp-05-slicing/SKILL.md` | 1.000 | 4/4 |
| nfp-06-readiness | `.agents/skills/nfp-06-readiness/SKILL.md` | 1.000 | 3/3 |
| nfp-07-worktree | `.agents/skills/nfp-07-worktree/SKILL.md` | 1.000 | 3/3 |
| nfp-08-tdd-implementation | `.agents/skills/nfp-08-tdd-implementation/SKILL.md` | 1.000 | 4/4 |
| nfp-09-review | `.agents/skills/nfp-09-review/SKILL.md` | 1.000 | 4/4 |
| nfp-10-verification | `.agents/skills/nfp-10-verification/SKILL.md` | 1.000 | 4/4 |
| nfp-11-finish | `.agents/skills/nfp-11-finish/SKILL.md` | 1.000 | 4/4 |
| nfp-12-promote | `.agents/skills/nfp-12-promote/SKILL.md` | 1.000 | 3/3 |

## Side By Side

| Scenario | Codebase | Feature Goal | Avg Focus Score |
| --- | --- | --- | ---: |
| 01-auth-reset-password | django/django-style monolith | Add secure email password reset with token expiry and audit logging. | 1.000 |
| 02-webhook-integration | expressjs/express-style API | Add signed inbound payment webhooks with idempotency and retry-safe processing. | 1.000 |
| 03-frontend-account-settings | react-admin style SPA | Add profile settings with validation, optimistic save, accessibility, and API integration. | 1.000 |
| 04-billing-plan-upgrade | saleor/saleor-style commerce platform | Add paid plan upgrade with entitlements, invoices, and rollback on payment failure. | 1.000 |
| 05-rbac-admin | fastapi/full-stack-fastapi-template style API | Add roles, permissions, policy checks, and admin assignment APIs. | 1.000 |
| 06-audit-log-export | superset/superset-style analytics app | Add filtered asynchronous audit log export with retention and privacy constraints. | 1.000 |
| 07-search-ranking | meilisearch/meilisearch-style search service | Add configurable ranking weights with regression fixtures and measurable relevance criteria. | 1.000 |
| 08-tenant-isolation | discourse/discourse-style multi-tenant app | Enforce tenant scoping across queries, jobs, cache keys, and logs. | 1.000 |
| 09-notification-preferences | mastodon/mastodon-style social platform | Add channel preferences, quiet hours, defaults, and unsubscribe semantics. | 1.000 |
| 10-job-retry-dashboard | sidekiq/sidekiq-style job system | Add queue visibility with retry and cancel actions, permission checks, and observability. | 1.000 |

## Iterations

| Iteration | Scenario | Weakest Step | Score | Status |
| ---: | --- | --- | ---: | --- |
| 1 | 01-auth-reset-password | nfp-00-intake | 1.000 | validated_after_skill_improvement |
| 2 | 02-webhook-integration | nfp-00-intake | 1.000 | validated_after_skill_improvement |
| 3 | 03-frontend-account-settings | nfp-00-intake | 1.000 | validated_after_skill_improvement |
| 4 | 04-billing-plan-upgrade | nfp-00-intake | 1.000 | validated_after_skill_improvement |
| 5 | 05-rbac-admin | nfp-00-intake | 1.000 | validated_after_skill_improvement |
| 6 | 06-audit-log-export | nfp-00-intake | 1.000 | validated_after_skill_improvement |
| 7 | 07-search-ranking | nfp-00-intake | 1.000 | validated_after_skill_improvement |
| 8 | 08-tenant-isolation | nfp-00-intake | 1.000 | validated_after_skill_improvement |
| 9 | 09-notification-preferences | nfp-00-intake | 1.000 | validated_after_skill_improvement |
| 10 | 10-job-retry-dashboard | nfp-00-intake | 1.000 | validated_after_skill_improvement |
