# Feature: GitHub sync conflict resolution and audit trail

## Intent
Implement GitHub sync conflict resolution and audit trail in Plane with production-grade contracts, tests, review, and promotion memory.

## Motivation
Plane already has GitHub issue sync concepts. ([Plane Docs][2]) Showcase feature: when a Plane issue and GitHub issue diverge, show conflict preview, choose source of truth, apply resolution, and log audit events. Expected pipeline output: feature contract with sync rules, ADR for conflict strategy, tech design for sync-state model, contract docs for GitHub webhook/API handling, TDD slices for conflict detection/resolution/audit.

## Actors
- Primary user for the feature workflow
- Administrator or reviewer who approves destructive or sensitive changes
- Background worker or integration process that records durable events

## Goals
- `FR-001` Detect divergence between Plane issue state and GitHub issue state from webhook/API sync metadata.
- `FR-002` Show a conflict preview that identifies changed fields, timestamps, actors, and proposed source of truth.
- `FR-003` Apply an explicit resolution policy and record an audit event for each resolved conflict.
- `FR-004` Handle webhook retries, stale payloads, and API failure without losing conflict history.

## Non-Goals
- Do not bypass existing permission boundaries.
- Do not silently mutate irreversible data.
- Do not promote artifacts without verification evidence.

## Related Existing Features
Round 3 requires source-backed reuse before new code is accepted.
The live implementation must inspect the repository context and either reuse the
closest existing module or record a no-existing-solution finding.

## Acceptance Criteria
- `AC-001` Given detect divergence between Plane issue state and GitHub issue state from webhook/API sync metadata., verification proves the behavior with a focused test and recorded evidence.
- `AC-002` Given show a conflict preview that identifies changed fields, timestamps, actors, and proposed source of truth., verification proves the behavior with a focused test and recorded evidence.
- `AC-003` Given apply an explicit resolution policy and record an audit event for each resolved conflict., verification proves the behavior with a focused test and recorded evidence.
- `AC-004` Given handle webhook retries, stale payloads, and API failure without losing conflict history., verification proves the behavior with a focused test and recorded evidence.

## Non-Functional Requirements
- `NFR-001` Mutating operations are auditable, observable, and rollback-aware.
- `NFR-002` External or asynchronous paths are idempotent and reject stale or replayed input.
- `NFR-003` Verification evidence must include exact commands, outputs, and artifact paths.

## Product Risks
- Replay or stale GitHub webhook overwrites newer Plane issue state.
- Ambiguous source-of-truth policy creates sync loops.
- Audit trail misses external actor and payload identity.

## Ambiguity Score
- Score: `0.18`
- Status: safe to proceed with recorded assumptions
- Blocking dimensions: functional scope, permissions, rollback, stale/replay behavior, and completion signals.

## Clarification Ledger
- Answered: core actor, target workflow, and audit requirement are known from the feature request.
- Assumed: exact repository module names are resolved during context inspection.
- Deferred: visual/UI copy and migration mechanics are decided after source inspection.
- Blocking: none remain in round 3 once repository context is inspected.

## Source-Backed Reuse Map
- Inspect and prefer `.github/ISSUE_TEMPLATE/--bug-report.yaml` before adding a parallel implementation.
- Inspect and prefer `.github/ISSUE_TEMPLATE/--feature-request.yaml` before adding a parallel implementation.
- Inspect and prefer `.github/ISSUE_TEMPLATE/config.yaml` before adding a parallel implementation.
- Inspect and prefer `.github/instructions/bash.instructions.md` before adding a parallel implementation.

## Open Questions
- Confirm exact repository module names during live implementation.
- Confirm whether existing audit/event tables can be reused or require migration.
