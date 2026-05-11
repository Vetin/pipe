# Architecture: Enterprise duplicate merge with preview, conflict rules, and rollback

## Change Delta
- New: Enterprise duplicate merge with preview, conflict rules, and rollback workflow, durable event trail, and verification evidence.
- Modified: nearest domain service, API/UI entry point, and test surfaces identified during context.
- Removed: none assumed before live source inspection.
- Unchanged: unrelated repository workflows and permission boundaries.

## System Context
The feature is modeled as a change set around Twenty domain state, API/UI entry points, persistence, audit events, and verification evidence.

## Component Interactions
- Company duplicate candidate service and normalized matching query
- Merge preview API with conflict policy and related-record impact model
- Transactional merge command with audit event and rollback payload
- CRM UI preview, confirmation, and audit-history surface

## Diagrams
```mermaid
sequenceDiagram
  actor User
  participant UI
  participant API
  participant Domain
  participant Audit
  User->>UI: request Enterprise duplicate merge with preview, conflict rules, and rollback
  UI->>API: preview/submit command
  API->>Domain: validate permissions and invariants
  Domain->>Audit: append decision and rollback data
  Domain-->>API: result with evidence id
  API-->>UI: confirmed outcome or conflict
```

## Security Model
- Permission checks happen before preview, mutation, and rollback.
- Destructive operations require explicit confirmation and audit identity.
- External payloads, if any, require replay protection and stale-event checks.

## Failure Modes
- Irreversible data loss from overwriting company fields without a field provenance record.
- Unsafe automation merging low-confidence duplicates.
- Broken relations if child records are reparented outside a transaction.

## Rollback Strategy
Persist enough before/after state and relation movement metadata to replay or compensate the operation safely.

## Migration Strategy
Deploy persistence and feature flag first, backfill or index audit records where required, then enable the user workflow after verification.

## ADRs
- ADR-001: Use append-only audit events for safety-critical state transitions.
- ADR-002: Block promotion until verification evidence covers every accepted requirement.

## Alternatives Considered
- Reuse existing domain event table directly; acceptable only if it can store rollback payloads and actor provenance.
- Add a feature-specific audit table; safer when existing events cannot preserve before/after state.
- Ship UI-only preview first; rejected for production because apply and rollback invariants must be designed together.

## Completeness Correctness Coherence
- Completeness: every requirement has an architecture component and rollback path.
- Correctness: permissions, audit, and stale/replay controls protect unsafe transitions.
- Coherence: modules align with repository context and defer exact names to source inspection.
