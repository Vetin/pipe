# ADR-009 Guardrail Status And Execution Summary Polish

## Status

Accepted for this feature.

## Context

Repeated review findings asked for clearer trust in public raw guardrails and a
cleaner boundary between `events.yaml` and `execution.md`. The pipeline already
has raw checks, event sidecars, and a central backlog, but future agents need a
single status document and promoted execution logs should not replay every
machine event field.

## Decision

Add `.ai/knowledge/pipeline-guardrails-status.md` as the shared guardrail
status anchor. Keep exact machine events in `events.yaml`. During promotion,
rewrite canonical `execution.md` event sections into grouped human summaries
derived from the sidecar.

## Consequences

- Reviewers get a stable status document for raw, wrapper, compile, formatting,
  and workflow checks.
- `execution.md` becomes easier to scan after promotion.
- Validators and benchmarks continue to consume exact records from `events.yaml`.
- Historical canonical journals are left intact until a dedicated migration is
  requested.
