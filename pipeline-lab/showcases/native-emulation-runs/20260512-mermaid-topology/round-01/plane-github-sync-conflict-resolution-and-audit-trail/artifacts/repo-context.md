# Repository Context: Plane

## Candidate Files And Modules
- `.github/ISSUE_TEMPLATE/--bug-report.yaml`
- `.github/ISSUE_TEMPLATE/--feature-request.yaml`
- `.github/ISSUE_TEMPLATE/config.yaml`
- `.github/instructions/bash.instructions.md`
- `.github/instructions/typescript.instructions.md`
- `.github/pull_request_template.md`
- `.github/workflows/build-branch.yml`
- `.github/workflows/check-version.yml`
- `.github/workflows/codeql.yml`
- `.github/workflows/copyright-check.yml`
- `.github/workflows/feature-deployment.yml`
- `.github/workflows/pull-request-build-lint-api.yml`
- `.github/workflows/pull-request-build-lint-web-apps.yml`
- `apps/admin/app/(all)/(dashboard)/authentication/github/form.tsx`
- `apps/admin/app/(all)/(dashboard)/authentication/github/page.tsx`
- `apps/admin/components/authentication/github-config.tsx`
- `apps/api/plane/api/serializers/issue.py`
- `apps/api/plane/api/views/issue.py`

## Existing-Solution Reuse Map
- Inspect and prefer `.github/ISSUE_TEMPLATE/--bug-report.yaml` before adding a parallel implementation.
- Inspect and prefer `.github/ISSUE_TEMPLATE/--feature-request.yaml` before adding a parallel implementation.
- Inspect and prefer `.github/ISSUE_TEMPLATE/config.yaml` before adding a parallel implementation.
- Inspect and prefer `.github/instructions/bash.instructions.md` before adding a parallel implementation.

## Source-Backed Facts
- Candidate paths come from `git ls-files` in the local checkout when present.
- Generated context is a source map only; final claims require opening cited files.

## Hypotheses To Verify
- The requested feature should extend an existing domain service before adding a new subsystem.
- Audit/event persistence should reuse the nearest existing event or activity model when available.
- Tests should be placed beside the module that owns the domain invariant.

## Context Rule
Round 1 requires live Codex implementation to inspect these paths before final architecture, code, or tests are accepted.
