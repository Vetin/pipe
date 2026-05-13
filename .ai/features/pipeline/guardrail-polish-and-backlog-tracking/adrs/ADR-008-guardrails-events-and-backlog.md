# ADR-008 Guardrails, Events, And Backlog

## Status

Accepted

## Context

Public raw and generated-artifact regressions recurred during pipeline
development. Event sidecars now exist, but `execution.md` can drift toward a
second machine event log if it mirrors every exact event field. Verification
debt also appeared in individual feature cards without a central retrieval
point.

## Decision

- Keep public raw and wrapper checks as a permanent committed guardrail through
  `pipelinebench.py check-public-raw` and GitHub Actions.
- Keep exact event fields in `events.yaml`.
- Keep `execution.md` as concise human narrative and docs-consulted context.
- Reject unexpected top-level fields in `events.yaml`.
- Track durable pipeline verification debt in `.ai/knowledge/pipeline-backlog.md`.

## Consequences

Future agents have a clear artifact boundary: parse `events.yaml`, read
`execution.md`. Raw endpoint and wrapper failures become visible regressions.
Deferred migration and showcase/package work can be found without reading every
feature card.
