# ADR-006 Events Schema And Execution Boundary

## Status

Accepted.

## Context

The pipeline now writes both `execution.md` and `events.yaml`. Earlier review
found that the two artifacts could drift because both were carrying machine-like
event streams.

## Decision

`events.yaml` is the machine-readable execution event source of truth.
`execution.md` is the human-readable journal and may summarize events, but it
must not be the only parseable source for gate, slice, retry, or promotion events.

The `events.yaml` contract is documented in:

- `.agents/pipeline-core/scripts/schemas/events.schema.json`
- `.agents/pipeline-core/scripts/featurectl_core/validators/events.py`

## Consequences

- Validation can reject malformed event sidecars deterministically.
- Future benchmark and review tooling can parse event state without scraping prose.
- Human readers still get a compact run narrative in `execution.md`.
- Event schema evolution now needs explicit schema and validator updates.

