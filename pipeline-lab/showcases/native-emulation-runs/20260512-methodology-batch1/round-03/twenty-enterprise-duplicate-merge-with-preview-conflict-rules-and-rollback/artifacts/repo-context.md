# Repository Context: Twenty

## Candidate Files And Modules
- `.github/workflows/cd-deploy-main.yaml`
- `.github/workflows/cd-deploy-tag.yaml`
- `.github/workflows/changed-files.yaml`
- `.github/workflows/ci-ai-catalog-sync.yaml`
- `.github/workflows/ci-breaking-changes.yaml`
- `.github/workflows/ci-create-app-e2e-hello-world.yaml`
- `.github/workflows/ci-create-app-e2e-minimal.yaml`
- `.github/workflows/ci-create-app-e2e-postcard.yaml`
- `.github/workflows/ci-create-app.yaml`
- `.github/workflows/ci-docs.yaml`
- `.github/workflows/ci-emails.yaml`
- `.github/workflows/ci-example-app-hello-world.yaml`
- `.github/workflows/ci-example-app-postcard.yaml`
- `.github/workflows/ci-front-component-renderer.yaml`
- `.github/workflows/ci-front.yaml`
- `.github/workflows/ci-merge-queue.yaml`
- `.github/workflows/ci-release-create.yaml`
- `.github/workflows/ci-release-merge.yaml`

## Existing-Solution Reuse Map
- Inspect and prefer `.github/workflows/cd-deploy-main.yaml` before adding a parallel implementation.
- Inspect and prefer `.github/workflows/cd-deploy-tag.yaml` before adding a parallel implementation.
- Inspect and prefer `.github/workflows/changed-files.yaml` before adding a parallel implementation.
- Inspect and prefer `.github/workflows/ci-ai-catalog-sync.yaml` before adding a parallel implementation.

## Source-Backed Facts
- Candidate paths come from `git ls-files` in the local checkout when present.
- Generated context is a source map only; final claims require opening cited files.

## Hypotheses To Verify
- The requested feature should extend an existing domain service before adding a new subsystem.
- Audit/event persistence should reuse the nearest existing event or activity model when available.
- Tests should be placed beside the module that owns the domain invariant.

## Context Rule
Round 3 requires live Codex implementation to inspect these paths before final architecture, code, or tests are accepted.
