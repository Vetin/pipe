I need you to implement this feature in the local Plane checkout.

Repository: /Users/egormasnankin/work/harness-pipeline/pipeline-lab/showcases/repos/plane
Feature: GitHub sync conflict resolution and audit trail
Expected result: Plane already has GitHub issue sync concepts. ([Plane Docs][2]) Showcase feature: when a Plane issue and GitHub issue diverge, show conflict preview, choose source of truth, apply resolution, and log audit events. Expected pipeline output: feature contract with sync rules, ADR for conflict strategy, tech design for sync-state model, contract docs for GitHub webhook/API handling, TDD slices for conflict detection/resolution/audit.

This is a normal user feature request. Work like this is going to production: discover the repository's native feature pipeline from local docs and tooling, work in place, preserve unrelated changes, create durable artifacts, implement with tests, review the result, verify it, and leave a concise final report.

Do not ask me to invoke individual internal skills by name; infer the workflow from the repository context and continue until the feature is handled end to end.

Round focus: Plain user request with end-to-end delivery expectations.

Repository hints to inspect first:
- .github/ISSUE_TEMPLATE/--bug-report.yaml
- .github/ISSUE_TEMPLATE/--feature-request.yaml
- .github/ISSUE_TEMPLATE/config.yaml
- .github/instructions/bash.instructions.md
- .github/instructions/typescript.instructions.md
- .github/pull_request_template.md
- .github/workflows/build-branch.yml
- .github/workflows/check-version.yml
