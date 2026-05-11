# Technical Design: GitHub sync conflict resolution and audit trail

## Interfaces
- Preview command returns affected entities, conflicts, warnings, and audit preview id.
- Apply command requires preview token/version, actor id, and explicit confirmation.
- Audit query returns immutable event history linked to source entity and request id.

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
