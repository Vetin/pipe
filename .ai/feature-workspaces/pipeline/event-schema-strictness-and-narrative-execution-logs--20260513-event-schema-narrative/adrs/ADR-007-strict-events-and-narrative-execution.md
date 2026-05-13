# ADR-007 Strict Events And Narrative Execution

## Status

Accepted.

## Context

`events.yaml` became the machine-readable event sidecar, but the schema remained
permissive and generated `execution.md` entries still duplicated machine fields.

## Decision

`events.yaml` uses a strict event type enum, rejects unexpected fields, and
requires UTC timestamps. Generated `execution.md` entries are narrative summaries.
Detailed machine fields belong in `events.yaml`.

Public raw verification is exposed through an explicit `pipelinebench` command.
Unit tests use local file-backed raw fixtures, while maintainers may run the
command against GitHub raw URLs.

## Consequences

- Event consumers can trust a bounded event vocabulary.
- Human readers see event summaries without duplicated machine fields.
- Public raw checks are reusable without forcing network access into normal tests.

