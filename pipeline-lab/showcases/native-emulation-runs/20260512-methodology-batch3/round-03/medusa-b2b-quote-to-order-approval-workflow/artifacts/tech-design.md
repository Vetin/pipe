# Technical Design: B2B quote-to-order approval workflow

## Change Delta
- Add preview/apply/audit behavior behind a feature flag.
- Extend the closest domain service instead of creating a parallel subsystem.
- Add tests for state transitions, permissions, rollback, and stale/replay behavior.

## Interfaces
- Preview command returns affected entities, conflicts, warnings, and audit preview id.
- Apply command requires preview token/version, actor id, and explicit confirmation.
- Audit query returns immutable event history linked to source entity and request id.

## Dependency And Ownership Plan
- Critical path: domain invariant, persistence/audit contract, apply command, then UI/API integration.
- Parallel streams: documentation and read-only preview UI can run after the contract is stable.
- File ownership: domain service and tests own invariant behavior; API/UI files own orchestration only.
- Conflict risk: medium for shared domain services; high if migrations or public contracts already exist.

## Data Model
- `feature_state`: state machine value, actor, timestamps, source version.
- `feature_audit_event`: event type, old value, new value, rollback payload, request id.
- `feature_review_note`: reviewer/comment metadata where human approval is required.

## Test Surfaces
- Unit tests for state transitions and conflict policies.
- Integration tests for permission, transaction, and audit persistence.
- Regression tests for rollback, retry, stale payload, or low-confidence blocking.

## Feature Flags
- Ship behind a scoped flag so migrations and UI can be deployed safely before enablement.

## Observability
- Emit counters for preview, apply, blocked apply, rollback, and audit-write failure.

## Decision Traceability
- `FR-001..FR-004` map to preview, apply, audit, and rollback slices.
- ADR-001 maps to append-only audit event shape.
- ADR-002 maps to evidence and promotion gates.
