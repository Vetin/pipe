# Feature: Enterprise duplicate merge with preview, conflict rules, and rollback

## Intent
Implement Enterprise duplicate merge with preview, conflict rules, and rollback in Twenty with production-grade contracts, tests, review, and promotion memory.

## Motivation
Twenty already has duplicate/merge-related discussions and issues, making this a realistic testbed. ([GitHub][4]) Expected output: feature contract for duplicate detection and merge behavior, architecture for entity relationships, ADR for merge conflict resolution, tech design for rollback/audit model, slices for preview/merge/audit/rollback, review catching irreversible data-loss risks.

## Actors
- Primary user for the feature workflow
- Administrator or reviewer who approves destructive or sensitive changes
- Background worker or integration process that records durable events

## Goals
- `FR-001` Detect likely duplicate companies from normalized name, domain, and configurable confidence rules.
- `FR-002` Show a merge preview with field-level conflicts, linked records, ownership changes, and irreversible-risk warnings.
- `FR-003` Apply a guarded merge that preserves a reversible audit record and blocks automation below the confidence threshold.
- `FR-004` Support rollback planning for copied fields, reparented relations, and audit replay.

## Non-Goals
- Do not bypass existing permission boundaries.
- Do not silently mutate irreversible data.
- Do not promote artifacts without verification evidence.

## Related Existing Features
Round 1 requires source-backed reuse before new code is accepted.
The live implementation must inspect the repository context and either reuse the
closest existing module or record a no-existing-solution finding.

## Acceptance Criteria
- `AC-001` Given detect likely duplicate companies from normalized name, domain, and configurable confidence rules., verification proves the behavior with a focused test and recorded evidence.
- `AC-002` Given show a merge preview with field-level conflicts, linked records, ownership changes, and irreversible-risk warnings., verification proves the behavior with a focused test and recorded evidence.
- `AC-003` Given apply a guarded merge that preserves a reversible audit record and blocks automation below the confidence threshold., verification proves the behavior with a focused test and recorded evidence.
- `AC-004` Given support rollback planning for copied fields, reparented relations, and audit replay., verification proves the behavior with a focused test and recorded evidence.

## Non-Functional Requirements
- `NFR-001` Mutating operations are auditable, observable, and rollback-aware.
- `NFR-002` External or asynchronous paths are idempotent and reject stale or replayed input.
- `NFR-003` Verification evidence must include exact commands, outputs, and artifact paths.

## Product Risks
- Irreversible data loss from overwriting company fields without a field provenance record.
- Unsafe automation merging low-confidence duplicates.
- Broken relations if child records are reparented outside a transaction.

## Ambiguity Score
- Score: `0.46`
- Status: requires risk closure before implementation
- Blocking dimensions: functional scope, permissions, rollback, stale/replay behavior, and completion signals.

## Clarification Ledger
- Answered: core actor, target workflow, and audit requirement are known from the feature request.
- Assumed: exact repository module names are resolved during context inspection.
- Deferred: visual/UI copy and migration mechanics are decided after source inspection.
- Blocking: none remain in round 1 once repository context is inspected.

## Source-Backed Reuse Map
- Inspect and prefer `.github/workflows/cd-deploy-main.yaml` before adding a parallel implementation.
- Inspect and prefer `.github/workflows/cd-deploy-tag.yaml` before adding a parallel implementation.
- Inspect and prefer `.github/workflows/changed-files.yaml` before adding a parallel implementation.
- Inspect and prefer `.github/workflows/ci-ai-catalog-sync.yaml` before adding a parallel implementation.

## Open Questions
- Confirm exact repository module names during live implementation.
- Confirm whether existing audit/event tables can be reused or require migration.
