# Feature Card: GitHub sync conflict resolution and audit trail

- Source: Plane
- Rank: 3
- Final behavior: Plane already has GitHub issue sync concepts. ([Plane Docs][2]) Showcase feature: when a Plane issue and GitHub issue diverge, show conflict preview, choose source of truth, apply resolution, and log audit events. Expected pipeline output: feature contract with sync rules, ADR for conflict strategy, tech design for sync-state model, contract docs for GitHub webhook/API handling, TDD slices for conflict detection/resolution/audit.
- Safety: permissions, audit, rollback, verification, and promotion memory are mandatory.
- Best next live step: run a local Codex implementation session from `prompt.md` in the target checkout.
